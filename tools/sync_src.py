"""Copy the latest REG item sources from cloud-work into tools/src/REG.

    py tools/sync_src.py            (run `git fetch` in cloud-work first)

Sources
  claude/terra-prep-becker : jobs/terra-prep-becker/원천/REG/area{1,1b,3,4,4b,5,5b}_mcq.json
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
FILES.append((REGBL, "jobs/terra-us/out_reg_bl/AreaII/기출/REG/II_mcq.json", "area2_mcq.json"))


def show(ref, path):
    r = subprocess.run(["git", "-C", CW, "-c", "core.quotepath=false", "show", f"{ref}:{path}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


os.makedirs(DST, exist_ok=True)
for ref, path, name in FILES:
    data = show(ref, path)
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
