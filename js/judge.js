/* Judgment engine — carried over from the Korean and Japanese sister apps'
 * js/judge.js, adapted for the US English frame. English has no particle
 * system to worry about (Korean needs different particles depending on
 * whether the previous syllable ends in a consonant; Japanese needed none
 * of that either), so sentence templates are simply written out directly.
 *
 *   concept/lecture → "read the correct sentences" (shows every correct
 *   released sentence for this topic in a row — not a written lecture)
 *
 * This is the engine that decides what to say and what to show next **the
 * instant** the learner submits an answer.
 *
 * Design principles —
 *   1. Learner action     right/wrong, time, **confidence**, retry
 *   2. Event log           answer_submitted + skill_id
 *   3. Judgment engine     rules + mastery → **classify the misunderstanding** → pick the next step
 *   4. Immediate feedback  one line — **name the concept, gently**
 *   5. Next question       easier / similar / review, chosen automatically
 *
 * ** No LLM call here. ** A rule decides in 0.01 seconds.
 *   Generating a fresh sentence every time is slow, costly, and inconsistent.
 *   An exam-prep product earns trust by returning **the same words for the
 *   same situation** every time. (If an LLM is ever added, its job would be
 *   further downstream — polishing the wording after this engine has
 *   already decided the verdict.)
 *
 * ─────────────────────────────────────────────
 * The axis this engine splits on is **confidence × correctness**.
 *
 *   confident + correct   →  they know it.            move on
 *   confident + wrong     →  **misconception**        ★ most dangerous — they believe they're right
 *   half-sure + correct   →  might be luck.            one more of the same concept
 *   half-sure + wrong     →  they're unsure.            review the concept, then an easier one
 *   guessed + correct     →  it was luck.               start from the concept
 *   guessed + wrong       →  they don't know it yet.    go read the source sentences
 *
 * Looking only at right/wrong collapses these six cases into two. Missing
 * it while confident and missing it while guessing are both "wrong," but
 * they call for opposite responses — the first needs the false belief
 * **broken**, the second needs to be **taught from scratch**.
 */
(function () {
  "use strict";

  /* ── thresholds — kept in one place ─────────────────────
     ★ Scattering numbers through the code makes them drift out of sync when tuned. */
  var T = {
    fast: 6000,          // answered faster than this = "knew it instantly" or "didn't read it"
    slow: 75000,         // took longer than this = it was a close call
    streakWrong: 3,      // this many misses in a row on the same leaf sends it to the reading list
    lowMastery: 0.55,    // below this, treat the leaf as not yet learned
    highMastery: 0.85    // at or above this, it's fine to move on
  };

  /* Confidence — the learner picks it themselves. null if not asked. */
  var CONFIDENCE_LEVELS = [
    { v: "sure", name: "Certain", w: 1.0 },
    { v: "half", name: "Not sure", w: 0.5 },
    { v: "guess", name: "Guessing", w: 0.0 }
  ];

  /* ── feedback copy ──────────────────────────────
     ★★ **No lecturing.** A wrong answer isn't a failure, it's another rep.
       Phrasing like "what you knew just fell apart" grades the learner —
       a first-time test-taker who hears that stops coming back.
     ★★ **Name the concept.** `{concept}` is replaced with that leaf's name.
       "Review this again" is much weaker than "Review **conditions for
       loss recognition on a wash sale** again" — the sentence itself says
       what to do.
     ★ A name-free version (the `_x` suffix) covers cases where no name is available.
     ★ Never evaluate the learner. State **only the next action**. */
  /* Verdict badge shown on screen — `kind` is the name used for logging */
  var LABELS = {
    know: "Knew it", knowFast: "Knew it", misconception: "Misconception", luck: "Lucky guess",
    confused: "Unsure", guessRight: "Guessed right", dontKnow: "Not learned yet", tooFastWrong: "Answered too fast",
    slowRight: "Correct after thinking", right: "Correct", wrong: "Incorrect", streakWrong: "Missed repeatedly", retryRight: "Correct on retry"
  };
  var PHRASES = {
    /* confident + correct */
    know: [
      "Correct. Move on from {concept}.",
      "You know {concept}. On to the next question."
    ],
    know_x: ["Correct. Move on.", "You know this. On to the next question."],

    knowFast: [
      "Correct, right away. Move on from {concept}.",
      "Correct, right away. Moving on from {concept}."
    ],
    knowFast_x: ["Correct, right away. Move on.", "Correct, right away."],

    /* ★ confident + wrong — the case to watch most closely. Never say "wrong." State only what to review. */
    misconception: [
      "You were certain, but that's not right. Take another look at {concept}.",
      "Read {concept} again.",
      "{concept} is an easy one to get backwards. Take another look."
    ],
    misconception_x: [
      "You were certain, but that's not right. Take another look at this.",
      "Read it again."
    ],

    /* half-sure + correct */
    luck: [
      "Correct. Try one more on {concept}.",
      "Correct. Take a look at one more on {concept}."
    ],
    luck_x: ["Correct. Try one more.", "Correct. Take a look at one more."],

    /* half-sure + wrong */
    confused: [
      "Read {concept} again.",
      "Go back to an easier question on {concept}."
    ],
    confused_x: ["Read it again.", "Go back to an easier question."],

    /* guessed + correct */
    guessRight: [
      "Correct, but that was a guess. Go read {concept}.",
      "Go read {concept}."
    ],
    guessRight_x: ["Correct, but that was a guess. Go read the source.", "Go read the source."],

    /* guessed + wrong */
    dontKnow: [
      "Read {concept} first.",
      "You haven't covered {concept} yet. Start by reading it."
    ],
    dontKnow_x: ["Read the source first.", "You haven't covered this yet. Start by reading it."],

    /* when confidence wasn't asked */
    right: ["Correct.", "That's right."],
    right_x: ["Correct.", "That's right."],
    wrong: [
      "Incorrect. Take another look at {concept}.",
      "Incorrect. Read the source for {concept}."
    ],
    wrong_x: ["Incorrect. Take another look.", "Incorrect. Read the source."],

    /* response time */
    tooFastWrong: ["That was answered too fast. Read it all the way through."],
    tooFastWrong_x: ["That was answered too fast. Read it all the way through."],

    slowRight: ["Correct. That took a while, so try one more on {concept}."],
    slowRight_x: ["Correct. That took a while, so try one more."],

    /* cumulative */
    streakWrong: ["You've missed {concept} several times now. Start by reading the source."],
    streakWrong_x: ["You've missed this several times now. Start by reading the source."],

    retryRight: ["Correct this time. {concept} — this is what sticks longest."],
    retryRight_x: ["Correct this time. This is what sticks longest."]
  };

  /* Replaces the `{concept}` placeholder with the concept name. */
  function fillConcept(text, name) {
    return String(text).replace(/\{concept\}/g, name);
  }

  /* Picks copy that fits the situation and **fills in the concept name.**
     ★ Falls back to the `_x` (name-free) version when no name is available.
     ★ A random pick would change on every reload — pin it to the question id instead. */
  function pick(key, seed, concept) {
    var name = String(concept || "").trim();
    /* strip a trailing marker (e.g. ★) so it doesn't read oddly inside a sentence */
    name = name.replace(/\s*★\s*$/, "").trim();
    var a = PHRASES[name ? key : (key + "_x")] || PHRASES[key] || PHRASES["right"];
    var h = 0, s = String(seed || "");
    for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
    var t = a[h % a.length];
    return name ? fillConcept(t, name) : t.replace(/\{concept\}/g, "");
  }

  /* ── judge ─────────────────────────────────────
     input —
       ok        was it correct
       conf      "sure" | "half" | "guess" | null (not asked)
       ms        time to answer, in milliseconds
       attempt   which attempt this is on this question (starting at 1)
       mastery   mastery of this leaf, 0-1 (null if unknown)
       streak    consecutive misses on this leaf
     returns —
       kind      name of the situation (used for logging/stats)
       say       the one line shown to the learner
       next      what to show next
       urgent    must this be addressed right now (a misconception)
  */
  function judge(x) {
    x = x || {};
    var ok = !!x.ok;
    var conf = x.conf || null;
    var ms = x.ms || 0;
    var attempt = x.attempt || 1;
    var mastery = (x.mastery == null) ? null : x.mastery;
    var streak = x.streak || 0;
    var seed = x.qid || "";
    var concept = x.leafName || "";        // ★ the concept name dropped into the sentence

    var kind, next, urgent = false;

    /* 1. missed the same leaf repeatedly — more questions isn't the answer */
    if (!ok && streak + 1 >= T.streakWrong) {
      return { kind: "streakWrong", say: pick("streakWrong", seed, concept),
               next: "lecture", urgent: true, tone: "warn" };
    }

    /* 2. correct on a retry — the moment that sticks best. Brief praise, then move on */
    if (ok && attempt >= 2) {
      return { kind: "retryRight", say: pick("retryRight", seed, concept),
               next: "forward", urgent: false, tone: "good" };
    }

    /* 3. confidence × correctness — the backbone of this engine */
    if (conf === "sure") {
      if (ok) {
        kind = (ms && ms < T.fast) ? "knowFast" : "know";
        next = (mastery != null && mastery >= T.highMastery) ? "skip" : "forward";
      } else {
        /* ★ confident + wrong = a misconception. They believe they're right. Always break it now. */
        kind = "misconception"; next = "same"; urgent = true;
      }
    } else if (conf === "half") {
      if (ok) { kind = "luck"; next = "similar"; }
      else { kind = "confused"; next = "easier"; }
    } else if (conf === "guess") {
      if (ok) { kind = "guessRight"; next = "concept"; }
      else { kind = "dontKnow"; next = "lecture"; }
    } else {
      /* confidence wasn't asked — fall back to response time instead */
      if (!ok && ms && ms < T.fast) { kind = "tooFastWrong"; next = "same"; }
      else if (ok && ms && ms > T.slow) { kind = "slowRight"; next = "similar"; }
      else if (ok) { kind = "right"; next = "forward"; }
      else { kind = "wrong"; next = "same"; }
    }

    /* 4. correct despite low mastery — don't advance yet */
    if (ok && mastery != null && mastery < T.lowMastery && next === "forward")
      next = "similar";

    /* ★ a misconception is shown in **orange**. It should look different from
       a plain miss — this isn't "wrong," it's "a belief just broke."
       Red would bury it among ordinary misses. */
    return { kind: kind, label: LABELS[kind] || kind, say: pick(kind, seed, concept), next: next, urgent: urgent,
             tone: urgent ? "warn" : (ok ? "good" : "bad") };
  }

  /* Next-step actions in plain words — used for on-screen button labels */
  var NEXT_ACTIONS = {
    forward: { t: "Next question", why: "You've got this concept — moving on" },
    skip:    { t: "Next concept", why: "You know this concept" },
    same:    { t: "One more on this concept", why: "Another question on the same concept" },
    similar: { t: "One more like this", why: "Another similar question" },
    easier:  { t: "Start easier", why: "An easier question first" },
    concept: { t: "Read the source", why: "Read every correct released sentence on this topic" },
    lecture: { t: "Read the source", why: "Read every correct released sentence on this topic" }
  };

  window.JUDGE = {
    judge: judge, thresholds: T, confidenceLevels: CONFIDENCE_LEVELS, nextActions: NEXT_ACTIONS,
    /* used by the inspection script — the full list of situation names */
    situations: Object.keys(PHRASES)
  };
})();
