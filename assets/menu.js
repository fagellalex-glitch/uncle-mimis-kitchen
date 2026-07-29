/* Uncle Mimi's Kitchen — progressive enhancement.
   The site is fully usable without JS; this only enhances the header. */
(function () {
  "use strict";

  var header = document.querySelector(".site-header");
  var toggle = document.querySelector(".nav-toggle");
  var drawer = document.querySelector(".mobile-nav");
  if (!drawer || !toggle) return;

  var panel = drawer.querySelector(".mobile-nav__panel");
  var scrim = drawer.querySelector(".mobile-nav__scrim");
  var closeBtn = drawer.querySelector(".mobile-nav__close");
  var lastFocused = null;

  function focusable() {
    return Array.prototype.slice.call(
      panel.querySelectorAll('a[href], button:not([disabled])')
    ).filter(function (el) { return el.offsetParent !== null; });
  }

  function openMenu() {
    lastFocused = document.activeElement;
    drawer.setAttribute("data-open", "true");
    toggle.setAttribute("aria-expanded", "true");
    document.body.classList.add("no-scroll");
    var f = focusable();
    if (f.length) f[0].focus();
    document.addEventListener("keydown", onKeydown);
  }

  function closeMenu(restoreFocus) {
    drawer.removeAttribute("data-open");
    toggle.setAttribute("aria-expanded", "false");
    document.body.classList.remove("no-scroll");
    document.removeEventListener("keydown", onKeydown);
    if (restoreFocus !== false && lastFocused) lastFocused.focus();
  }

  function onKeydown(e) {
    if (e.key === "Escape") { closeMenu(); return; }
    if (e.key === "Tab") {
      var f = focusable();
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  }

  toggle.addEventListener("click", function () {
    if (drawer.getAttribute("data-open") === "true") closeMenu();
    else openMenu();
  });
  if (closeBtn) closeBtn.addEventListener("click", function () { closeMenu(); });
  if (scrim) scrim.addEventListener("click", function () { closeMenu(); });

  // Close when a navigation link is chosen; keep focus at the destination.
  panel.addEventListener("click", function (e) {
    var link = e.target.closest("a[href]");
    if (link) closeMenu(false);
  });

  // Sticky-header shadow once the page is scrolled.
  var onScroll = function () {
    if (header) header.setAttribute("data-scrolled", window.scrollY > 8 ? "true" : "false");
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  // Scrollspy: mark the current section link with aria-current.
  var links = Array.prototype.slice.call(document.querySelectorAll('[data-spy]'));
  var sections = links
    .map(function (l) { return document.querySelector(l.getAttribute("href")); })
    .filter(Boolean);

  if ("IntersectionObserver" in window && sections.length) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var id = "#" + entry.target.id;
        links.forEach(function (l) {
          if (l.getAttribute("href") === id) l.setAttribute("aria-current", "true");
          else l.removeAttribute("aria-current");
        });
      });
    }, { rootMargin: "-45% 0px -50% 0px", threshold: 0 });
    sections.forEach(function (s) { spy.observe(s); });
  }

  // Scroll reveal: fade + rise elements into view once, skipped entirely
  // under reduced-motion (they simply stay visible, per main.css defaults).
  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var revealEls = Array.prototype.slice.call(document.querySelectorAll("[data-reveal]"));

  if (!reduceMotion && "IntersectionObserver" in window && revealEls.length) {
    revealEls.forEach(function (el) { el.classList.add("is-hidden"); });
    var reveal = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.remove("is-hidden");
        obs.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.1 });
    revealEls.forEach(function (el) { reveal.observe(el); });
  }
})();
