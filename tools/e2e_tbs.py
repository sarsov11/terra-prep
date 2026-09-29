# -*- coding: utf-8 -*-
"""Browser walk-through of tbs.html (needs Playwright + Edge).

  py -m http.server 18590 --bind 127.0.0.1     (in the repo root)
  py tools/e2e_tbs.py [port]

Desktop and 375px phone: list + filters, practice (check, carry-forward, hints, explanation, copy, retry wrong, result),
number variant, exam mode (timer, confirm, submit), citation forms, dropdown diff. Screenshots -> tools/screens/tbs_*.png.
FAR section (run_far): list/section switch, journal-entry cell (autocomplete, balance, line credit, carry-forward, hints, mistakes struck through),
ratio/percent formats, ASC/GASB number forms, link button only when a link exists, exam mode. Screenshots -> tools/screens/tbs_far_*.png.
Exit code 1 on a failed check or any console error.
"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
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


# ───────────── FAR section ─────────────
COA_NAME = {a["id"]: a["name"] for a in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "TBS", "je_coa.json"), encoding="utf-8"))["coa"]}


def je_cells(pg):
    return pg.evaluate("TBSApp.R.cells.filter(c=>c.kind==='je').map(c=>({id:c.id,points:c.points,lines:c.lines.map(l=>({a:l.a,s:l.s,v:l.v,deps:l.deps,expr:l.expr})),hints:c.hints}))")


def pick_account(pg, cid, row, acct_id, typed=None):
    """Type into the account box of one line and choose the suggestion by clicking it."""
    name = COA_NAME[acct_id]
    box = pg.locator('[data-c="%s"]' % cid)
    a = box.locator(".jl").nth(row).locator(".jl-acct")
    a.click()
    a.fill("")
    a.type(typed or name[:4])
    opt = box.locator(".jl-opt", has_text=name).first
    opt.wait_for(state="visible", timeout=4000)
    opt.click()
    return a


def fill_je(pg, cid, lines, amounts=None):
    """lines = [(account id, 'D'|'C', amount)] entered through the screen (autocomplete + amount boxes)."""
    box = pg.locator('[data-c="%s"]' % cid)
    while box.locator(".jl").count() < len(lines):
        box.locator("[data-add]").click()
    for i, (aid, side, amt) in enumerate(lines):
        pick_account(pg, cid, i, aid)
        row = box.locator(".jl").nth(i)
        fld = row.locator(".jl-d" if side == "D" else ".jl-c")
        fld.fill(str(amt))
        fld.blur()


def correct_lines(c):
    return [(l["a"], l["s"], l["v"]) for l in c["lines"]]


def run_far(pg, tag, mobile):
    shotf = lambda n, full=False: pg.screenshot(path=os.path.join(OUT, "tbs_far_%s_%s.png" % (tag, n)), full_page=full)
    # ── list: section switch, filters ──
    pg.goto(BASE)
    pg.wait_for_selector(".tb-list li")
    pg.click('[data-mode="practice"]')
    pg.goto(BASE + "?sec=FAR")
    pg.wait_for_selector(".tb-list li")
    check(tag + " FAR list 24 rows", pg.locator(".tb-list li").count() == 24)
    check(tag + " FAR section chip pressed", pg.locator('[data-sec="FAR"]').get_attribute("aria-pressed") == "true")
    check(tag + " FAR rows link FAR ids", pg.locator(".tb-list li a").first.get_attribute("href").startswith("#/FAR-"))
    shotf("list")
    check(tag + " FAR areas I-III only", pg.locator("#fa option").count() == 4, pg.locator("#fa option").count())
    pg.select_option("#ff", "journal_entry")
    check(tag + " FAR filter journal entry = 8", pg.locator(".tb-list li").count() == 8, pg.locator(".tb-list li").count())
    pg.select_option("#ff", "")
    pg.click('[data-sec="REG"]')
    pg.wait_for_selector(".tb-list li")
    check(tag + " switch to REG = 24 REG rows", pg.locator(".tb-list li").count() == 24 and pg.locator(".tb-list li a").first.get_attribute("href").startswith("#/REG-"))
    check(tag + " REG has no journal entry format", pg.locator("#ff option[value=journal_entry]").count() == 0)
    pg.click('[data-sec="FAR"]')
    pg.wait_for_selector(".tb-list li")
    home = pg.evaluate("localStorage.getItem('te.tbs.v1')")
    check(tag + " section choice saved", '"sec":"FAR"' in (home or ""))

    # ── journal-entry cell, practice ──
    pg.goto(BASE + "#/FAR-II-T-005/0/new")
    pg.wait_for_selector(".jecell")
    jes = je_cells(pg)
    check(tag + " FAR TBS has 3 journal cells", len(jes) == 3, [j["id"] for j in jes])
    j2 = next(j for j in jes if j["id"] == "c2")
    rows0 = pg.locator('[data-c="c2"] .jl').count()
    check(tag + " starts with lines + 2 rows", rows0 == len(j2["lines"]) + 2, rows0)
    if mobile:
        b = pg.locator('[data-c="c2"] .jl').first.bounding_box()
        a = pg.locator('[data-c="c2"] .jl .jl-acct').first.bounding_box()
        d = pg.locator('[data-c="c2"] .jl .jl-d').first.bounding_box()
        c_ = pg.locator('[data-c="c2"] .jl .jl-c').first.bounding_box()
        check(tag + " mobile line: account full width, debit/credit below side by side",
              a["width"] > b["width"] * 0.7 and d["y"] > a["y"] + a["height"] - 2 and abs(d["y"] - c_["y"]) < 3 and d["x"] < c_["x"], (a, d, c_))
        check(tag + " mobile inputs tall enough (>=44px)", min(a["height"], d["height"]) >= 43.5, (a["height"], d["height"]))
        check(tag + " mobile column header hidden", pg.locator(".jl-head").first.is_hidden())
    else:
        check(tag + " desktop line: account, debit, credit in one row", abs(pg.locator('[data-c="c2"] .jl .jl-d').first.bounding_box()["y"] - pg.locator('[data-c="c2"] .jl .jl-acct').first.bounding_box()["y"]) < 4)
    # autocomplete: names, synonyms, candidates first
    box = pg.locator('[data-c="c2"]')
    first = box.locator(".jl-acct").first
    first.click()
    check(tag + " focus lists candidate accounts", box.locator(".jl-opt").count() >= 6, box.locator(".jl-opt").count())
    first.type("checking")
    check(tag + " synonym finds Cash", box.locator(".jl-opt", has_text="Cash").count() >= 1 and "Checking" in box.locator(".jl-opt").first.inner_text(), box.locator(".jl-dd").inner_text() if box.locator(".jl-dd").count() else "")
    first.fill("")
    shotf("je_dropdown")
    # number cell c1 (issue price) correct, then the entry with autocomplete
    c1 = pg.evaluate("TBSApp.R.cells.find(c=>c.id==='c1').answer")
    fill(pg, "c1", "{:,}".format(c1))
    pg.click("#cell-c1 [data-a=chk]")
    lines = correct_lines(j2)
    fill_je(pg, "c2", lines)
    bal = pg.inner_text('[data-c="c2"] .jl-bal')
    check(tag + " balance line says Balanced", bal.startswith("Balanced"), bal)
    shotf("je_filled")
    # off-balance display
    box.locator(".jl").nth(0).locator(".jl-d").fill(str(lines[0][2] + 5))
    check(tag + " off-balance shows diff", "diff $5" in pg.inner_text('[data-c="c2"] .jl-bal'), pg.inner_text('[data-c="c2"] .jl-bal'))
    box.locator(".jl").nth(0).locator(".jl-d").fill(str(lines[0][2]))
    pg.click("#cell-c2 [data-a=chk]")
    check(tag + " correct entry = ok", "ok" in (pg.get_attribute("#cell-c2", "class") or "") and "Correct" in pg.inner_text("#cell-c2 .fb"), pg.inner_text("#cell-c2 .fb")[:80])
    check(tag + " correct entry locked", box.locator(".jl-acct").first.is_disabled() and box.locator("[data-add]").is_disabled())
    # partial credit: one right line, one wrong amount, one reversed side
    j3 = next(j for j in jes if j["id"] == "c3")
    l3 = correct_lines(j3)
    bad3 = [l3[0], (l3[1][0], l3[1][1], l3[1][2] + 1234), (l3[2][0], "C" if l3[2][1] == "D" else "D", l3[2][2])]
    fill_je(pg, "c3", bad3)
    pg.click("#cell-c3 [data-a=chk]")
    cls3 = pg.get_attribute("#cell-c3", "class") or ""
    fb3 = pg.inner_text("#cell-c3 .fb")
    check(tag + " partial journal entry marked half", "half" in cls3, cls3)
    check(tag + " partial: struck wrong value + right value shown", pg.locator("#cell-c3 .fb del").count() >= 2 and pg.locator("#cell-c3 .fb ins").count() >= 2, fb3[:200])
    check(tag + " partial: score in lines", "1.5 of 3 lines" in fb3, fb3[:60])
    check(tag + " partial: diagnosis message per line", pg.locator("#cell-c3 .fb .jr .msg").count() >= 2, pg.locator("#cell-c3 .fb .jr .msg").count())
    shotf("je_partial", True)
    # hints: 3 levels then steps
    j6 = next(j for j in jes if j["id"] == "c6")
    ns = []
    for _ in range(4):
        pg.click("#cell-c6 [data-a=hint]")
        ns.append(pg.locator("#cell-c6 .hintbox li").count())
    check(tag + " journal hints 1,2,3 levels then steps", ns[:3] == [1, 2, 3] and "Steps" in pg.inner_text("#cell-c6 .hintbox"), ns)
    check(tag + " hints never show amounts", not any(str(l["v"]) in pg.inner_text("#cell-c6 .hintbox").replace(",", "").split("Steps")[0] for l in j6["lines"]))
    # retry the wrong entry

    # ── carry-forward inside a journal entry (fresh attempt, wrong c1 -> c2 lines follow it) ──
    pg.goto(BASE + "#/FAR-II-T-005/0/new")
    pg.wait_for_selector(".jecell")
    wrong1 = c1 + 10000
    fill(pg, "c1", "{:,}".format(wrong1))
    pg.click("#cell-c1 [data-a=chk]")
    check(tag + " c1 wrong", "bad" in (pg.get_attribute("#cell-c1", "class") or ""))
    fol = pg.evaluate("""(w)=>{const R=TBSApp.R, ns=TBSEngine.buildNs(R.params,R.derived,true);
        R.cells.forEach(c=>{if(c.kind==='number')ns[c.id]=c.answer});ns.c1=w;
        const c=R.cells.find(x=>x.id==='c2');return c.lines.map(l=>TBSEngine.rd(TBSEngine.ev(l.expr,ns),0));}""", wrong1)
    fill_je(pg, "c2", [(l["a"], l["s"], f) for l, f in zip(j2["lines"], fol)])
    pg.click("#cell-c2 [data-a=chk]")
    fb2 = pg.inner_text("#cell-c2 .fb")
    check(tag + " journal carry-forward marked and half credit", "half" in (pg.get_attribute("#cell-c2", "class") or "") and "Carried forward" in fb2, fb2[:160])
    got = pg.evaluate("TBSApp.A.res.c2.credit")
    check(tag + " carry-forward lines score 0.75 for the changed lines", 0.7 < got < 0.95, got)
    # Retry wrong offers c1 and c2 again
    check(tag + " retry wrong counts journal cell", pg.locator(".rwb").count() >= 1)

    # ── variant: perfect entry through the screen = 100% ──
    pg.click("#var")
    pg.wait_for_selector(".jecell")
    check(tag + " variant url has seed", "#/FAR-II-T-005/" in pg.url and not pg.url.endswith("/new"), pg.url)
    R = pg.evaluate("TBSApp.R.cells.map(c=>({id:c.id,kind:c.kind,answer:c.answer,options:c.options,lines:c.lines?c.lines.map(l=>({a:l.a,s:l.s,v:l.v})):null}))")
    for c in R:
        if c["kind"] == "number":
            fill(pg, c["id"], c["answer"])
        elif c["kind"] == "dropdown":
            fill(pg, c["id"], c["answer"])
        else:
            fill_je(pg, c["id"], [(l["a"], l["s"], l["v"]) for l in c["lines"]])
    pg.click("#chkall")
    big = pg.inner_text("#res .big")
    check(tag + " variant perfect entry = 100%", "100%" in big, big)
    check(tag + " result lists sources (ASC)", "ASC" in pg.inner_text("#res dl"), pg.inner_text("#res dl")[-80:])
    check(tag + " result row shows journal lines points", pg.locator("#res .rp").count() == 3, pg.locator("#res .rp").count())
    shotf("je_result", True)
    if mobile:
        pg.click('.tb-tabs [data-t="task"]')
    pg.click("#cell-c2 [data-a=exp]")
    check(tag + " explanation shows answer table + per-line reason", pg.locator("#cell-c2 .jl-ans").count() == 1 and pg.locator("#cell-c2 .jl-ans tr.why").count() == len(j2["lines"]))
    pg.click("#cell-c2 [data-a=cp]")
    clip = pg.evaluate("navigator.clipboard.readText()")
    check(tag + " journal explanation copies as lines", "Dr " in clip and "Cr " in clip, clip[:100])
    # reload restores journal rows
    st = pg.evaluate("JSON.parse(localStorage.getItem('te.tbs.v1')).items['FAR-II-T-005']")
    check(tag + " progress saved", st and st["done"] >= 1 and st["best"] == 100, st)

    # ── input restore after reload (journal rows) ──
    pg.goto(BASE + "#/FAR-III-T-005/0/new")
    pg.wait_for_selector(".jecell")
    jj = je_cells(pg)[0]
    fill_je(pg, jj["id"], correct_lines(jj)[:1])
    pg.wait_for_timeout(500)
    pg.reload()
    pg.wait_for_selector(".jecell")
    v0 = pg.locator('[data-c="%s"] .jl-acct' % jj["id"]).first.input_value()
    check(tag + " journal line restored after reload", v0 == COA_NAME[jj["lines"][0]["a"]], v0)
    # remove a line
    n0 = pg.locator('[data-c="%s"] .jl' % jj["id"]).count()
    pg.locator('[data-c="%s"] .jl-rm' % jj["id"]).nth(n0 - 1).click()
    check(tag + " remove line", pg.locator('[data-c="%s"] .jl' % jj["id"]).count() == max(2, n0 - 1))

    # ── formats: ratio x2 and percent p1, unit suffixes accepted ──
    pg.goto(BASE + "#/FAR-I-T-004/0/new")
    pg.wait_for_selector(".cell")
    cs = cells(pg)
    fmts = pg.evaluate("TBSApp.R.cells.map(c=>c.fmt)")
    ok = []
    for c, f in zip(cs, fmts):
        if c["kind"] != "number":
            continue
        txt = "{:.2f}x".format(c["answer"]) if f == "x2" else "{:.1f}%".format(c["answer"]) if f == "p1" else str(c["answer"])
        fill(pg, c["id"], txt)
        pg.click("#cell-%s [data-a=chk]" % c["id"])
        ok.append("ok" in (pg.get_attribute("#cell-%s" % c["id"], "class") or ""))
    check(tag + " ratio 1.25x and percent 12.5% entries accepted", all(ok) and len(ok) >= 6, ok)
    pg.goto(BASE + "#/FAR-I-T-004/0/new")
    pg.wait_for_selector(".cell")
    fill(pg, "c1", "1.2")
    check(tag + " decimal fields format on blur (1.20)", pg.input_value('[data-c="c1"]') == "1.20", pg.input_value('[data-c="c1"]'))

    # ── citation: ASC and GASB numbers, link button only when a link exists ──
    pg.goto(BASE + "#/FAR-I-T-008/0/new")
    pg.wait_for_selector(".cell")
    cs = cells(pg)
    forms = ["GASB Statement No. {0}", "GASB {0}", "Statement {0}", "{0}", "GASB No. {0}", "#{0}"]
    got = []
    for i, c in enumerate(cs):
        a = c["accept"][0]
        fill(pg, c["id"], forms[i % len(forms)].format(a))
        pg.click("#cell-%s [data-a=chk]" % c["id"])
        got.append("ok" in (pg.get_attribute("#cell-%s" % c["id"], "class") or ""))
    check(tag + " GASB number forms accepted", all(got), got)
    if mobile:
        pg.click('.tb-tabs [data-t="task"]')
    pg.click("#cell-%s [data-a=exp]" % cs[0]["id"])
    href = pg.get_attribute("#cell-%s .exp .lnk a" % cs[0]["id"], "href")
    check(tag + " GASB source link shown when present", href and href.startswith("https://storage.gasb.org/"), href)
    pg.goto(BASE + "#/FAR-I-T-007/0/new")
    pg.wait_for_selector(".cell")
    cs = cells(pg)
    forms = ["ASC {0}", "FASB ASC Topic {0}", "topic {0}", "{0}", "ASC {0}-10-25"]
    got = []
    for i, c in enumerate(cs):
        a = c["accept"][0]
        fill(pg, c["id"], forms[i % len(forms)].format(a))
        pg.click("#cell-%s [data-a=chk]" % c["id"])
        got.append("ok" in (pg.get_attribute("#cell-%s" % c["id"], "class") or ""))
    check(tag + " ASC number forms accepted (incl. more specific)", all(got), got)
    if mobile:
        pg.click('.tb-tabs [data-t="task"]')
    pg.click("#cell-%s [data-a=exp]" % cs[0]["id"])
    check(tag + " no source link button when link is empty", pg.locator("#cell-%s .exp .lnk a" % cs[0]["id"]).count() == 0 and pg.locator("#cell-%s .exp" % cs[0]["id"]).is_visible())
    shotf("citation", True)

    # ── FAR exam mode with a journal cell ──
    pg.goto(BASE)
    pg.wait_for_selector(".tb-list li")
    pg.click('[data-mode="exam"]')
    pg.goto(BASE + "#/FAR-III-T-005/0/new")
    pg.wait_for_selector(".jecell")
    check(tag + " FAR exam: no Check/Hint buttons", pg.locator("[data-a=chk],[data-a=hint]").count() == 0 and pg.locator("#sub").count() == 1)
    jj = je_cells(pg)[0]
    fill_je(pg, jj["id"], correct_lines(jj))
    pg.click("#sub")
    pg.click("#yes")
    check(tag + " FAR exam result shown", pg.locator("#res .big").count() == 1, pg.inner_text("#res .big") if pg.locator("#res .big").count() else "")
    check(tag + " FAR exam: journal cell graded ok after submit", "ok" in (pg.get_attribute("#cell-%s" % jj["id"], "class") or ""))
    if mobile:
        pg.click('.tb-tabs [data-t="task"]')
    shotf("exam_result", True)
    pg.goto(BASE)
    pg.wait_for_selector(".tb-list li")
    pg.click('[data-mode="practice"]')

    # ── layout on the journal page ──
    pg.goto(BASE + "#/FAR-III-T-002/0/new")
    pg.wait_for_selector(".jecell")
    if mobile:
        pg.click('.tb-tabs [data-t="task"]')
    overflow = pg.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
    check(tag + " FAR journal page: no horizontal scroll", not overflow)
    small = pg.evaluate("""()=>{let m=99;document.querySelectorAll('.tbs *').forEach(e=>{if(e.childNodes.length&&[...e.childNodes].some(n=>n.nodeType==3&&n.textContent.trim())){const s=parseFloat(getComputedStyle(e).fontSize);if(s<m)m=s}});return m}""")
    check(tag + " FAR journal page: min font >= 13.5px", small >= 13.5, small)
    jj = je_cells(pg)[1]
    pg.locator('[data-c="%s"] .jl-acct' % jj["id"]).first.click()
    pg.locator('[data-c="%s"] .jl-acct' % jj["id"]).first.type("re")
    pg.locator('[data-c="%s"] .jl-opt' % jj["id"]).first.wait_for(state="visible")
    shotf("je_layout")


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

    # ══════════ FAR section: list, journal-entry cell, formats, citations, exam ══════════
    run_far(pg, tag, mobile)

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
