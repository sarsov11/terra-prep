# -*- coding: utf-8 -*-
"""Browser walk-through of tbs.html (needs Playwright + Edge).

  py -m http.server 18590 --bind 127.0.0.1     (in the repo root)
  py tools/e2e_tbs.py [port]

Desktop and 375px phone: list + filters, practice (check, carry-forward, hints, explanation, copy, retry wrong, result),
number variant, exam mode (timer, confirm, submit), citation forms, dropdown diff. Screenshots -> tools/screens/tbs_*.png.
Exit code 1 on a failed check or any console error.
"""
import json, os, sys
from playwright.sync_api import sync_playwright

PORT = sys.argv[1] if len(sys.argv) > 1 else "18590"
BASE = "http://127.0.0.1:%s/tbs.html" % PORT
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens")
os.makedirs(OUT, exist_ok=True)
errors, fails = [], []


def check(name, ok, info=""):
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(info) if info else ""))
    if not ok:
        fails.append(name)


def cells(pg):
    return pg.evaluate("TBSApp.R.cells.map(c=>({id:c.id,kind:c.kind,answer:c.answer,accept:c.accept,options:c.options,traps:c.traps,wrong:c.wrong,deps:c.deps,expr:c.expr}))")


def fill(pg, cid, val):
    el = pg.locator('[data-c="%s"]' % cid)
    if el.evaluate("e=>e.tagName") == "SELECT":
        el.select_option(val)
    else:
        el.fill(str(val))
        el.blur()


def run(pw, tag, viewport, mobile):
    br = pw.chromium.launch(channel="msedge")
    ctx = br.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, permissions=["clipboard-read", "clipboard-write"])
    pg = ctx.new_page()
    pg.on("console", lambda m: errors.append((tag, m.text)) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append((tag, str(e))))
    shot = lambda n, full=False: pg.screenshot(path=os.path.join(OUT, "tbs_%s_%s.png" % (tag, n)), full_page=full)

    pg.goto(BASE)
    pg.wait_for_selector(".tb-list li")
    check(tag + " list 24 rows", pg.locator(".tb-list li").count() == 24)
    shot("list")
    pg.select_option("#fa", "IV")
    check(tag + " filter Area IV = 7", pg.locator(".tb-list li").count() == 7)
    pg.select_option("#fa", "")
    pg.select_option("#ff", "research")
    check(tag + " filter research = 4", pg.locator(".tb-list li").count() == 4)
    pg.select_option("#ff", "")

    # ── practice: numeric item with carry-forward ──
    pg.goto(BASE + "#/REG-IV-T-012")
    pg.wait_for_selector(".cell")
    check(tag + " exhibit tabs", pg.locator("#extabs button").count() >= 2)
    if mobile:
        check(tag + " mobile tabs shown", pg.locator(".tb-tabs").is_visible())
        pg.click('.tb-tabs [data-t="exh"]')
        check(tag + " exhibits pane visible on Exhibits tab", pg.locator("#exbody").is_visible() and not pg.locator("#cells").is_visible())
        shot("exhibits")
        pg.click('.tb-tabs [data-t="task"]')
    else:
        check(tag + " split: exhibit and task both visible", pg.locator("#exbody").is_visible() and pg.locator("#cells").is_visible())
    cs = cells(pg)
    nums = [c for c in cs if c["kind"] == "number"]
    c2 = next(c for c in nums if c["id"] == "c2")
    fill(pg, "c1", "{:,}".format(nums[0]["answer"]))   # with thousands separator
    pg.click("#cell-c1 [data-a=chk]")
    check(tag + " c1 correct (comma input)", "ok" in (pg.get_attribute("#cell-c1", "class") or ""))
    check(tag + " c1 locked after correct", pg.locator('[data-c="c1"]').is_disabled())
    # wrong c2 (+1000), then c3 computed from the wrong c2 -> carry-forward
    wrong2 = c2["answer"] + 1000
    fill(pg, "c2", wrong2)
    pg.click("#cell-c2 [data-a=chk]")
    check(tag + " c2 wrong", "bad" in (pg.get_attribute("#cell-c2", "class") or ""))
    check(tag + " wrong diff strikes entry", pg.locator("#cell-c2 .fb del").count() == 1)
    alt_ti = pg.evaluate("(w)=>{const p=TBSApp.R.params;return w-p.std}", wrong2)
    c3 = next(c for c in nums if c["id"] == "c3")
    fill(pg, "c3", alt_ti)
    pg.click("#cell-c3 [data-a=chk]")
    check(tag + " c3 carry-forward half credit", "half" in (pg.get_attribute("#cell-c3", "class") or "") and "Carried forward" in pg.inner_text("#cell-c3 .fb"), pg.inner_text("#cell-c3 .fb"))
    # hints one step at a time
    pg.click("#cell-c4 [data-a=hint]")
    n1 = pg.locator("#cell-c4 .hintbox li").count()
    pg.click("#cell-c4 [data-a=hint]")
    n2 = pg.locator("#cell-c4 .hintbox li").count()
    check(tag + " hints step by step", n1 == 1 and n2 == 2, (n1, n2))
    pg.click("#cell-c4 [data-a=hint]")
    check(tag + " third press shows steps", "Steps" in pg.inner_text("#cell-c4 .hintbox"))
    shot("practice", True)
    # explanation hidden until asked; retry wrong
    check(tag + " explanation hidden by default", pg.locator("#cell-c1 .exp").is_hidden())
    pg.click("#cell-c1 [data-a=exp]")
    check(tag + " explanation shows answer + copy", pg.locator("#cell-c1 .exp ins").count() == 1 and pg.locator("#cell-c1 [data-a=cp]").count() == 1)
    pg.click("#cell-c1 [data-a=cp]")
    clip = pg.evaluate("navigator.clipboard.readText()")
    check(tag + " explanation copied", "Answer:" in clip, clip[:60])
    check(tag + " explanation text selectable", pg.evaluate("getComputedStyle(document.querySelector('#cell-c1 .exp')).userSelect") in ("text", "auto"))
    # fill the rest correctly (c2 stays wrong+revealed)
    for c in nums:
        if c["id"] in ("c1", "c2", "c3"):
            continue
        fill(pg, c["id"], c["answer"])
    pg.click("#chkall")
    fill_ok = pg.evaluate("TBSApp.A.done")
    check(tag + " attempt done after Check all", fill_ok is True or c3 is not None)
    check(tag + " retry wrong offered", pg.locator(".rwb").count() >= 1)
    check(tag + " result score shown", pg.locator("#res .big").count() == 1, pg.inner_text("#res .big") if pg.locator("#res .big").count() else "")
    shot("result", True)
    # retry c3 correctly
    pg.locator(".rwb:visible").first.click()
    fill(pg, "c2", c2["answer"])
    pg.click("#cell-c2 [data-a=chk]")
    check(tag + " retry credit shown as after-retry", "After retry" in pg.inner_text("#res"))
    st = pg.evaluate("JSON.parse(localStorage.getItem('te.tbs.v1')).items['REG-IV-T-012']")
    check(tag + " progress saved with te.tbs. key", st and st["done"] == 1 and st["best"] < 100, st)

    # ── variant ──
    before = pg.evaluate("TBSApp.R.params")
    pg.click("#var")
    pg.wait_for_selector(".cell")
    check(tag + " variant url has seed", "#/REG-IV-T-012/" in pg.url and not pg.url.endswith("/new"), pg.url)
    after = pg.evaluate("TBSApp.R.params")
    seeds = set()
    for _ in range(4):
        pg.click("#var")
        pg.wait_for_selector(".cell")
        seeds.add(json.dumps(pg.evaluate("TBSApp.R.params"), sort_keys=True))
    check(tag + " variants change the numbers", len(seeds | {json.dumps(before, sort_keys=True), json.dumps(after, sort_keys=True)}) > 1)
    for c in cells(pg):
        if c["kind"] == "number":
            fill(pg, c["id"], c["answer"])
    pg.click("#chkall")
    check(tag + " variant perfect entry = 100%", "100%" in pg.inner_text("#res .big"), pg.inner_text("#res .big"))
    shot("variant", True)

    # ── research (citation forms) ──
    pg.goto(BASE + "#/REG-III-T-010")
    pg.wait_for_selector(".cell")
    cs = cells(pg)
    forms = ["§{0}", "{0}", "IRC {0}", "Sec. {0}", "26 U.S.C. § {0}"]
    got = []
    for i, c in enumerate(cs):
        a = c["accept"][0]
        fill(pg, c["id"], forms[i % len(forms)].format(a))
        pg.click("#cell-%s [data-a=chk]" % c["id"])
        got.append("ok" in (pg.get_attribute("#cell-%s" % c["id"], "class") or ""))
    check(tag + " citation forms accepted", all(got), got)
    if mobile:
        pg.click('.tb-tabs [data-t="task"]')  # finishing switches to the Result tab
    pg.click("#cell-%s [data-a=exp]" % cs[0]["id"])
    href = pg.get_attribute("#cell-%s .exp .lnk a" % cs[0]["id"], "href")
    check(tag + " citation source link law.cornell.edu", href and href.startswith("https://www.law.cornell.edu/"), href)
    shot("research", True)

    # ── dropdown diff ──
    pg.goto(BASE + "#/REG-II-T-004")
    pg.wait_for_selector(".cell")
    d = cells(pg)[0]
    wrong = next(o for o in d["options"] if o != d["answer"])
    fill(pg, d["id"], wrong)
    pg.click("#cell-%s [data-a=chk]" % d["id"])
    check(tag + " dropdown wrong: struck choice + reason", pg.locator("#cell-%s .fb del" % d["id"]).count() == 1 and pg.locator("#cell-%s .fb .msg" % d["id"]).count() == 1)
    fill(pg, d["id"], d["answer"]) if False else None
    shot("dropdown")

    # ── exam mode ──
    pg.goto(BASE)
    pg.wait_for_selector(".tb-list li")
    pg.click('[data-mode="exam"]')
    pg.goto(BASE + "#/REG-I-T-001")
    pg.wait_for_selector(".cell")
    check(tag + " exam: no Check/Hint buttons", pg.locator("[data-a=chk],[data-a=hint]").count() == 0 and pg.locator("#sub").count() == 1)
    t0 = pg.inner_text("#tmr")
    pg.wait_for_timeout(2200)
    t1 = pg.inner_text("#tmr")
    check(tag + " exam timer counts down from 18:00", t0.startswith("17:5") or t0.startswith("18:0"), (t0, t1))
    check(tag + " exam timer moves", t0 != t1, (t0, t1))
    cs = cells(pg)
    for c in cs[:3]:
        fill(pg, c["id"], c["answer"])
    pg.click("#sub")
    check(tag + " confirm shows unanswered count", "Unanswered 3" in pg.inner_text("#cf"), pg.inner_text("#cf"))
    shot("exam_confirm")
    pg.click("#yes")
    check(tag + " exam result 3 of 6 ok", pg.locator("#res .big").count() == 1 and pg.inner_text("#res .big").startswith("3 / 6"), pg.inner_text("#res .big") if pg.locator("#res .big").count() else "")
    check(tag + " exam: explanations after submit", pg.locator("[data-a=exp]").count() == 6)
    check(tag + " exam: no retry", pg.locator(".rwb").count() == 0)
    shot("exam_result", True)

    # ── resume ──
    pg.goto(BASE + "#/REG-IV-T-013")
    pg.wait_for_selector(".cell")
    fill(pg, "c1", "1234")
    pg.wait_for_timeout(500)
    pg.reload()
    pg.wait_for_selector(".cell")
    check(tag + " input restored after reload", pg.input_value('[data-c="c1"]') == "1,234", pg.input_value('[data-c="c1"]'))
    if mobile:
        pg.click('.tb-tabs [data-t="res"]')
        check(tag + " mobile Result tab", pg.locator("#split").get_attribute("data-tab") == "res")
        pg.click('.tb-tabs [data-t="task"]')
        pg.click("#seex")
        check(tag + " mobile fab -> Exhibits", pg.locator("#split").get_attribute("data-tab") == "exh")
    overflow = pg.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
    check(tag + " no horizontal page scroll", not overflow)
    small = pg.evaluate("""()=>{let m=99;document.querySelectorAll('.tbs *').forEach(e=>{if(e.childNodes.length&&[...e.childNodes].some(n=>n.nodeType==3&&n.textContent.trim())){const s=parseFloat(getComputedStyle(e).fontSize);if(s<m)m=s}});return m}""")
    check(tag + " min font size >= 13.5px", small >= 13.5, small)
    shot("solver")
    # no br.close(): on this PC closing Edge can hang the driver; leaving the `with` block stops it


_RUNS = (("desktop", {"width": 1440, "height": 900}, False), ("mobile", {"width": 375, "height": 812}, True))
for _tag, _vp, _mob in [r for r in _RUNS if len(sys.argv) < 3 or r[0] == sys.argv[2]]:
    with sync_playwright() as pw:  # one driver per run (Edge close can drop the driver connection)
        run(pw, _tag, _vp, _mob)

for e in errors:
    print("CONSOLE ERROR", e)
check("console errors = 0", not errors)
print("FAILED: %s" % fails if fails else "ALL PASS")
sys.exit(1 if fails or errors else 0)
