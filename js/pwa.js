/* Offline support and update notice — load on every screen (after brand.js).
   Registers sw.js. When a new version has been downloaded in the background, shows
   "A new version is ready" with a Reload button. Shows "Offline" while the device has no connection. */
(function () {
  "use strict";
  function bar(id, html) {
    var el = document.getElementById(id);
    if (!el) { el = document.createElement("div"); el.id = id; el.className = "pwabar"; el.setAttribute("role", "status"); document.body.appendChild(el); }
    el.innerHTML = html; return el;
  }
  function drop(id) { var el = document.getElementById(id); if (el) el.remove(); }
  function online() {
    if (navigator.onLine) drop("pwa-off");
    else bar("pwa-off", "<span>Offline · answers saved on this device</span>");
  }
  window.addEventListener("online", online); window.addEventListener("offline", online);
  document.addEventListener("DOMContentLoaded", online);

  if (!("serviceWorker" in navigator) || !/^https?:$/.test(location.protocol)) return;
  function offer(w) {
    var b = bar("pwa-new", '<span>A new version is ready.</span><button type="button" class="btn sm" id="pwa-go">Reload</button>');
    b.querySelector("#pwa-go").onclick = function () { w.postMessage("skipWaiting"); };
  }
  var reloaded = false, had = !!navigator.serviceWorker.controller;   /* first install also fires controllerchange — only reload for an update */
  navigator.serviceWorker.addEventListener("controllerchange", function () { if (reloaded || !had) return; reloaded = true; location.reload(); });
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("sw.js").then(function (reg) {
      if (reg.waiting && navigator.serviceWorker.controller) offer(reg.waiting);
      reg.addEventListener("updatefound", function () {
        var w = reg.installing; if (!w) return;
        w.addEventListener("statechange", function () { if (w.state === "installed" && navigator.serviceWorker.controller) offer(w); });
      });
      if (navigator.onLine) reg.update().catch(function () {});
    }).catch(function () {});
  });
})();
