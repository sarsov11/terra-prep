/* Loads the data file (data/<id>.js) for the subject being studied right now — place this
   before store.js on every screen. js/brand.js, catalog.js, and data/ready.js must already
   be loaded.
   If the chosen subject isn't ready yet, fall back to the first ready subject among the
   learner's chosen subjects, and if none of those are ready, fall back to any ready subject.
   Storage-key prefix — this app uses "te." (must not collide with the sister apps' "tj.",
   "jg.", "mj." prefixes — if served from the same github.io, browser storage would mix). */
(function () {
  "use strict";
  var P = {};
  try { P = JSON.parse(localStorage.getItem("te.pref.v1") || "{}"); } catch (e) {}
  var R = window.READY || {};
  var want = new URLSearchParams(location.search).get("s");
  var cur = want && R[want] ? want : P.cur;
  if (!R[cur]) cur = (P.subs || []).filter(function (s) { return R[s]; })[0] || Object.keys(R)[0];
  if (want && R[want] && P.cur !== want) {
    P.cur = want;
    try { localStorage.setItem("te.pref.v1", JSON.stringify(P)); } catch (e) {}
  }
  window.TJ_CUR = cur;
  if (cur) document.write('<script src="data/' + cur + '.js?v=' + (R[cur].v || "") + '"><\/script>');

  /* Brand substitution — replaces {{BRAND}} in <title> with the name set in js/brand.js.
     Runs once per screen here (the nav logo name is set separately in store.js). */
  if (window.BRAND) document.title = document.title.replace(/\{\{BRAND\}\}/g, window.BRAND);
})();
