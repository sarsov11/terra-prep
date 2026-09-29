/* T-account view shared by the Journal Drill (js/je.js) and the TBS journal-entry cell (js/tbs.js).
   TAcct.make(COA, { esc, fmtNum }) -> { tAccounts(items), tHTML(items, multi) }
   items: [{a: account id, s: "D"|"C", v: amount, si: set index}]. COA[id] = { name, cls, n: normal side "D"|"C" }.
   Styles: css/tacct.css. Moved out of je.js unchanged so both screens draw the same accounts. */
(function () {
  "use strict";
  var CLS = { asset: "asset", liability: "liability", equity: "equity", revenue: "revenue", expense: "expense", gain: "gain", loss: "loss",
              "contra-asset": "contra-asset", "contra-liability": "contra-liability", "contra-equity": "contra-equity", "contra-revenue": "contra-revenue" };
  function make(COA, o) {
    var esc = o.esc, fmtNum = o.fmtNum;
    function fmtMoney(v) { return "$" + fmtNum(v); }
    function tAccounts(items) {
      /* items: [{a, s, v, si}] → [{a, dr:[{v,si}], cr:[...], net}] in first-appearance order */
      var order = [], map = {};
      items.forEach(function (it) {
        if (!map[it.a]) { map[it.a] = { a: it.a, dr: [], cr: [] }; order.push(it.a); }
        (it.s === "D" ? map[it.a].dr : map[it.a].cr).push({ v: it.v, si: it.si });
      });
      return order.map(function (a) {
        var t = map[a], d = t.dr.reduce(function (x, y) { return x + y.v; }, 0), c = t.cr.reduce(function (x, y) { return x + y.v; }, 0);
        t.d = d; t.c = c; t.net = d - c; return t;
      });
    }
    function tHTML(items, multi) {
      return tAccounts(items).map(function (t) {
        var acc = COA[t.a], inc = (t.net >= 0 ? "D" : "C") === acc.n, amt = Math.abs(t.net);
        function col(list) {
          return list.map(function (e) { return '<div class="je-te">' + (multi ? '<i>(' + (e.si + 1) + ')</i>' : "") + "<span>" + fmtNum(e.v) + "</span></div>"; }).join("");
        }
        return '<div class="je-t"><div class="je-th">' + esc(acc.name) + '<small>' + CLS[acc.cls] + "</small></div>" +
          '<div class="je-tb"><div class="je-tl">' + col(t.dr) + '</div><div class="je-tr">' + col(t.cr) + "</div></div>" +
          '<div class="je-tt"><span>' + (t.net >= 0 ? "Dr " : "Cr ") + fmtMoney(amt) + "</span><b>" + (inc ? "↑ increase" : "↓ decrease") + "</b></div></div>";
      }).join("");
    }
    return { tAccounts: tAccounts, tHTML: tHTML };
  }
  window.TAcct = { make: make, CLS: CLS };
})();
