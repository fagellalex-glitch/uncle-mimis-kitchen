/* Uncle Mimi's Kitchen — progressive enhancement.
   The site is fully usable without JS; this only enhances the header
   and adds the product-photo lightbox. Navigation is a plain, always
   visible link list (horizontally scrollable on narrow screens) with
   no toggle/overlay, so there's nothing to animate on open and nothing
   that can glitch. */
(function () {
  "use strict";

  // Shared scroll lock: freezes the page at its current position while an
  // overlay (currently just the lightbox) is open. Plain `overflow: hidden`
  // on body doesn't reliably stop iOS Safari's momentum scroll from
  // continuing to move the page behind a fixed overlay once you're not at
  // the very top. Pinning body at its exact scroll offset via
  // position: fixed removes the scrollable surface entirely, so there's
  // nothing left for momentum to act on.
  var scrollLockY = 0;
  var scrollLockCount = 0;

  function lockScroll() {
    if (scrollLockCount === 0) {
      scrollLockY = window.scrollY || window.pageYOffset || 0;
      document.body.style.top = (-scrollLockY) + "px";
      document.body.classList.add("no-scroll");
    }
    scrollLockCount++;
  }

  function unlockScroll() {
    scrollLockCount = Math.max(0, scrollLockCount - 1);
    if (scrollLockCount === 0) {
      document.body.classList.remove("no-scroll");
      document.body.style.top = "";
      window.scrollTo(0, scrollLockY);
    }
  }

  // Sticky-header shadow once the page is scrolled.
  var header = document.querySelector(".site-header");
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

  // Product photo lightbox: click a baked-good photo to see it larger.
  var lightbox = document.getElementById("lightbox");
  var zoomButtons = Array.prototype.slice.call(document.querySelectorAll(".product-card__zoom"));
  if (lightbox && zoomButtons.length) {
    var lbImg = lightbox.querySelector(".lightbox__img");
    var lbCaption = lightbox.querySelector(".lightbox__caption");
    var lbClose = lightbox.querySelector(".lightbox__close");
    var lbScrim = lightbox.querySelector(".lightbox__scrim");
    var lbLastFocused = null;

    function openLightbox(trigger) {
      lbLastFocused = trigger;
      lbImg.src = trigger.getAttribute("data-lightbox-src") || "";
      lbImg.alt = trigger.getAttribute("data-lightbox-alt") || "";
      lbImg.width = trigger.getAttribute("data-lightbox-w") || "";
      lbImg.height = trigger.getAttribute("data-lightbox-h") || "";
      lbCaption.textContent = trigger.getAttribute("data-lightbox-caption") || "";
      lightbox.setAttribute("data-open", "true");
      lockScroll();
      lbClose.focus();
      document.addEventListener("keydown", onLbKeydown);
    }

    function closeLightbox() {
      lightbox.removeAttribute("data-open");
      unlockScroll();
      document.removeEventListener("keydown", onLbKeydown);
      if (lbLastFocused) lbLastFocused.focus();
    }

    function onLbKeydown(e) {
      if (e.key === "Escape") { closeLightbox(); return; }
      if (e.key === "Tab") {
        // The close button is the only focusable control in the dialog.
        e.preventDefault();
        lbClose.focus();
      }
    }

    zoomButtons.forEach(function (btn) {
      btn.addEventListener("click", function () { openLightbox(btn); });
    });
    lbClose.addEventListener("click", closeLightbox);
    lbScrim.addEventListener("click", closeLightbox);
  }
})();
