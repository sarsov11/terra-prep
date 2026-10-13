/* ═══════════════════════════════════════════════════════════
   {{BRAND}} — exam / series / subject catalog (US English frame)

   First-time setup asks "Which exam are you taking?" → (if the exam has a
   series) which series → which subjects. Each subject's material lives in
   one data/<file>.js. Only a subject with material loads; others show
   "Coming soon." Which subjects are ready is reported by data/ready.js
   (a pipeline artifact) — counts are never hard-coded here.

   CPA candidates sit for REG on their own schedule (no single fixed test
   date), so date stays null and the learner enters their own test date on
   the Settings screen. When date is null, GB.goal() just falls back to
   today as a placeholder goal — nothing breaks.

   To add CFA Level I — Ethics once its data lands in data/cfa_l1_ethics.js,
   add a subject entry and an EXAMS entry the same way as REG below (3
   choices per question instead of REG's 4 — the app already supports 3-5).
   ═══════════════════════════════════════════════════════════ */
(function () {
  "use strict";
  /* Subjects — key is the data/ filename (letters, digits, underscore). name is the display name. */
  var SUBJECTS = {
    reg_tax_procedures: { name: "Federal Tax Procedures" },
    reg_property_transactions: { name: "Federal Taxation of Property Transactions" },
    reg_individuals: { name: "Federal Taxation of Individuals" },
    reg_entities: { name: "Federal Taxation of Entities" },
    cfa_l1_ethics: { name: "Ethical and Professional Standards" }
  };

  /* Exams — an exam with only one series omits the series list. */
  var EXAMS = [
    { id: "cpa", name: "US CPA — REG (Taxation)", sub: "Offered year-round at Prometric testing centers — enter your own test date on the Settings screen.",
      date: null, subs: ["reg_tax_procedures", "reg_property_transactions", "reg_individuals", "reg_entities"] },
    { id: "cfa1", name: "CFA Level I", sub: "Computer-based testing available year-round — enter your own test date on the Settings screen.",
      date: null, series: [
        { id: "ethics", name: "Ethics", subs: ["cfa_l1_ethics"] } ] }
  ];

  function exam(id) { return EXAMS.filter(function (e) { return e.id === id; })[0] || null; }
  function series(examId, sid) {
    var e = exam(examId); if (!e || !e.series) return null;
    return e.series.filter(function (s) { return s.id === sid; })[0] || null;
  }
  /* The subjects this learner is taking — determined by exam + series */
  function subsOf(examId, sid) {
    var e = exam(examId); if (!e) return [];
    if (!e.series) return e.subs.slice();
    var s = series(examId, sid); return s ? s.subs.slice() : [];
  }
  function ready(id) { return !!(window.READY && window.READY[id]); }
  function count(id) { return (window.READY && window.READY[id] && window.READY[id].n) || 0; }

  window.CATALOG = { SUBJECTS: SUBJECTS, EXAMS: EXAMS, exam: exam, series: series, subsOf: subsOf,
                     ready: ready, count: count,
                     name: function (id) { return (SUBJECTS[id] || { name: id }).name; } };
})();
