/* Concept cards screen: Area list → topics → one card. Route is the URL hash:
     #/            Areas          #/a/IV   topics of an Area          #/c/CARD-REG-IV-B-01   one card
   Read marks are kept in localStorage "te.cards.read.v1" ({cardId: timestamp}). Data: data/cards_reg.js (tools/build_cards.py). */
(function () {
  "use strict";
  GB.mountNav("learn.html");
  var D = window.CARDS || { areas: [], cards: [] }, esc = GB.esc, stage = document.getElementById("stage");
  var KEY = "te.cards.read.v1", byId = {}, read = {};
  D.cards.forEach(function (c) { byId[c.id] = c; });
  try { read = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { read = {}; }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(read)); } catch (e) {} }
  function nRead(list) { return list.filter(function (c) { return read[c.id]; }).length; }
  function areaCards(a) { return D.cards.filter(function (c) { return c.area === a; }); }
  function areaOf(a) { return D.areas.filter(function (x) { return x.area === a; })[0]; }
  function link(u) { return /^https?:\/\//.test(u) ? u : "#"; }

  function viewAreas() {
    document.title = "Concept cards — " + (window.BRAND || "");
    stage.innerHTML = '<div class="hd"><h1>Concept cards</h1><div class="k num">' + nRead(D.cards) + " / " + D.cards.length + " read</div></div>" +
      '<div class="list">' + D.areas.map(function (a) {
        var l = areaCards(a.area), r = nRead(l), done = l.length && r === l.length;
        return '<a class="row" href="#/a/' + a.area + '"><span class="t"><b>Area ' + esc(a.area) + "</b><span>" + esc(a.title) + "</span>" +
          '<div class="aprog"><i style="width:' + (l.length ? Math.round(r / l.length * 100) : 0) + '%"></i></div></span>' +
          '<span class="go num' + (done ? " done" : "") + '">' + r + " / " + l.length + "</span></a>"; }).join("") + "</div>";
  }

  function viewArea(a) {
    var A = areaOf(a); if (!A) return viewAreas();
    document.title = "Area " + a + " cards — " + (window.BRAND || "");
    var l = areaCards(a), tops = [];
    l.forEach(function (c) { if (tops.indexOf(c.topic) < 0) tops.push(c.topic); });
    stage.innerHTML = '<a class="back" href="#/">← Areas</a><div class="hd" style="padding-top:6px"><h1>Area ' + esc(a) + "</h1>" +
      '<div class="k">' + esc(A.title) + '</div><div class="k num">' + nRead(l) + " / " + l.length + " read</div></div>" +
      tops.map(function (t) {
        return '<section class="tp"><h2>' + esc(t) + '</h2><div class="list">' + l.filter(function (c) { return c.topic === t; }).map(function (c) {
          return '<a class="row" href="#/c/' + esc(c.id) + '"><span class="tick' + (read[c.id] ? " on" : "") + '" aria-hidden="true">' + (read[c.id] ? "✓" : "") + "</span>" +
            '<span class="t"><b>' + esc(c.title) + "</b></span>" + '<span class="go">' + (read[c.id] ? "Read" : "5 min") + "</span></a>"; }).join("") + "</div></section>"; }).join("");
  }

  function viewCard(id) {
    var c = byId[id]; if (!c) return viewAreas();
    document.title = c.title + " — " + (window.BRAND || "");
    var l = areaCards(c.area), i = l.indexOf(c), prev = l[i - 1], next = l[i + 1];
    stage.innerHTML =
      '<a class="back" href="#/a/' + esc(c.area) + '">← Area ' + esc(c.area) + '</a>' +
      '<div class="card-h"><div class="chips"><span class="chip g">Area ' + esc(c.area) + '</span>' +
      (c.from ? '<span class="chip">Testable from ' + esc(c.from) + "</span>" : "") + "</div>" +
      "<h1>" + esc(c.title) + '</h1><div class="tpc">' + esc(c.topic) + "</div></div>" +
      '<section class="blk"><h2>Rules</h2><div class="rules">' + c.rules.map(function (r) { return "<div>" + esc(r) + "</div>"; }).join("") + "</div></section>" +
      '<section class="blk"><h2>Steps</h2><ol class="steps">' + c.steps.map(function (s) { return "<li>" + esc(s) + "</li>"; }).join("") + "</ol></section>" +
      '<section class="blk trap"><h2>Traps</h2><div class="traps">' + c.traps.map(function (s) { return "<div>" + esc(s) + "</div>"; }).join("") + "</div></section>" +
      '<section class="blk"><h2>Example</h2><div class="ex"><p class="q">' + esc(c.ex.q) + "</p>" +
      '<button type="button" class="btn ghost" id="show" aria-expanded="false" aria-controls="ans">Show explanation</button>' +
      '<div class="ans" id="ans" hidden><p class="a">' + esc(c.ex.a) + "</p><ol>" + c.ex.work.map(function (w) { return "<li>" + esc(w) + "</li>"; }).join("") + "</ol></div></div></section>" +
      '<section class="blk"><h2>Sources</h2><ul class="cite">' + c.cites.map(function (x) {
        return '<li><a href="' + esc(link(x.u)) + '" target="_blank" rel="noopener noreferrer">' + esc(x.l) + "</a></li>"; }).join("") + "</ul>" +
      '<p class="fine">Law as of ' + esc(c.asof) + "</p></section>" +
      '<div class="acts">' + (c.node ? '<a class="btn" href="ox.html?s=' + esc(c.sk) + "&node=" + c.node + '">Practice this topic</a>' : "") +
      '<button type="button" class="btn ghost' + (read[c.id] ? " on" : "") + '" id="mark" aria-pressed="' + (read[c.id] ? "true" : "false") + '">' + (read[c.id] ? "✓ Read" : "Mark as read") + "</button></div>" +
      '<div class="pn"><a class="btn ghost" href="' + (prev ? "#/c/" + esc(prev.id) : "#") + '"' + (prev ? "" : ' aria-disabled="true" tabindex="-1"') + '>← Previous</a>' +
      '<a class="btn ghost" href="' + (next ? "#/c/" + esc(next.id) : "#") + '"' + (next ? "" : ' aria-disabled="true" tabindex="-1"') + ">Next →</a></div>";
    document.getElementById("show").onclick = function () {
      var b = this, a = document.getElementById("ans"), open = a.hasAttribute("hidden");
      if (open) a.removeAttribute("hidden"); else a.setAttribute("hidden", "");
      b.setAttribute("aria-expanded", open ? "true" : "false"); b.textContent = open ? "Hide explanation" : "Show explanation";
    };
    document.getElementById("mark").onclick = function () {
      if (read[c.id]) delete read[c.id]; else read[c.id] = Date.now();
      save(); this.classList.toggle("on", !!read[c.id]); this.setAttribute("aria-pressed", read[c.id] ? "true" : "false");
      this.textContent = read[c.id] ? "✓ Read" : "Mark as read";
    };
  }

  function route() {
    var h = (location.hash || "").replace(/^#\/?/, "").split("/");
    if (h[0] === "a" && h[1]) viewArea(h[1]); else if (h[0] === "c" && h[1]) viewCard(h.slice(1).join("/")); else viewAreas();
    window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", route);
  route();
})();
