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


# ---------------------------------------------------------------------------
# Wrong-choice cause tags (rule based, no model call).
#   concept  = a different rule applied / rule misunderstood
#   calc     = arithmetic or procedure slip in a computed answer
#   trap     = a tempting phrase, absolute word or wrong "because" reason
#   limit    = a dollar limit, percentage, day or year count, or threshold mixed up
#   unclassified = no rule fired with confidence
# A source item may carry its own tags and they win over the rules:
#   "wrong_tags": {"A": "trap", "C": "calc"}   (also accepted as "distractor_tags", or a 4-list)
# ---------------------------------------------------------------------------
WRONG_TAGS = ["concept", "calc", "trap", "limit", "unclassified"]
_LIMIT = re.compile(r"\b(limit|limits|limited|threshold|cap|capped|ceiling|phase-?out|maximum|minimum|band|bracket|increment|"
                    r"reach-back|recognition period|look-?back|statute of limitations|exceeds?)\b"
                    r"|\b(\d+|two|three|four|five|six|ten|twelve|thirty|sixty|ninety)[- ](percent|days?|months?|years?|year)\b|\b\d+(\.\d+)?%\s+(rule|test|threshold|limit)", re.I)
_OP = re.compile(r"^(Uses|Adds|Subtracts|Ignores|Doubles|Reduces|Rounds|Applies|Omits|Deducts|Includes|Forgets|Counts|Taxes|Multiplies|"
                 r"Divides|Excludes|Disallows|Computes|Takes|Treats|Reverses|Double|Fails|Stops|Starts|Mixes|Only|This is only|This is the|This is)\b")
_TRAP = re.compile(r"\b(even though|even if|regardless|no matter|merely|does not depend|not on who|rather than|is not the test|looks|appears|"
                   r"tempting|superficial|the results are reversed|only because|not because)\b", re.I)
_TRAP_OPT = re.compile(r"\b(only if|only when|solely|automatically|regardless|always|never|both)\b", re.I)
_CONCEPT = re.compile(r"\b(is|are) (excluded|not|treated|taxable|deductible|allowed|required|stepped|a|an|the|considered)\b|does not|do not|cannot|may not|"
                      r"not part|instead|applies|apply|governed|reverses|only (for|to)|no state law|is not required|is limited to|must|requires?", re.I)


def _numeric_option(t):
    return bool(re.fullmatch(r"-?\$?[\d,]+(\.\d+)?%?", t.strip())) or bool(re.match(r"^\$[\d,]+", t.strip()))


def _src_tags(it):
    t = it.get("wrong_tags") or it.get("distractor_tags")
    if isinstance(t, dict):
        return {k: v for k, v in t.items() if v in WRONG_TAGS}
    if isinstance(t, list) and len(t) == 4:
        return {k: v for k, v in zip("ABCD", t) if v in WRONG_TAGS}
    return {}


def tag_wrong_options(it):
    """List of 4 tags aligned with options; the correct option gets ''."""
    src = _src_tags(it)
    out = []
    for k, opt in zip("ABCD", it["options"]):
        if k == it["answer"]:
            out.append(""); continue
        if k in src:
            out.append(src[k]); continue
        why = re.sub(r"^(Correct|Incorrect)\.\s*", "", str(it["why"][k])).strip()
        limit = bool(_LIMIT.search(why))
        if it.get("calc") and _numeric_option(opt):
            out.append("limit" if limit and not _OP.match(why) else "calc")
        elif _OP.match(why) and _numeric_option(opt):
            out.append("calc")
        elif limit:
            out.append("limit")
        elif _TRAP.search(why) or _TRAP_OPT.search(opt):
            out.append("trap")
        elif _CONCEPT.search(why):
            out.append("concept")
        else:
            out.append("unclassified")
    return out


# ---------------------------------------------------------------------------
# Offline (PWA): the file list and a content hash that versions the service worker cache.
# ---------------------------------------------------------------------------
def pwa_files():
    """Shipped app files. PWA_EXCLUDE="tbs.html,js/tbs.js" (comma list) leaves out files that are not committed yet."""
    skip = {x.strip() for x in os.environ.get("PWA_EXCLUDE", "").split(",") if x.strip()}
    out = []
    for d, ext in (("", (".html",)), ("css", (".css",)), ("js", (".js",)), ("data", (".js",)), ("icons", (".svg", ".png"))):
        base = os.path.join(ROOT, d) if d else ROOT
        if not os.path.isdir(base):
            continue
        for n in sorted(os.listdir(base)):
            if n.endswith(ext) and not (d == "" and n in ("sw.js",)):
                out.append((d + "/" + n) if d else n)
    out.append("manifest.webmanifest")
    return sorted(set(out) - skip)


def pwa_version(files):
    import hashlib
    h = hashlib.md5()
    for f in files:
        h.update(f.encode()); h.update(open(os.path.join(ROOT, f), "rb").read())
    return h.hexdigest()[:10]
