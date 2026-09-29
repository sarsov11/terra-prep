"""Copy the latest REG item sources from cloud-work into tools/src/REG.

    py tools/sync_src.py            (run `git fetch` in cloud-work first)

Sources
  claude/terra-prep-becker : jobs/terra-prep-becker/원천/REG/area{1,1b,3,4,4b,5,5b}_mcq.json, cards_reg.json (concept cards)
  claude/terra-us-regbl    : jobs/terra-us/out_reg_bl/AreaII/기출/REG/II_mcq.json  -> area2_mcq.json
Missing files are skipped. Idempotent.
"""
import os, subprocess, sys

CW = os.environ.get("CLOUD_WORK", r"C:\Users\서문여고\테라러닝_2컴\작업\cloud-work")
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "REG")
BECKER = "origin/claude/terra-prep-becker"
REGBL = "origin/claude/terra-us-regbl"
FILES = [(BECKER, f"jobs/terra-prep-becker/원천/REG/{n}_mcq.json", f"{n}_mcq.json")
         for n in ("area1", "area1b", "area3", "area4", "area4b", "area5", "area5b")]
FILES.append((BECKER, "jobs/terra-prep-becker/원천/REG/cards_reg.json", "cards_reg.json"))
FILES.append((REGBL, "jobs/terra-us/out_reg_bl/AreaII/기출/REG/II_mcq.json", "area2_mcq.json"))


def show(ref, path):
    r = subprocess.run(["git", "-C", CW, "-c", "core.quotepath=false", "show", f"{ref}:{path}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def merge_area2(data):
    """Merge rule_line/wrong_tags from area2_enrich.json (Area II is owned by another window)."""
    import json
    enrich = show(BECKER, "jobs/terra-prep-becker/원천/REG/area2_enrich.json")
    if enrich is None:
        return data
    add = json.loads(enrich.decode("utf-8"))
    doc = json.loads(data.decode("utf-8"))
    items = doc if isinstance(doc, list) else next(v for v in doc.values() if isinstance(v, list))
    for it in items:
        e = add.get(it.get("id"))
        if e:
            it.setdefault("rule_line", e.get("rule_line"))
            it.setdefault("wrong_tags", e.get("wrong_tags"))
    return (json.dumps(doc, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


os.makedirs(DST, exist_ok=True)
for ref, path, name in FILES:
    data = show(ref, path)
    if data is not None and name == "area2_mcq.json":
        data = merge_area2(data)
    if data is None:
        print(f"skip  {name} (not on {ref})")
        continue
    out = os.path.join(DST, name)
    old = open(out, "rb").read() if os.path.exists(out) else None
    if old != data:
        open(out, "wb").write(data)
        print(f"sync  {name} ({len(data):,} bytes)")
    else:
        print(f"same  {name}")
sys.exit(0)
