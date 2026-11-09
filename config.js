// ============================================================
//  THE ONE FILE TO EDIT.  Paste your real links here, save, deploy.
//  Every button on every page reads from this list.
//  Leave a link as "" and its buttons scroll to #pricing instead.
// ============================================================
window.VAULT_LINKS = {
  pro:           "",  // Payhip link for the $147 Pro Bundle
  leadMagnet:    "",  // Payhip link for the free checklist (collects emails)
  refund:        "",  // Refund policy page
  terms:         "",  // Terms of service page
  accessibility: ""   // Accessibility statement page
};

// Wires up every <a data-link="..."> on the page. No need to touch this.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("a[data-link]").forEach(function (a) {
    var url = window.VAULT_LINKS[a.dataset.link];
    if (url) {
      a.href = url;
      a.target = "_blank";
      a.rel = "noopener";
    } else {
      a.href = (location.pathname.endsWith("index.html") || location.pathname === "/" ? "" : "/") + "#pricing";
      a.removeAttribute("target");
    }
  });
  var y = document.getElementById("year");
  if (y) y.textContent = String(new Date().getFullYear());
});
