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

# ---------------------------------------------------------------------------
# FAR section (same schema and rules as REG; the source folder is tools/src/FAR/far_area<N>*_mcq.json)
# Blueprint weights = midpoint of the 2026 ranges (I 30-40, II 30-40, III 25-35 -> 35/35/30, see FAR_SPEC.md).
# ---------------------------------------------------------------------------
FAR_DEFAULT_SRC = os.path.join(HERE, "src", "FAR")
FAR_AREAS = ["I", "II", "III"]
FAR_SUBJECTS = {
    "I":   ("far_area1_financial_reporting", "Area I · Financial Reporting", "--fam-geo"),
    "II":  ("far_area2_balance_sheet", "Area II · Select Balance Sheet Accounts", "--fam-soc"),
    "III": ("far_area3_transactions", "Area III · Select Transactions", "--fam-eth"),
}
FAR_AREA_TITLE = {"I": "Conceptual Framework, Standard-Setting, and Financial Reporting",
                  "II": "Select Financial Statement Accounts", "III": "Select Transactions"}
FAR_WEIGHT = {"I": 35, "II": 35, "III": 30}
# ---------------------------------------------------------------------------
# TCP section (elective discipline; source folder tools/src/TCP/tcp_*_mcq.json, Areas I-IV; items carry group_name; file tcp_b holds
# extra Analysis items of any Area, so TCP items are gathered from every file and split by their own "area" field).
# Blueprint weights = midpoint of the 2026 ranges (I 30-40, II 30-40, III 10-20, IV 10-20 -> 35/35/15/15, see TCP_SPEC.md).
# ---------------------------------------------------------------------------
TCP_DEFAULT_SRC = os.path.join(HERE, "src", "TCP")
TCP_AREAS = ["I", "II", "III", "IV"]
TCP_SUBJECTS = {
    "I":   ("tcp_area1_individuals", "Area I · Individuals and Personal Financial Planning", "--fam-geo"),
    "II":  ("tcp_area2_entity_compliance", "Area II · Entity Tax Compliance", "--fam-soc"),
    "III": ("tcp_area3_entity_planning", "Area III · Entity Tax Planning", "--fam-eth"),
    "IV":  ("tcp_area4_property", "Area IV · Property Transactions", "--mint"),
}
TCP_WEIGHT = {"I": 35, "II": 35, "III": 15, "IV": 15}
SECTIONS = {
    "REG": {"areas": AREAS, "subjects": SUBJECTS, "weight": WEIGHT, "src": DEFAULT_SRC, "prefix": "reg", "tool": "build_reg.py"},
    "FAR": {"areas": FAR_AREAS, "subjects": FAR_SUBJECTS, "weight": FAR_WEIGHT, "src": FAR_DEFAULT_SRC, "prefix": "far", "tool": "build_far.py"},
    "TCP": {"areas": TCP_AREAS, "subjects": TCP_SUBJECTS, "weight": TCP_WEIGHT, "src": TCP_DEFAULT_SRC, "prefix": "tcp", "tool": "build_tcp.py"},
}


def find_files(src, area, sec="REG"):
    """All source files for an Area, e.g. area4_mcq.json plus area4b_mcq.json (merged into one subject).
    FAR files are named far_area<N>*_mcq.json."""
    import glob
    n = {"I": "1", "II": "2", "III": "3", "IV": "4", "V": "5"}[area]
    if sec == "TCP":
        return sorted(glob.glob(os.path.join(src, "tcp_*_mcq.json")))
    if sec == "FAR":
        return sorted(glob.glob(os.path.join(src, "far_area%s*_mcq.json" % n)))
    found = sorted(glob.glob(os.path.join(src, "area%s*_mcq.json" % n)))
    if area == "II" and not found:
        found = [p for p in [os.path.join(src, "II_mcq.json")] if os.path.exists(p)]
    return found


def load_area(src, area, sec="REG"):
    files = find_files(src, area, sec)
    if not files:
        return None, []
    meta, items = None, []
    for p in files:
        d = json.load(open(p, encoding="utf-8"))
        if meta is None:
            meta = d.get("meta", {})
        for it in d.get("items", []):
            if sec == "TCP" and it.get("area") != area:
                continue                      # TCP: one folder, items belong to the Area named in the item
            items.append(it)                  # duplicate ids across files are reported by check_reg.py
    return meta, items


def group_names(area, meta, items, sec="REG"):
    """Group letter -> name. Blueprint names are read from meta.blueprint when present (FAR items carry group_name)."""
    names = dict(GROUP_NAMES.get(area, {})) if sec == "REG" else {}
    if sec in ("FAR", "TCP"):
        for i in items:
            if i.get("group_name"):
                names.setdefault(i["group"], i["group_name"])
    bp = (meta or {}).get("blueprint", "") if sec == "REG" else ""
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


# ---------------------------------------------------------------------------
# FAR display rule: a paragraph-level citation is shown only when verify.cite_ok says that paragraph was checked against the
# source text. Everything else is cut back to the topic (ASC 842, GASB 34, ...) at build time; the source files are not changed.
# ---------------------------------------------------------------------------
_UNCONFIRMED = re.compile(r"미열람|(번호|문단)[^;.(),]{0,25}미확인")


def _confirmed(ref, ok):
    """Is this exact paragraph named in cite_ok as checked?"""
    m = re.match(r"Statement (\d+), paragraphs? (\d+)", ref)
    if m:
        return re.search(r"(?<!\d)%s\s*¶\s*%s(?!\d)" % (m.group(1), m.group(2)), ok) is not None
    if ref in ok:
        return True
    base, _, last = ref.rpartition("-")                # "250-10-45-18/19" also confirms 250-10-45-19
    return bool(base) and re.search(re.escape(base) + r"-\d+(/\d+)*/" + re.escape(last) + r"(?!\d)", ok) is not None


def _topic(src, ref):
    """(src, ref) cut back to topic level."""
    if src == "ASC":
        return src, ref.split("-")[0]
    if src == "GASB":
        m = re.match(r"Statement (\d+)", ref)
        if m: return src, m.group(1)
        if ref.startswith("Cod. Sec."): return src, "Cod. Sec. " + re.search(r"\d+", ref).group(0)
    if src == "SFAC":
        return src, ref.split(",")[0]
    if src == "SEC":
        m = re.match(r"(Form [\w-]+)", ref)
        if m: return src, m.group(1)
    return src, ref                                    # ASU, AU-C, Interpretation, SAB, Blueprint notes: already topic level


def far_cite(it):
    """Citation list shown for a FAR item: paragraph numbers only where cite_ok confirms them, topic otherwise."""
    ok = str((it.get("verify") or {}).get("cite_ok") or "")
    checked = ok.startswith("public-checked") and not _UNCONFIRMED.search(ok)
    out, have = [], set()
    for c in it.get("cite") or []:
        src, ref = (c.get("src") or "").strip(), (c.get("ref") or "").strip()
        if ref and not (checked and _confirmed(ref, ok)):
            src, ref = _topic(src, ref)
        key = (src, ref)
        if key not in have:
            have.add(key); out.append({"src": src, "ref": ref})
    conf = {(s, r) for s, r in have if s == "ASC" and re.search(r"-", r)}      # drop a bare topic that a confirmed paragraph already covers
    out = [c for c in out if not (c["src"] == "ASC" and "-" not in c["ref"] and any(k[1].split("-")[0] == c["ref"] for k in conf))]
    return out


def far_cite_is_paragraph(text):
    """True when a displayed citation string carries an ASC paragraph number."""
    return re.search(r"\d{3}-\d{2}-\d{2}", text) is not None


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


# ---------------------------------------------------------------------------
# Builder helpers shared by build_reg.py and build_far.py
# ---------------------------------------------------------------------------
def first_sentence(t):
    t = re.sub(r"^(Correct|Incorrect)\.\s*", "", str(t)).strip()
    m = re.match(r"(.+?[.!?])(\s|$)", t)
    return m.group(1) if m else t


def clean(t):
    return re.sub(r"^(Correct|Incorrect)\.\s*", "", str(t)).strip()


def question(it):
    ex = it.get("exhibit")
    mc = {
        "s": it["stem"],
        "d": ex if isinstance(ex, str) else "",
        "o": list(it["options"]),
        "a": "ABCD".index(it["answer"]) + 1,
        "cite": cite_text(it["cite"]),
        "rat": first_sentence(it["why"][it["answer"]]),
        "ex": [clean(it["why"][k]) for k in "ABCD"],
        "wt": tag_wrong_options(it),
        "tags": {"area": it["area"], "group": it["group"], "skill": it["skill"], "diff": it["difficulty"]},
        "asof": it.get("law_asof") or "",
    }
    if it.get("rule_line"):
        mc["rl"] = str(it["rule_line"]).strip()
    if isinstance(ex, list) and ex:
        mc["tb"] = ex
    if it.get("testable_from"):
        mc["from"] = it["testable_from"]
    if it.get("calc"):
        mc["calc"] = 1
    if it.get("steps"):
        mc["steps"] = list(it["steps"])
    return {"i": it["id"], "t": it["stem"], "mc": mc}


def dump_js(path, T, Q, tool="build_reg.py"):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("/* Auto-generated by tools/%s — pipeline artifact. Do not hand-edit */\n" % tool)
        f.write("window.TREE=" + json.dumps(T, ensure_ascii=False, separators=(",", ":")) + ";\n")
        f.write("window.QBANK=" + json.dumps(Q, ensure_ascii=False, separators=(",", ":")) + ";\n")
        f.write("window.PAIRS=[];\n")


def read_ready():
    rp = os.path.join(ROOT, "data", "ready.js")
    if os.path.exists(rp):
        t = open(rp, encoding="utf-8").read()
        try:
            return json.loads(t[t.index("=") + 1:].rstrip().rstrip(";"))
        except Exception:
            pass
    return {}


def write_ready(R):
    """Fixed key order (other subjects, then reg_*, far_*, tcp_*), so a rebuild of one section never reorders the others."""
    def rank(k):
        return 1 if k.startswith("reg_") else 2 if k.startswith("far_") else 3 if k.startswith("tcp_") else 0
    R = {k: R[k] for k in sorted(R, key=rank)}          # stable sort keeps the order inside a group
    with open(os.path.join(ROOT, "data", "ready.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write("/* Auto-generated — pipeline artifact */\nwindow.READY=" + json.dumps(R, ensure_ascii=False) + ";\n")


def write_catalog(sec):
    """Rewrite the subject list and the exam's subject list between the <sec> markers of js/catalog.js."""
    cfg = SECTIONS[sec]
    cp = os.path.join(ROOT, "js", "catalog.js")
    cat = open(cp, encoding="utf-8").read()
    subj = "".join('    %s: { name: %s, area: "%s", weight: %d },\n' % (cfg["subjects"][ar][0], json.dumps(cfg["subjects"][ar][1], ensure_ascii=False), ar, cfg["weight"][ar]) for ar in cfg["areas"])
    subs = ", ".join('"%s"' % cfg["subjects"][ar][0] for ar in cfg["areas"])
    cat = re.sub(r"(/\* BEGIN %s SUBJECTS[^\n]*\*/\n).*?(    /\* END %s SUBJECTS \*/)" % (sec, sec), lambda m: m.group(1) + subj + m.group(2), cat, flags=re.S)
    cat = re.sub(r"(/\* BEGIN %s SUBS \*/).*?(/\* END %s SUBS \*/)" % (sec, sec), lambda m: m.group(1) + "[" + subs + "]" + m.group(2), cat, flags=re.S)
    open(cp, "w", encoding="utf-8", newline="\n").write(cat)


def write_sw(tool="build_reg.py"):
    """Service worker file list + version (content hash of every shipped app file). Returns a report line or None."""
    swp = os.path.join(ROOT, "sw.js")
    if not os.path.exists(swp):
        return None
    files = pwa_files()
    ver = pwa_version(files)
    sw = open(swp, encoding="utf-8").read()
    sw = re.sub(r"(/\* BEGIN PRECACHE[^\n]*\*/\n).*?(/\* END PRECACHE \*/)",
                lambda m: m.group(1) + 'var VERSION = "%s";\nvar FILES = %s;\n' % (ver, json.dumps(files, indent=1)) + m.group(2), sw, flags=re.S)
    open(swp, "w", encoding="utf-8", newline="\n").write(sw)
    return "sw.js version %s, %d files precached" % (ver, len(files))
