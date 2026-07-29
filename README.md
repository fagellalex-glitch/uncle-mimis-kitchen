# Uncle Mimi's Kitchen — Website

A redesign and full migration of the original Weebly site
(`https://unclemimi.weebly.com/`) into a fast, accessible, dependency‑free
static website for a small‑batch artisan bakery on Martha's Vineyard.

- **No framework, no runtime JavaScript required for content** — the page is
  fully rendered HTML and works with JavaScript disabled.
- **No third‑party requests** — fonts, styles, scripts and images are all
  self‑hosted. There is no Weebly, Google Fonts, analytics, or tracking code.
- **Editable from structured data** — all copy, products, and locations live in
  JSON files under [`src/data/`](src/data/); a small Python script regenerates
  the site.

---

## Project structure

```
uncle-mimis-kitchen/
├── build.py                 # Static-site generator (Python 3, stdlib only + macOS `sips`)
├── asset-manifest.json      # Machine-readable image manifest (generated)
├── src/
│   ├── data/                # ← EDIT HERE: content source of truth
│   │   ├── site.json        #   brand, tagline, contact, nav, canonical URL
│   │   ├── story.json       #   "Our Story" copy + sign image
│   │   ├── products.json    #   the six products
│   │   └── locations.json   #   the three retail locations
│   ├── styles/main.css      # Design system (CSS variables, layout, responsive)
│   └── scripts/menu.js      # Progressive enhancement (mobile nav, scrollspy)
├── public/assets/
│   ├── fonts/               # Self-hosted Fraunces + Inter (woff2, variable)
│   └── images/              # Full-resolution source images (descriptively named)
├── raw/                     # Untouched originals downloaded from Weebly (provenance)
├── reference/               # Original page HTML + font CSS, for reference only
└── dist/                    # ← GENERATED output. This is what you deploy.
```

## Requirements

- **macOS** (the build uses the built‑in `sips` tool for image resizing).
- **Python 3** (uses only the standard library). Check with `python3 --version`.

No Node, npm, or internet connection is needed to build.

> Porting off macOS: the only OS dependency is `sips`. Replace the three `sips`
> helpers in `build.py` with ImageMagick (`magick`) or `sharp`/`cwebp` and the
> rest of the build is portable. See **Adding WebP/AVIF** below.

## Build

```bash
python3 build.py
```

This regenerates `dist/` from scratch: responsive image variants, favicons, the
social‑share image, `index.html`, `sitemap.xml`, `robots.txt`, and
`site.webmanifest`.

## Preview / local development

The output is plain static files. Serve the `dist/` folder with any static
server:

```bash
cd dist
python3 -m http.server 8080
# open http://localhost:8080
```

There is no separate "dev server" — what you preview is exactly what deploys.

## Deploy

Upload the **contents of `dist/`** to any static host (Netlify, Vercel, Cloudflare
Pages, GitHub Pages, S3/CloudFront, or classic shared hosting). No server-side
runtime is required.

1. Set your real domain in [`src/data/site.json`](src/data/site.json) → `"url"`
   (used for the canonical link, Open Graph tags, sitemap, and structured data).
2. Run `python3 build.py`.
3. Publish everything inside `dist/` at the site root.

All internal asset paths are **relative**, so the site also works from a
subdirectory without changes.

---

## Updating content (no coding required)

Edit the JSON in `src/data/`, then run `python3 build.py`.

**Change a product description, name, or award**
`src/data/products.json` — each product has `name`, `description`, optional
`tag` (e.g. "Vegan"), and optional `award` (shows a blue prize‑ribbon icon on the
photo; hovering or focusing it reveals `award.label` and `award.detail`).

**Update the logo**
The header, footer, and hero all use your real hand‑drawn "UNCLE MIMI" artwork
at `public/assets/images/brand/uncle-mimi-logo.png` (transparent background).
Replace that file with a new export any time and re‑run `python3 build.py` — no
code changes needed. The build automatically derives two extra variants from
it: a light cream recolor for the hero (`uncle-mimi-logo-hero.png`, since the
original dark ink wouldn't read well over the photo) and the favicon/app‑icon
set. Removing the source file falls back to a typographic wordmark in the
header and hero, and a plain green favicon.

**Scroll‑reveal animation**
Section intros and cards fade/rise into view once as you scroll
(`data-reveal` attribute + `menu.js`). It's pure progressive enhancement: with
JavaScript disabled everything is simply visible immediately, and it's skipped
entirely under `prefers-reduced-motion: reduce`. To add it to a new element,
give it `data-reveal` in `build.py`; stagger multiple items in the same group
with an inline `style="transition-delay:_ms"`.

**Add or change the Instagram link**
`src/data/site.json` → `"instagram"` (full profile URL, or `null` to hide it).
It appears in the footer and the Inquiries contact card.

**Adjust the color palette**
All color is defined once, as CSS custom properties, at the top of
[`src/styles/main.css`](src/styles/main.css) (`--green`, `--terracotta`,
`--cream`, etc. under `:root`). Change a value there and every button, link,
eyebrow, and section tint updates from that single source.

**Swap a product or location photo**
Drop the new file into the matching folder under
`public/assets/images/…`, then point that item's `image.src` at it in the JSON
and update the `alt` text to describe the new photo. Re‑run the build; all
resized variants are regenerated automatically.

**Update a store address, phone, or map pin**
`src/data/locations.json` — `street`, `city`, `state`, `zip`, `phone`
(`+1` E.164 format for the tel: link), `phoneDisplay`, and `lat`/`lng`.
Directions and map links are built from the address automatically.

**Change contact email/phone, tagline, or navigation**
`src/data/site.json`.

**Edit the story or the availability note**
`src/data/story.json` and the `note` field in `src/data/locations.json`.

## Adding WebP/AVIF (optional enhancement)

The build currently emits optimized, responsive **JPEG** variants, because this
environment had no WebP/AVIF encoder available. To add modern formats, install
`cwebp`/`avifenc` (or `sharp`) and extend `make_image()` in `build.py` to also
emit `.webp`/`.avif` siblings, then wrap each `<img>` in a `<picture>` with
`<source type="image/avif">` / `type="image/webp"`. The data model and markup
are structured to make this a localized change.

---

## What was intentionally changed vs. the original

Minor copyediting only (grammar, punctuation, capitalization) — no factual
claims were altered. See
[`CONTENT-MIGRATION-CHECKLIST.md`](CONTENT-MIGRATION-CHECKLIST.md) for a
line‑by‑line record, and [`UNRESOLVED.md`](UNRESOLVED.md) for the short list of
items that need the owner's confirmation.
