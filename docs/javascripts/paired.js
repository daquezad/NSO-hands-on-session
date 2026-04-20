/**
 * Story 3.3 — copy acknowledgment (UX-DR23).
 * Story 3.7 — also announces to global #css-a11y-announcer (polite, one region in main.html).
 */
(function () {
  "use strict";

  function announceCopied() {
    var ann = document.getElementById("css-a11y-announcer");
    if (ann) {
      ann.textContent = "Copied";
      window.setTimeout(function () {
        ann.textContent = "";
      }, 1600);
    }
  }

  function findLiveRegion(paired) {
    return paired && paired.querySelector(".paired__live");
  }

  document.body.addEventListener("click", function (e) {
    var btn = e.target.closest(
      ".paired__command button.md-clipboard, .paired__command .md-clipboard"
    );
    if (!btn) return;
    var paired = btn.closest(".paired");
    var live = findLiveRegion(paired);
    if (!live) return;

    window.setTimeout(function () {
      live.textContent = "Copied";
      announceCopied();
      window.setTimeout(function () {
        live.textContent = "";
      }, 1600);
    }, 150);
  });
})();
