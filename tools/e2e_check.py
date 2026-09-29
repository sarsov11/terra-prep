# -*- coding: utf-8 -*-
"""Browser walk-through of the learning features (needs Playwright + Edge).

  py tools/e2e_check.py [port]      serve the folder on 127.0.0.1:<port> first, e.g.  py -m http.server 18471 --bind 127.0.0.1

Steps: seed settings, answer questions (one wrong), set a cause, copy, memo, flashcard, review the card, Insights,
Study plan, method page, then go offline (context.set_offline) and solve again. Screenshots go to tools/screens/.
Exits 1 on any console error or failed check.
"""
import json, os, sys, datetime
from playwright.sync_api import sync_playwright

PORT = sys.argv[1] if len(sys.argv) > 1 else "18471"
BASE = "http://127.0.0.1:%s/" % PORT
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens")
os.makedirs(OUT, exist_ok=True)
errors, checks = [], []


def check(name, ok, info=""):
    checks.append((name, ok, info))
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(info) if info else ""))


def run(pw, tag, viewport, mobile):
    br = pw.chromium.launch(channel="msedge")
    ctx = br.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, permissions=["clipboard-read", "clipboard-write"])
    pg = ctx.new_page()
    pg.on("console", lambda m: errors.append((tag, m.text)) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append((tag, str(e))))
    goal = (datetime.date.today() + datetime.timedelta(days=60)).isoformat()
    pg.goto(BASE + "index.html?nostart")
    pg.evaluate("""g => localStorage.setItem("te.pref.v1", JSON.stringify({exam:"cpa",onboarded:"x",subs:CATALOG.subsOf("cpa"),cur:"reg_area4_individuals",goal:g,goalMark:true,goalMine:true,hours:10}))""", goal)
    pg.goto(BASE + "index.html?nostart")
    pg.wait_for_selector("#todo")
    check(tag + " home plan list", pg.locator(".planlist li").count() == 5)
    check(tag + " home readiness text", "Practice scores can differ from the real exam" in pg.inner_text("body"))
    pg.screenshot(path=os.path.join(OUT, tag + "_home.png"), full_page=True)

    # --- practice: first question wrong on purpose, confidence step is off by default
    pg.goto(BASE + "ox.html?nostart")
    pg.wait_for_selector("#oxb")
    check(tag + " why chips", pg.locator(".why .chip").count() >= 1, pg.locator(".why").inner_text() if pg.locator(".why").count() else "")
    ans = pg.evaluate("() => { var s = GB.today().seq.filter(x=>!x.done)[0]; return GB.item(s.id).mc.a; }")
    wrong = 1 if ans != 1 else 2
    pg.click('#oxb [data-a="%d"]' % wrong)
    pg.wait_for_selector("#cause")
    pre = pg.locator("#cause button[aria-pressed=true]").count()
    check(tag + " cause picker shown, auto value preselected when known", pre in (0, 1), "preselected=%d" % pre)
    pg.click('#cause button[data-v="trap"]')
    check(tag + " cause set", pg.evaluate("() => { var l = GB.state().wlog; return l[l.length-1].cause; }") == "trap")
    pg.click("#cpx")
    pg.wait_for_selector("#cpm .fine")
    clip = pg.evaluate("() => navigator.clipboard.readText()")
    check(tag + " copy explanation", "Correct answer:" in clip, len(clip))
    pg.click(".memo summary")
    pg.fill("#memo", "Remember the limit")
    pg.locator("#memo").blur()
    check(tag + " memo saved", any(v["t"] == "Remember the limit" for v in pg.evaluate("() => GB.state().notes").values()))
    pg.click("#mkc")
    check(tag + " flashcard made", pg.evaluate("() => GB.cardList().length") == 1)
    pg.screenshot(path=os.path.join(OUT, tag + "_answer_tools.png"), full_page=True)

    # --- clipboard blocked: fallback textarea
    pg.evaluate("() => { Object.defineProperty(navigator, 'clipboard', {value: undefined, configurable: true}); document.execCommand = () => false; }")
    pg.click("#cpx")
    pg.wait_for_selector("#cbx")
    check(tag + " copy fallback selects text", pg.evaluate("() => document.getElementById('cbx').selectionEnd > 10"))

    # --- more answers so the readiness range appears (12 more, mixed)
    pg.evaluate("""() => { var ids = GB.ranked(null).slice(0, 14).map(c => c.q); ids.forEach((q, i) => GB.answer(q.i, i % 3 !== 0, {conf: i % 2 ? "sure" : "half", pick: i % 3 !== 0 ? q.mc.a - 1 : (q.mc.a % 4), kind: "x"})); }""")
    pg.goto(BASE + "insights.html?nostart")
    pg.wait_for_selector("#rd .big")
    txt = pg.inner_text("#rd")
    check(tag + " estimated range shown", "Estimated range" in txt, txt.split("\n")[1] if "\n" in txt else txt[:60])
    check(tag + " weekly cause table", "Certain + wrong" in pg.inner_text("#wk"))
    pg.screenshot(path=os.path.join(OUT, tag + "_insights.png"), full_page=True)

    pg.goto(BASE + "cards.html?nostart")
    pg.wait_for_selector("#fl")
    pg.click("#fl"); pg.wait_for_selector("#ok")
    pg.screenshot(path=os.path.join(OUT, tag + "_flashcard.png"), full_page=True)
    pg.click("#ok")
    check(tag + " flashcard graded and rescheduled", pg.evaluate("() => GB.cardList()[0].box") == 1)

    pg.goto(BASE + "plan.html?nostart")
    pg.wait_for_selector(".planlist")
    check(tag + " plan page", "Next 14 days" in pg.inner_text("#out"))
    pg.screenshot(path=os.path.join(OUT, tag + "_plan.png"), full_page=True)
    pg.goto(BASE + "method.html?nostart")
    pg.wait_for_selector("#pick")
    check(tag + " method page has formula", "score = 100" in pg.inner_text("#body"))
    pg.screenshot(path=os.path.join(OUT, tag + "_method.png"), full_page=True)

    # --- offline: service worker must already control the page
    pg.goto(BASE + "index.html?nostart")
    pg.wait_for_function("() => navigator.serviceWorker && navigator.serviceWorker.controller", timeout=20000)
    check(tag + " service worker controls page", True)
    ctx.set_offline(True)
    pg.goto(BASE + "ox.html?nostart")
    pg.wait_for_selector("#oxb", timeout=15000)
    check(tag + " offline: question loads", True)
    pg.wait_for_selector("#pwa-off")
    pg.click('#oxb [data-a="1"]')
    pg.wait_for_selector("#after .verdict")
    check(tag + " offline: answer and explanation", pg.locator("#after .exs").count() == 1)
    pg.screenshot(path=os.path.join(OUT, tag + "_offline.png"))
    pg.goto(BASE + "exam.html?nostart")
    pg.wait_for_selector("#go:not([disabled])", timeout=15000)
    check(tag + " offline: mock exam data loads for every Area", "questions in 5 Areas" in pg.inner_text("#note"), pg.inner_text("#note")[-40:])
    ctx.set_offline(False)
    try:
        br.close()
    except Exception:
        pass


with sync_playwright() as pw:
    run(pw, "desktop", {"width": 1200, "height": 900}, False)
    run(pw, "mobile", {"width": 390, "height": 800}, True)

bad = [e for e in errors if "favicon" not in e[1]]
for e in bad:
    print("CONSOLE ERROR", e)
print("checks: %d passed, %d failed | console errors: %d" % (sum(1 for c in checks if c[1]), sum(1 for c in checks if not c[1]), len(bad)))
sys.exit(1 if bad or any(not c[1] for c in checks) else 0)
