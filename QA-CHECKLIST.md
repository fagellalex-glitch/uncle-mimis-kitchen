# QA & Browser‑Testing Checklist

This build was produced and verified on macOS. The static output was validated
programmatically, and the rendered pages were checked in **headless Chrome**
(via the DevTools Protocol) at multiple viewport widths. Node/npm and Lighthouse
were **not** available in the environment, so the Lighthouse score and the
interactive/cross‑browser items marked **⧗** should be spot‑checked once before
go‑live — the site is built to make them pass.

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

- [ ] Mobile menu: opens/closes via button, scrim, ✕, Escape, and auto‑closes on
      link tap; body scroll locks while open; focus is trapped and returns to the
      toggle on close. *(Implemented in `menu.js`.)*
- [ ] Keyboard‑only: skip link appears on first Tab; visible focus ring on every
      interactive element; full nav reachable.
- [ ] `prefers-reduced-motion: reduce` disables smooth scroll, hover zoom, and
      transitions. *(Implemented in CSS.)*
- [ ] JavaScript disabled: all content, links, and contact info still work
      (progressive enhancement — only the mobile drawer needs JS, and desktop nav
      is always visible ≥860px).
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
