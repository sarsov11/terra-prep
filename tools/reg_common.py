# -*- coding: utf-8 -*-
"""Shared helpers for tools/build_reg.py and tools/check_reg.py.

Source files (SPEC section 4 schema, one per Blueprint Area) live in tools/src/REG/ by default:
  area1_mcq.json  area2_mcq.json  area3_mcq.json  area4_mcq.json  area5_mcq.json
Use --src DIR to read another folder (the cloud-work source folder has the same file names;
Area II is II_mcq.json there and is also accepted).
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_SRC = os.path.join(HERE, "src", "REG")

ACCEPT = {"verified"}                     # statuses shipped by default
AREAS = ["I", "II", "III", "IV", "V"]
FILES = {"I": ["area1_mcq.json"], "II": ["area2_mcq.json", "II_mcq.json"], "III": ["area3_mcq.json"],
         "IV": ["area4_mcq.json"], "V": ["area5_mcq.json"]}

# subject key (= data/<key>.js), display name, orbit colour token (skilltree)
SUBJECTS = {
    "I":   ("reg_area1_ethics_procedures", "Area I · Ethics and Federal Tax Procedures", "--fam-geo"),
    "II":  ("reg_area2_business_law", "Area II · Business Law", "--fam-soc"),
    "III": ("reg_area3_property", "Area III · Property Transactions", "--fam-eth"),
    "IV":  ("reg_area4_individuals", "Area IV · Individual Taxation", "--mint"),
    "V":   ("reg_area5_entities", "Area V · Entity Taxation", "--fam-geo"),
}
AREA_TITLE = {
    "I": "Ethics, Professional Responsibilities and Federal Tax Procedures",
    "II": "Business Law",
    "III": "Federal Taxation of Property Transactions",
    "IV": "Federal Taxation of Individuals",
    "V": "Federal Taxation of Entities",
}
# Blueprint weights (midpoint of the 2026 ranges) used by the mock exam and placement check
WEIGHT = {"I": 15, "II": 20, "III": 10, "IV": 27, "V": 28}
GROUP_NAMES = {
    "II": {"A": "Agency", "B": "Contracts", "C": "Debtor-creditor relationships",
           "D": "Federal laws affecting business", "E": "Business structure"},
}
SKILLS = ["Remembering & Understanding", "Application", "Analysis"]


def find_files(src, area):
    """All source files for an Area, e.g. area4_mcq.json plus area4b_mcq.json (merged into one subject)."""
    import glob
    n = {"I": "1", "II": "2", "III": "3", "IV": "4", "V": "5"}[area]
    found = sorted(glob.glob(os.path.join(src, "area%s*_mcq.json" % n)))
    if area == "II" and not found:
        found = [p for p in [os.path.join(src, "II_mcq.json")] if os.path.exists(p)]
    return found


def load_area(src, area):
    files = find_files(src, area)
    if not files:
        return None, []
    meta, items = None, []
    for p in files:
        d = json.load(open(p, encoding="utf-8"))
        if meta is None:
            meta = d.get("meta", {})
        for it in d.get("items", []):
            items.append(it)                  # duplicate ids across files are reported by check_reg.py
    return meta, items


def group_names(area, meta, items):
    """Group letter -> name. Blueprint names are read from meta.blueprint when present."""
    names = dict(GROUP_NAMES.get(area, {}))
    bp = (meta or {}).get("blueprint", "")
    for m in re.finditer(r"\b([A-F]) ([A-Z][^,;()]+)", bp):
        names.setdefault(m.group(1), m.group(2).strip())
    for g in sorted({i["group"] for i in items}):
        if g not in names:
            tops = [i["topic"] for i in items if i["group"] == g]
            names[g] = tops[0] if len(set(tops)) == 1 else "Group " + g
    return names


def cite_text(cite):
    out = []
    for c in cite or []:
        src, ref = (c.get("src") or "").strip(), (c.get("ref") or "").strip()
        if not ref:
            out.append(src)
        elif ref.lower().startswith(src.lower()) or re.match(r"(Pub|Reg|IRC|Rev|Form)\b", ref):
            out.append(ref)
        elif src == "Pub":
            out.append("Pub " + ref)
        else:
            out.append((src + " " + ref).strip())
    return "; ".join(out)


def accepted(items, include_draft=False):
    ok = set(ACCEPT) | ({"draft"} if include_draft else set())
    return [i for i in items if i.get("status") in ok]
