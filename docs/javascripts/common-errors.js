/**
 * Story 3.4 — open first Common Errors disclosure per group (web); print CSS expands all.
 */
(function () {
  "use strict";
  function openFirst() {
    document.querySelectorAll(".css-common-errors").forEach(function (wrap) {
      var first = wrap.querySelector(":scope > details.css-common-error");
      if (first) first.setAttribute("open", "");
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", openFirst);
  } else {
    openFirst();
  }
})();
