# QA & Browser‑Testing Checklist

This build was produced and verified on macOS. The static output was validated
programmatically, and the rendered pages were checked in **headless Chrome**
(via the DevTools Protocol) at multiple viewport widths. Node/npm and Lighthouse
were **not** available in the environment, so the Lighthouse score and the
interactive/cross‑browser items marked **⧗** should be spot‑checked once before
go‑live — the site is built to make them pass.

> **The hamburger menu has been removed entirely (owner's decision).** After
> several rounds of real, distinct bugs in the off‑canvas drawer (documented
> below for the record — each was a genuine fix, verified, and confirmed by
> the owner as *not* the same issue recurring), a glitch on real phones
> persisted. Rather than keep chasing device‑specific rendering behavior
> this environment's headless testing structurally cannot reproduce
> (`--disable-gpu` forces software rendering, which doesn't exhibit the same
> compositor behavior as a real phone), the toggle/drawer/scrim/panel were
> removed outright. Navigation is now a plain, always‑visible link list in
> the header — horizontally scrollable on narrow screens — with no JS
> required to use it, no overlay, no animation, and therefore nothing left
> that can glitch. The notes below are kept as a record of what was
> genuinely fixed along the way, not as claims about the current
> implementation, which no longer has an off‑canvas panel at all.
>
> **Update — the owner then asked for the header/nav bar itself to be
> removed on mobile**, not just the hamburger (the always‑visible link row
> from the previous fix was still technically "a nav bar"). `.site-header`
> is now `display: none` below 860px and `display: block` at 860px and up —
> on mobile the page opens directly into the hero, which already carries
> the logo and both CTAs, so branding isn't lost. `--header-h` is `0px` on
> mobile accordingly (no sticky header left to clear), reinstated to `76px`
> only at the desktop breakpoint. Verified: `getComputedStyle(...).display`
> is `"none"` at 390px and `"block"` at 1440px; a footer nav link jump to
> `#products` on mobile lands with exactly `24px` clearance (`1.5rem`,
> matching `scroll-margin-top` — no header to account for anymore); zero
> horizontal overflow at either width; lightbox interaction set re-verified
> unaffected.
> **Bug found and fixed during the browser pass:** at ≤375px the off‑canvas
> mobile‑nav panel (`transform: translateX(100%)`) created horizontal overflow
> (`scrollWidth` 680 vs viewport 320) that `body { overflow-x: hidden }` could not
> contain. Fixed by clipping the panel at its own fixed container
> (`.mobile-nav { overflow: hidden }`). Re‑measured: `scrollWidth == innerWidth`
> at 320, 375, 500, and 1440px. ✔
>
> **Inconsistency found and fixed in a later pass:** the SVG favicon and the
> raster favicon/apple‑touch‑icon were built from two unrelated sources — a
> hand‑authored wheat icon (SVG) vs. a cropped photo of challah bread (PNG/ICO) —
> so the browser‑tab icon differed depending on browser support, and neither
> matched the site's brand color after the palette changed to green. Fixed by
> deriving both from the same source: the SVG uses a simplified vector of the
> real logo's zig‑zag mark on brand green; the PNG/ICO/apple‑touch‑icon are the
> actual logo artwork composited onto a plain cream square. Verified the SVG's
> fill is `#2c5f47` (brand green, not the old orange) and the apple‑touch‑icon
> visually matches the header logo.
>
> **Real bug found and fixed (reported by the owner testing on their phone):**
> the mobile menu "glitched" on open. Root cause: `.mobile-nav` (`position:
> fixed; inset: 0`) was nested *inside* `<header>`, and the header has
> `backdrop-filter` for its frosted‑glass effect — which, per the CSS spec,
> makes any ancestor with `backdrop-filter`/`filter`/`transform` a new
> containing block for `position: fixed` descendants. So `inset: 0` was
> resolving against the ~68px‑tall header box instead of the real viewport,
> squeezing the entire nav panel (all four links + the CTA button) into a
> sliver at the top of the screen instead of covering it. Confirmed via
> `getBoundingClientRect()` before (`h: 124`) and after (`h: 844`, matching
> the emulated viewport) the fix, which simply moved the `.mobile-nav` markup
> to be a sibling of `<header>` rather than a child. Re‑verified open/close
> (button, scrim, Escape, link‑click), focus handling, and zero horizontal
> overflow, all via real DevTools Protocol interaction — not just code review.
>
> **New feature added:** clicking a product photo now opens it larger in an
> accessible lightbox (focus moves to the close button, Tab is trapped inside,
> Escape/scrim/✕ all close it and restore focus to the photo that was
> clicked, body scroll locks while open). Verified via the same real‑browser
> method as above, on both desktop and a 390px mobile viewport (no horizontal
> overflow in either).
>
> **Bug found and fixed (reported by the owner testing on their phone):** the
> "Custom Orders" button inside the mobile menu was rendering at the nav
> links' oversized 26px serif font with only 4px of horizontal padding
> (should be ~16px sans‑serif with 24px padding), making it look
> disproportionate and contributing to a layout "glitch" during the open
> animation. Root cause: `.mobile-nav a` (specificity `.class` + `a`) beat
> the plain `.btn` class's own font‑size/padding rules, because the CTA is an
> `<a class="btn btn--primary">` sibling of `<nav>`, not a link *inside* it —
> so the broad selector unintentionally caught it too. Fixed by scoping the
> rule to `.mobile-nav nav a`. Confirmed via computed styles before (26.15px
> font, `13.6px 4px` padding, 72px tall) and after (16.46px font, `12px 24px`
> padding, 53px tall) the fix. Also added `will-change: transform` /
> `translate3d` to the panel as a defensive measure for smoother
> GPU‑composited animation on real mobile hardware, which headless testing
> can't fully validate.
>
> **Investigated, not reproducible:** the owner also reported the product
> lightbox not opening in Chrome specifically (worked in Safari). Verified
> the live production site's `main.css`/`menu.js` were correct and current,
> and reproduced the click‑to‑open flow successfully in a cache‑disabled
> fresh Chrome session against the live domain. Owner confirmed it started
> working after a hard refresh — consistent with a stale browser cache
> rather than a code defect.
>
> **Menu glitch persisted after the button-sizing fix — real root cause
> found and fixed.** The owner confirmed the glitch was still happening on
> a real phone. Frame-by-frame CDP screencast capture during the open
> transition couldn't reproduce it, which pointed at the likely explanation:
> this test environment runs headless Chrome with `--disable-gpu` (forced
> software rendering), which doesn't exhibit the same behavior as a real
> device's GPU compositor. The suspect: `.mobile-nav` toggled CSS
> `visibility` at the exact same moment its child's `transform` animation
> started — a combination known to cause a real GPU compositor to briefly
> paint a stale/unanimated frame before the transform takes over (a "layer
> promotion glitch"), even though it renders perfectly in software-rendered
> testing. Fixed by removing the `visibility` toggle entirely — the panel is
> now always laid out off-screen (never removed from the render tree), so
> opening it is a single uninterrupted transform animation. Replaced
> `visibility:hidden`'s side-effect of removing the closed panel from the
> tab order with the explicit `inert` HTML attribute (present in the markup
> by default, so it's correct even with JavaScript disabled; toggled by
> `menu.js` on open/close). Re-verified the full interaction set — initial
> `inert` state, open, close via ✕/Escape/link-click, and the resulting
> `inert` state after each — all correct, with zero console errors.
>
> **Glitch persisted a second time — real root cause finally isolated.** The
> owner narrowed it down precisely: smooth at the very top of the page,
> glitches the instant you've scrolled at all before opening the menu. That
> detail pointed at a different, well‑documented mobile Safari bug: plain
> `overflow: hidden` on `<body>` does not reliably stop the page from
> continuing to move (via momentum/inertia scrolling) behind a fixed overlay
> once you're not at the very top — that residual motion fighting the
> panel's own entrance animation is what read as a glitch, and explains why
> it never happened at scrollY 0 (nothing to leak). Fixed by replacing the
> scroll lock with the standard, battle‑tested pattern: capture the exact
> scroll offset, pin `<body>` at `position: fixed; top: -{offset}px`, and
> restore the scroll position on close — removing the scrollable surface
> entirely while locked rather than merely hiding overflow. Extracted into a
> shared `lockScroll`/`unlockScroll` pair used by both the mobile menu and
> the product lightbox, since both had the same underlying exposure.
> Verified via CDP: scrolled to `scrollY: 886`, opened the menu, confirmed
> `body { position: fixed; top: -886px }` and `window.scrollY === 0` while
> open, then confirmed `scrollY` was restored to exactly `886` on close.
> Re‑verified the lightbox's full interaction set still passes using the
> shared lock.

## ✅ Verified programmatically (all passing)

- **Production build runs clean** — `python3 build.py` exits 0 with no errors.
- **All 42 referenced assets return HTTP 200** when serving `dist/` — CSS, JS,
  fonts, favicons, OG image, and every responsive image variant. Zero 404s.
- **Filename casing** — every referenced file exists with exact‑case match
  (safe for case‑sensitive Linux hosts).
- **No Weebly/anti‑patterns** — no reference to `weebly`, `editmysite`, Weebly
  CDN URLs, `href="#"`, empty buttons, `TODO`/`lorem`/`placeholder`, or the
  obfuscated `[email protected]` string anywhere in the output.
- **Single `<h1>`**, logical heading order (h1→h2→h3, footer h2), no skipped
  levels.
- **Every `<img>` has** `alt`, explicit `width`+`height`, `srcset`, and `sizes`.
- **Hero image** loads eagerly with `fetchpriority="high"` + a matching
  `<link rel="preload">`; all other images are `loading="lazy"`.
- **All in‑page anchors resolve** (`#story`, `#products`, `#contact`,
  `#locations`, `#top`, `#main`).
- **Contact links functional & correctly formatted** — one `mailto:` and four
  E.164 `tel:` links; Google Maps directions/search URLs are well‑formed and
  URL‑encoded.
- **Content fidelity** — automated check confirms all 34 original copy strings
  are present verbatim.
- **SEO files present & valid** — `robots.txt`, `sitemap.xml`,
  `site.webmanifest`, canonical link, Open Graph + Twitter tags, and
  `Bakery` JSON‑LD (no fabricated ratings, hours, or prices).
- **Zero console errors/warnings and zero failed network requests** — measured
  via a real DevTools Protocol session loading the production build (not just
  static analysis).
- **Brand consistency** — header logo, footer logo, hero logo, and both favicon
  formats (SVG + raster) now derive from the same real artwork/color system; no
  leftover colors from the previous palette anywhere in `dist/`.
- **Scroll‑reveal verified in three states via real browser automation, not
  just code review**: (1) fresh load — all 15 `data-reveal` elements start
  `.is-hidden`; (2) scrolling through the page — each group's `.is-hidden` is
  removed as it enters the viewport, reaching 0 remaining by the bottom;
  (3) with JavaScript disabled and with `prefers-reduced-motion: reduce`
  emulated — 0 elements ever get `.is-hidden` in either case, i.e. content is
  immediately visible with no animation.

## ✅ Verified in headless Chrome

- **No horizontal overflow** — `scrollWidth == innerWidth` measured at 320, 375,
  500, and 1440 px.
- **Full‑page renders inspected** at 320 px (mobile), 390 px (mobile), and
  1440 px (desktop): correct layout, aligned product/location cards, headings
  wrap cleanly and clear the sticky header, images are undistorted, and the
  Google Maps embeds load. Screenshots: `reference/qa-*.png`.
- **Graceful map fallback** confirmed — when an embed hadn't finished loading,
  the "Map preview unavailable · Open in Google Maps" fallback showed.

## ⧗ Recommended final spot‑check before go‑live

Remaining widths to eyeball (all built with the same fluid system):
**430 · 768 · 1024 · 1280 · 1920 px.**

- [ ] Mobile nav: all four links plus "Custom Orders" are visible without
      opening anything; the link row scrolls horizontally if it doesn't fully
      fit; tapping a link scrolls to the right section with the header
      correctly clear of the heading. *(No toggle/overlay exists anymore —
      see the "hamburger menu removed" note below.)*
- [ ] Keyboard‑only: skip link appears on first Tab; visible focus ring on every
      interactive element; full nav reachable.
- [ ] `prefers-reduced-motion: reduce` disables smooth scroll, hover zoom, and
      transitions. *(Implemented in CSS.)*
- [ ] JavaScript disabled: all content, links, and contact info still work.
      Navigation itself needs no JS at all now; only the product lightbox does.
- [ ] Maps: each embed shows the correct store; if an embed is blocked, the
      fallback "Open in Google Maps" link is present.
- [ ] Console shows **no errors** and the Network panel shows **no failed
      requests** and **no third‑party hosts**.
- [ ] Cross‑browser: current Chrome, Safari, Firefox, Edge; iOS Safari + Android
      Chrome.
- [ ] Lighthouse targets: Performance ≥90, Accessibility ≥95, Best Practices ≥95,
      SEO ≥95. The build is optimized for these (local assets, responsive images,
      lazy loading, preloaded fonts with `font-display: swap`, ~115 KB total font
      payload, minimal JS, stable image dimensions).

## Notes for the tester

- Serve the **built** folder, not the source: `cd dist && python3 -m http.server`.
- `color-mix()` and `aspect-ratio` are used; both are supported in all current
  evergreen browsers (Safari 16.4+, Chrome/Edge 111+, Firefox 113+).
