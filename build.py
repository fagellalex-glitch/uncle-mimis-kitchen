#!/usr/bin/env python3
"""
Uncle Mimi's Kitchen — static site build.

Reads structured content from src/data/*.json and the source assets in
public/assets, then renders a fully static, dependency-free site into dist/.

Responsibilities
  * Generate responsive JPEG variants (via macOS `sips`) + width/height metadata
  * Generate the social-share (OG) image and favicons from real brand photos
  * Render index.html from small Python "component" functions
  * Emit robots.txt, sitemap.xml, site.webmanifest and an asset-manifest.json

Usage:   python3 build.py
Output:  ./dist   (serve the folder root; no dev server required)
"""

import html
import json
import os
import struct
import shutil
import subprocess
from datetime import date, timezone, datetime
from urllib.parse import quote_plus, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
PUBLIC = os.path.join(ROOT, "public")
DIST = os.path.join(ROOT, "dist")
DATA = os.path.join(SRC, "data")

JPEG_QUALITY = "78"
MANIFEST = []  # collected per-image records for asset-manifest.json


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def esc(s):
    """Escape a text node."""
    return html.escape(str(s), quote=False)


def attr(s):
    """Escape an attribute value."""
    return html.escape(str(s), quote=True)


def sips(*args):
    subprocess.run(["sips", *args], check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def dims(path):
    out = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
        check=True, capture_output=True, text=True).stdout
    w = h = 0
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("pixelWidth:"):
            w = int(line.split(":")[1])
        elif line.startswith("pixelHeight:"):
            h = int(line.split(":")[1])
    return w, h


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


# --------------------------------------------------------------------------
# responsive image pipeline
# --------------------------------------------------------------------------
def make_image(rel_src, widths, section, alt):
    """
    Produce downscaled JPEG variants of PUBLIC/<rel_src> into DIST/<dir>.
    Returns a dict: {src, srcset, w, h} where src/w/h describe the largest
    variant (used for width/height attributes -> stable aspect ratio).
    """
    src_path = os.path.join(PUBLIC, rel_src)
    ow, oh = dims(src_path)
    rel_dir = os.path.dirname(rel_src)
    stem = os.path.splitext(os.path.basename(rel_src))[0]
    out_dir = os.path.join(DIST, rel_dir)
    ensure_dir(out_dir)

    # only widths we can produce without upscaling; always include the cap
    targets = sorted({w for w in widths if w < ow} | {min(max(widths), ow)})
    variants = []
    for w in targets:
        out_rel = f"{rel_dir}/{stem}-{w}.jpg"
        out_path = os.path.join(DIST, out_rel)
        sips("--resampleWidth", str(w), "-s", "format", "jpeg",
             "-s", "formatOptions", JPEG_QUALITY, src_path, "--out", out_path)
        vw, vh = dims(out_path)
        variants.append((out_rel, vw, vh))

    largest = variants[-1]
    srcset = ", ".join(f"{p} {w}w" for p, w, h in variants)
    MANIFEST.append({
        "section": section,
        "source_original": rel_src,
        "original_dimensions": f"{ow}x{oh}",
        "output_widths": [w for _, w, _ in variants],
        "output_format": "jpeg",
        "alt": alt,
    })
    return {"src": largest[0], "w": largest[1], "h": largest[2], "srcset": srcset}


def make_logo(site):
    """Prepare the header/footer logo if the owner's file is present; else None."""
    rel = site.get("logo")
    if not rel:
        return None
    src = os.path.join(PUBLIC, rel)
    if not os.path.exists(src):
        return None
    out_rel = "assets/images/brand/uncle-mimi-logo.png"
    out_path = os.path.join(DIST, out_rel)
    ensure_dir(os.path.dirname(out_path))
    sips("--resampleHeight", "96", "-s", "format", "png", src, "--out", out_path)
    w, h = dims(out_path)
    return {"src": out_rel, "w": w, "h": h}


def write_png_rgba(path, width, height, rgba):
    import zlib
    def chunk(ctype, cdata):
        c = ctype + cdata
        return struct.pack(">I", len(cdata)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    stride = width * 4
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw += rgba[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    with open(path, "wb") as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", b""))


def make_hero_logo(site, color=(253, 244, 234)):
    """A light-recolored version of the real logo (same artwork, same
    shapes) for placement directly over the dark hero photo, where the
    original dark ink wouldn't have enough contrast."""
    rel = site.get("logo")
    if not rel:
        return None
    src = os.path.join(PUBLIC, rel)
    if not os.path.exists(src):
        return None
    w, h, rgba = read_png_rgba(src)
    out = bytearray(rgba)
    for i in range(0, len(out), 4):
        if out[i + 3] > 0:
            out[i], out[i + 1], out[i + 2] = color
    out_rel = "assets/images/brand/uncle-mimi-logo-hero.png"
    out_path = os.path.join(DIST, out_rel)
    ensure_dir(os.path.dirname(out_path))
    write_png_rgba(out_path, w, h, bytes(out))
    return {"src": out_rel, "w": w, "h": h}


def picture_img(img, alt, sizes, klass="", eager=False):
    loading = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    cls = f' class="{attr(klass)}"' if klass else ""
    return (
        f'<img{cls} src="{attr(img["src"])}" srcset="{attr(img["srcset"])}" '
        f'sizes="{attr(sizes)}" width="{img["w"]}" height="{img["h"]}" '
        f'alt="{attr(alt)}" {loading} decoding="async">'
    )


# --------------------------------------------------------------------------
# map / directions link builders
# --------------------------------------------------------------------------
def full_address(s):
    return f'{s["street"]}, {s["city"]}, {s["state"]} {s["zip"]}'


def map_embed_src(s):
    q = quote_plus(f'{s["name"]}, {full_address(s)}')
    return f"https://www.google.com/maps?q={q}&z=15&hl=en&output=embed"


def directions_url(s):
    return ("https://www.google.com/maps/dir/?api=1&destination="
            + quote_plus(full_address(s)))


def maps_search_url(s):
    return ("https://www.google.com/maps/search/?api=1&query="
            + quote_plus(f'{s["name"]}, {full_address(s)}'))


# --------------------------------------------------------------------------
# inline SVG icons (no icon font, no external requests)
# --------------------------------------------------------------------------
ICON = {
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 21s7-6.4 7-11a7 7 0 1 0-14 0c0 4.6 7 11 7 11Z"/><circle cx="12" cy="10" r="2.5"/></svg>',
    "info": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><circle cx="12" cy="7.75" r="1" fill="currentColor" stroke="none"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    "zoom": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.3 15.3 21 21"/><path d="M10.5 7.5v6M7.5 10.5h6"/></svg>',
    "instagram": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r="1" fill="currentColor" stroke="none"/></svg>',
    # Hand-drawn "UNCLE MIMI" mark — recreated to match the owner's sketch
    # (block "UNCLE" caps over a zigzag "M I M I" glyph in crayon maroon).
    "logo_mark": (
        '<svg class="brand__mark-svg" viewBox="0 0 190 96" aria-hidden="true">'
        '<text x="95" y="18" text-anchor="middle" font-family="var(--font-body)" '
        'font-weight="700" font-size="16" letter-spacing="3" fill="var(--ink)">UNCLE</text>'
        '<g fill="none" stroke="var(--logo-maroon)" stroke-width="9" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M6,86 L23,41 L34,61 L53,39 L71,87"/>'
        '<path d="M85,42 L85,87"/>'
        '<path d="M101,88 L119,40 L129,62 L148,41 L166,86"/>'
        '<path d="M180,41 L180,88"/>'
        '</g></svg>'
    ),
    # A blue prize rosette (custom vector — no external/copyrighted asset)
    "award_ribbon": (
        '<svg viewBox="0 0 48 64" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
        '<path d="M18 36h6v25l-3-4.2-3 4.2z" fill="#164a86"/>'
        '<path d="M24 36h6v25l-3-4.2-3 4.2z" fill="#1a5aa0"/>'
        '<circle cx="24" cy="24" r="17.5" fill="#1f5fa8"/>'
        '<circle cx="24" cy="24" r="17.5" fill="none" stroke="#15487f" stroke-width="2" stroke-dasharray="2.6 3"/>'
        '<circle cx="24" cy="24" r="13" fill="#2f76c6"/>'
        '<circle cx="24" cy="24" r="13" fill="none" stroke="#ffffff" stroke-width="1.4" opacity="0.9"/>'
        '<path d="M24 15.2l2.34 4.74 5.23.76-3.78 3.69.89 5.21L24 27.4l-4.68 2.46.89-5.21-3.78-3.69 5.23-.76z" fill="#f4c24b"/>'
        '</svg>'
    ),
}


# --------------------------------------------------------------------------
# component renderers
# --------------------------------------------------------------------------
def brand_markup(logo_img):
    """Header brand: the owner's raster logo file if present, else the
    hand-drawn "UNCLE MIMI" mark recreated from the owner's sketch."""
    if logo_img:
        return (
            f'<a class="brand brand--logo" href="#top">'
            f'<img class="brand__img" src="{attr(logo_img["src"])}" '
            f'width="{logo_img["w"]}" height="{logo_img["h"]}" '
            f'alt="Uncle Mimi\'s Kitchen" fetchpriority="high"></a>')
    return (
        '<a class="brand brand--drawn" href="#top" '
        'aria-label="Uncle Mimi\'s Kitchen — home">'
        f'{ICON["logo_mark"]}<small>Kitchen</small></a>')


def render_header(site, logo_img):
    nav_links = "".join(
        f'<li><a href="{attr(n["href"])}" data-spy>{esc(n["label"])}</a></li>'
        for n in site["nav"])
    brand = brand_markup(logo_img)
    cta = site["cta"]
    return f'''<header class="site-header">
    <div class="wrap wrap--wide site-header__inner">
      {brand}
      <nav class="primary-nav" aria-label="Primary">
        <ul>{nav_links}</ul>
      </nav>
      <div class="header-actions">
        <a class="btn btn--primary" href="{attr(cta["href"])}">{esc(cta["label"])}</a>
      </div>
    </div>
  </header>'''


def render_hero(site, hero_img, hero_logo_img):
    cta = site["cta"]
    if hero_logo_img:
        title = (f'<h1 class="hero__title hero__title--logo">'
                  f'<img class="hero__logo" src="{attr(hero_logo_img["src"])}" '
                  f'width="{hero_logo_img["w"]}" height="{hero_logo_img["h"]}" '
                  f'alt="Uncle Mimi\'s Kitchen" fetchpriority="high"></h1>')
    else:
        title = '<h1 class="hero__title">Uncle Mimi\'s Kitchen</h1>'
    return f'''<section class="hero" id="top">
      <div class="hero__media">
        {picture_img(hero_img, "A basket of golden braided challah loaves on a weathered wooden table, with garden greenery behind — freshly baked on Martha's Vineyard.", "100vw", eager=True)}
      </div>
      <div class="wrap wrap--wide hero__inner">
        <div class="hero__content">
          {title}
          <p class="hero__tagline">{esc(site["tagline"])}</p>
          <div class="hero__actions">
            <a class="btn btn--light" href="#products">Explore our products</a>
            <a class="btn btn--outline-light" href="{attr(cta["href"])}">Custom orders</a>
          </div>
        </div>
      </div>
    </section>'''


def render_story(story, sign_img):
    all_paras = [story["lead"]] + story["paragraphs"]
    paras = "".join(f'<p class="story__lead">{esc(p)}</p>' for p in all_paras)
    return f'''<section class="section" id="story" aria-labelledby="story-title">
      <div class="wrap story__grid">
        <div class="story__text" data-reveal>
          <div class="section__head">
            <p class="eyebrow">Our Story</p>
            <h2 class="section__title" id="story-title">Baked with love on the Vineyard</h2>
          </div>
          <div class="story__body">{paras}</div>
        </div>
        <figure class="sign-figure" data-reveal style="transition-delay:120ms">
          <div class="sign-figure__frame">
            {picture_img(sign_img, story["sign"]["alt"], "(min-width: 860px) 44vw, 92vw")}
          </div>
          <figcaption>The original “Uncle Mimi's Restaurant” sign.</figcaption>
        </figure>
      </div>
    </section>'''


def render_products(products, imgs):
    cards = []
    for i, p in enumerate(products):
        img = imgs[p["id"]]
        ribbon = ""
        aw = p.get("award")
        if aw:
            aria = f'{aw["label"]}. {aw["detail"]}.'
            ribbon = (
                f'<span class="ribbon-badge" tabindex="0" role="img" aria-label="{attr(aria)}">'
                f'{ICON["award_ribbon"]}'
                f'<span class="ribbon-badge__tip" role="tooltip">'
                f'<strong>{esc(aw["label"])}</strong>{esc(aw["detail"])}</span>'
                f'</span>')
        tag = f'<span class="tag">{esc(p["tag"])}</span>' if p.get("tag") else ""
        delay = (i % 3) * 90
        cards.append(f'''<article class="product-card" data-reveal style="transition-delay:{delay}ms">
          <div class="product-card__media">
            {ribbon}
            <button type="button" class="product-card__zoom"
                    data-lightbox-src="{attr(img["src"])}" data-lightbox-w="{img["w"]}"
                    data-lightbox-h="{img["h"]}" data-lightbox-alt="{attr(p["image"]["alt"])}"
                    data-lightbox-caption="{attr(p["name"])}"
                    aria-label="View a larger photo of {attr(p["name"])}">
              {picture_img(img, p["image"]["alt"], "(min-width: 860px) 30vw, (min-width: 560px) 45vw, 92vw")}
              <span class="product-card__zoom-icon" aria-hidden="true">{ICON["zoom"]}</span>
            </button>
          </div>
          <div class="product-card__body">
            <h3 class="product-card__name">{esc(p["name"])}</h3>
            <p class="product-card__desc">{esc(p["description"])}</p>
            {tag}
          </div>
        </article>''')
    return f'''<section class="section section--tint" id="products" aria-labelledby="products-title">
      <div class="wrap wrap--wide">
        <div class="section__head" data-reveal>
          <p class="eyebrow">Our Products</p>
          <h2 class="section__title" id="products-title">Fresh from the oven</h2>
          <p class="section__intro">Every item is made in small batches with the highest-quality ingredients.</p>
        </div>
        <div class="product-grid">{"".join(cards)}</div>
      </div>
    </section>'''


def render_team(team, imgs):
    cards = []
    for i, m in enumerate(team["members"]):
        img = imgs[m["id"]]
        bio = "".join(f'<p>{esc(p)}</p>' for p in m["bio"])
        delay = i * 90
        cards.append(f'''<article class="team-card" data-reveal style="transition-delay:{delay}ms">
          <figure class="team-card__media">
            {picture_img(img, m["image"]["alt"], "(min-width: 1080px) 30vw, (min-width: 720px) 45vw, 92vw")}
            <figcaption>{esc(m["caption"])}</figcaption>
          </figure>
          <div class="team-card__body">
            <h3 class="team-card__name">{esc(m["name"])}</h3>
            {bio}
          </div>
        </article>''')
    return f'''<section class="section" id="team" aria-labelledby="team-title">
      <div class="wrap wrap--wide">
        <div class="section__head" data-reveal>
          <p class="eyebrow">{esc(team["eyebrow"])}</p>
          <h2 class="section__title" id="team-title">{esc(team["heading"])}</h2>
        </div>
        <div class="team-grid">{"".join(cards)}</div>
      </div>
    </section>'''


def render_extras(extras):
    classes = extras["classes"]
    catering = extras["catering"]
    classes_paras = "".join(f'<p>{esc(p)}</p>' for p in classes["paragraphs"])
    catering_paras = "".join(f'<p>{esc(p)}</p>' for p in catering["paragraphs"])
    return f'''<section class="section section--tint" id="extras" aria-labelledby="extras-title">
      <div class="wrap">
        <div class="contact__grid">
          <div class="contact__card" data-reveal>
            <div class="section__head" style="margin-bottom:var(--space-md)">
              <p class="eyebrow">{esc(classes["eyebrow"])}</p>
              <h2 class="section__title" id="extras-title">{esc(classes["heading"])}</h2>
            </div>
            {classes_paras}
          </div>
          <div class="contact__card" data-reveal style="transition-delay:120ms">
            <p class="eyebrow">{esc(catering["eyebrow"])}</p>
            <h3>{esc(catering["heading"])}</h3>
            {catering_paras}
          </div>
        </div>
      </div>
    </section>'''


def instagram_handle(url):
    return "@" + url.rstrip("/").rsplit("/", 1)[-1]


def instagram_contact(site):
    ig = site.get("instagram")
    if not ig:
        return ""
    return (
        f'<a class="contact-method" href="{attr(ig)}" target="_blank" rel="noopener">'
        f'<span class="contact-method__icon">{ICON["instagram"]}</span>'
        f'<span><span class="contact-method__label">Follow along</span>'
        f'<span class="contact-method__value">{esc(instagram_handle(ig))}</span></span></a>')


def render_contact(site):
    return f'''<section class="section" id="contact" aria-labelledby="contact-title">
      <div class="wrap">
        <div class="contact__grid">
          <div class="contact__card" data-reveal>
            <div class="section__head" style="margin-bottom:var(--space-md)">
              <p class="eyebrow">Inquiries &amp; Custom Orders</p>
              <h2 class="section__title" id="contact-title">Let's bake something special</h2>
            </div>
            <p>Planning a Shabbat dinner, a celebration, or a standing order for your café?
               Reach out and Tammy will help put together exactly what you need.</p>
            <div class="contact-methods">
              <a class="contact-method" href="mailto:{attr(site["email"])}">
                <span class="contact-method__icon">{ICON["mail"]}</span>
                <span><span class="contact-method__label">Email us</span>
                  <span class="contact-method__value">{esc(site["email"])}</span></span>
              </a>
              {instagram_contact(site)}
            </div>
          </div>
          <div class="contact__card" data-reveal style="transition-delay:120ms">
            <h3>A note on ordering</h3>
            <p>Uncle Mimi's is a small-batch kitchen on Martha's Vineyard. Custom orders are
               arranged directly by email — there's no online checkout, so you'll always
               talk to a real person about quantities, timing, and pickup or delivery.</p>
            <p>You can also find our baked goods on shelves at three island stores — see
               <a href="#locations">Where to Find Us</a>.</p>
          </div>
        </div>
      </div>
    </section>'''


def render_locations(loc, imgs):
    cards = []
    for i, s in enumerate(loc["stores"]):
        img = imgs[s["id"]]
        delay = i * 90
        cards.append(f'''<article class="location-card" data-reveal style="transition-delay:{delay}ms">
          <div class="location-card__media">
            {picture_img(img, s["image"]["alt"], "(min-width: 1080px) 30vw, (min-width: 720px) 45vw, 92vw")}
          </div>
          <div class="location-card__body">
            <h3 class="location-card__name">{esc(s["name"])}</h3>
            <address>
              {esc(s["street"])}<br>{esc(s["city"])}, {esc(s["state"])} {esc(s["zip"])}<br>
              <a class="location-card__phone" href="tel:{attr(s["phone"])}">{esc(s["phoneDisplay"])}</a>
            </address>
            <div class="map-embed">
              <div class="map-embed__fallback">
                <span>Map preview unavailable.</span>
                <a href="{attr(maps_search_url(s))}" target="_blank" rel="noopener">Open in Google Maps</a>
              </div>
              <iframe src="{attr(map_embed_src(s))}" title="Map showing {attr(s["name"])}, {attr(full_address(s))}"
                      loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
            </div>
            <div class="location-card__actions">
              <a class="btn btn--ghost" href="{attr(directions_url(s))}" target="_blank" rel="noopener">Get directions</a>
              <a class="btn btn--ghost" href="{attr(maps_search_url(s))}" target="_blank" rel="noopener">Open in Google Maps</a>
            </div>
          </div>
        </article>''')
    return f'''<section class="section section--tint" id="locations" aria-labelledby="locations-title">
      <div class="wrap wrap--wide">
        <div class="section__head" data-reveal>
          <p class="eyebrow">Where to Find Us on Island</p>
          <h2 class="section__title" id="locations-title">Find us across Martha's Vineyard</h2>
        </div>
        <p class="locations-note">{ICON["info"]}<span>{esc(loc["note"])}</span></p>
        <div class="location-grid">{"".join(cards)}</div>
      </div>
    </section>'''


def render_footer(site, logo_img, year):
    nav = "".join(f'<li><a href="{attr(n["href"])}">{esc(n["label"])}</a></li>'
                  for n in site["nav"])
    insta = ""
    if site.get("instagram"):
        insta = (f'<li><a class="footer__social" href="{attr(site["instagram"])}" '
                 f'target="_blank" rel="noopener">{ICON["instagram"]}'
                 f'<span>{esc(instagram_handle(site["instagram"]))}</span></a></li>')
    footer_logo = ""
    if logo_img:
        footer_logo = (
            f'<div class="footer__logo">'
            f'<img src="{attr(logo_img["src"])}" width="{logo_img["w"]}" '
            f'height="{logo_img["h"]}" alt="" loading="lazy"></div>')
    return f'''<footer class="site-footer">
      <div class="wrap wrap--wide">
        <div class="footer-grid">
          <div class="footer__about">
            {footer_logo}
            <p class="footer__brand">Uncle <span class="brand__mark">Mimi's</span> Kitchen</p>
            <p class="footer__tag">Small-batch artisan baking on Martha's Vineyard, Massachusetts.</p>
          </div>
          <nav class="footer-col" aria-label="Footer">
            <h2>Explore</h2>
            <ul>{nav}</ul>
          </nav>
          <div class="footer-col">
            <h2>Get in touch</h2>
            <ul>
              <li><a href="mailto:{attr(site["email"])}">{esc(site["email"])}</a></li>
              {insta}
            </ul>
          </div>
        </div>
        <div class="footer__bottom">
          <span>&copy; {year} Uncle Mimi's Kitchen. All rights reserved.</span>
          <span>Martha's Vineyard, MA</span>
        </div>
      </div>
    </footer>'''


def json_ld(site, products):
    offers = [{
        "@type": "Offer",
        "itemOffered": {"@type": "Product", "name": p["name"], "description": p["description"]},
        "availability": "https://schema.org/LimitedAvailability",
    } for p in products]
    data = {
        "@context": "https://schema.org",
        "@type": "Bakery",
        "name": site["name"],
        "description": site["metaDescription"],
        "url": site["url"],
        "image": site["url"] + site["ogImage"],
        "email": site["email"],
        "areaServed": {"@type": "Place", "name": "Martha's Vineyard, Massachusetts"},
        "makesOffer": offers,
    }
    if site.get("instagram"):
        data["sameAs"] = [site["instagram"]]
    return json.dumps(data, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------
# page assembly
# --------------------------------------------------------------------------
def render_page(site, story, products, locations, team, extras, imgs, hero_img,
                sign_img, logo_img, hero_logo_img, year):
    head = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Uncle Mimi's Kitchen — Artisan Bakery on Martha's Vineyard</title>
  <meta name="description" content="{attr(site["metaDescription"])}">
  <link rel="canonical" href="{attr(site["url"])}">
  <meta name="theme-color" content="#f5f8f4">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Uncle Mimi's Kitchen">
  <meta property="og:title" content="Uncle Mimi's Kitchen — Artisan Bakery on Martha's Vineyard">
  <meta property="og:description" content="{attr(site["metaDescription"])}">
  <meta property="og:url" content="{attr(site["url"])}">
  <meta property="og:image" content="{attr(site["url"] + site["ogImage"])}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="A basket of golden braided challah from Uncle Mimi's Kitchen.">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Uncle Mimi's Kitchen — Artisan Bakery on Martha's Vineyard">
  <meta name="twitter:description" content="{attr(site["tagline"])}">
  <meta name="twitter:image" content="{attr(site["url"] + site["ogImage"])}">

  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="assets/favicon.ico" sizes="32x32">
  <link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
  <link rel="manifest" href="site.webmanifest">

  <link rel="preload" href="assets/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="assets/fonts/fraunces-var.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" as="image" href="{attr(hero_img["src"])}" imagesrcset="{attr(hero_img["srcset"])}" imagesizes="100vw" fetchpriority="high">
  <link rel="stylesheet" href="assets/main.css">

  <script type="application/ld+json">
{json_ld(site, products)}
  </script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
{render_header(site, logo_img)}
  <main id="main">
{render_hero(site, hero_img, hero_logo_img)}
{render_story(story, sign_img)}
{render_products(products, imgs["products"])}
{render_team(team, imgs["team"])}
{render_extras(extras)}
{render_contact(site)}
{render_locations(locations, imgs["locations"])}
  </main>
{render_footer(site, logo_img, year)}
  <div class="lightbox" id="lightbox">
    <div class="lightbox__scrim" data-close></div>
    <div class="lightbox__dialog" role="dialog" aria-modal="true" aria-label="Enlarged photo">
      <button class="lightbox__close" type="button" aria-label="Close">&times;</button>
      <img class="lightbox__img" src="" alt="" loading="eager">
      <p class="lightbox__caption"></p>
    </div>
  </div>
  <script src="assets/menu.js" defer></script>
</body>
</html>'''
    return head


# --------------------------------------------------------------------------
# favicons, OG image, static files
# --------------------------------------------------------------------------
FAVICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Uncle Mimi's Kitchen">
  <rect width="64" height="64" rx="14" fill="#2c5f47"/>
  <path d="M14,42 L24,20 L32,30 L40,20 L50,42" fill="none" stroke="#fdf1e3"
        stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

WEBMANIFEST = {
    "name": "Uncle Mimi's Kitchen",
    "short_name": "Uncle Mimi's",
    "description": "Small-batch artisan bakery on Martha's Vineyard.",
    "start_url": "./",
    "display": "browser",
    "background_color": "#f5f8f4",
    "theme_color": "#f5f8f4",
    "icons": [
        {"src": "assets/favicon.svg", "sizes": "any", "type": "image/svg+xml"},
        {"src": "assets/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
    ],
}


def read_png_rgba(path):
    """Minimal PNG decoder (8-bit RGB or RGBA, non-interlaced) -> (w, h, rgba bytes)."""
    import zlib
    with open(path, "rb") as f:
        data = f.read()
    pos = 8
    width = height = colortype = None
    idat = b""
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            width, height, _, colortype = struct.unpack(">IIBB", chunk[:10])
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
        pos += 8 + length + 4
    raw = zlib.decompress(idat)
    channels = {2: 3, 6: 4}[colortype]
    stride = width * channels
    out = bytearray(height * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        ftype = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        for x in range(stride):
            a = line[x - channels] if x >= channels else 0
            b = prev[x]
            c = prev[x - channels] if x >= channels else 0
            if ftype == 1: line[x] = (line[x] + a) & 0xFF
            elif ftype == 2: line[x] = (line[x] + b) & 0xFF
            elif ftype == 3: line[x] = (line[x] + (a + b) // 2) & 0xFF
            elif ftype == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    if channels == 3:
        rgba = bytearray(width * height * 4)
        for i in range(width * height):
            rgba[i*4:i*4+3] = out[i*3:i*3+3]
            rgba[i*4+3] = 255
        out = rgba
    return width, height, bytes(out)


def write_png_rgb(path, width, height, rgb):
    import zlib
    def chunk(ctype, cdata):
        c = ctype + cdata
        return struct.pack(">I", len(cdata)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    with open(path, "wb") as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", b""))


def composite_logo_icon(logo_path, out_path, canvas=512, bg=(245, 248, 244)):
    """Center the real logo (alpha-composited) onto a solid square, for
    favicons/app icons — keeps the browser-tab icon consistent with the
    actual header logo instead of an unrelated cropped photo."""
    resized = out_path + "._tmp.png"
    sips("--resampleWidth", str(int(canvas * 0.74)), "-s", "format", "png",
         logo_path, "--out", resized)
    lw, lh, lrgba = read_png_rgba(resized)
    os.remove(resized)
    ox, oy = (canvas - lw) // 2, (canvas - lh) // 2
    rgb = bytearray(bg * (canvas * canvas))
    for y in range(lh):
        for x in range(lw):
            si = (y * lw + x) * 4
            r, g, b, a = lrgba[si], lrgba[si+1], lrgba[si+2], lrgba[si+3]
            if a == 0:
                continue
            dx, dy = ox + x, oy + y
            if not (0 <= dx < canvas and 0 <= dy < canvas):
                continue
            di = (dy * canvas + dx) * 3
            af = a / 255.0
            rgb[di]   = int(r * af + rgb[di]   * (1 - af))
            rgb[di+1] = int(g * af + rgb[di+1] * (1 - af))
            rgb[di+2] = int(b * af + rgb[di+2] * (1 - af))
    write_png_rgb(out_path, canvas, canvas, bytes(rgb))


def png_to_ico(png_path, ico_path, size):
    """Wrap a PNG as a single-image .ico (ICO permits PNG-encoded entries)."""
    with open(png_path, "rb") as f:
        png = f.read()
    dim = 0 if size >= 256 else size
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), 22)
    with open(ico_path, "wb") as f:
        f.write(header + entry + png)


def build_favicons_and_og(site):
    assets = os.path.join(DIST, "assets")
    ensure_dir(assets)
    # SVG favicon
    with open(os.path.join(assets, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(FAVICON_SVG)

    # Raster fallbacks (apple-touch-icon, favicon.ico/png) — built from the
    # SAME brand mark as the SVG favicon and header logo, not an arbitrary
    # product photo, so the browser tab / iOS home screen icon matches the
    # rest of the site's identity.
    logo_src = os.path.join(PUBLIC, site.get("logo", ""))
    tmp = os.path.join(assets, "_iconbase.png")
    if site.get("logo") and os.path.exists(logo_src):
        composite_logo_icon(logo_src, tmp, canvas=512, bg=(245, 248, 244))
    else:
        # No owner logo file yet: fall back to a plain brand-green square
        # bearing the same zig-zag mark used in favicon.svg.
        w = h = 512
        write_png_rgb(tmp, w, h, bytes((44, 95, 71) * (w * h)))
    sips("--resampleWidth", "180", tmp, "--out", os.path.join(assets, "apple-touch-icon.png"))
    fav32 = os.path.join(assets, "favicon-32.png")
    sips("--resampleWidth", "32", tmp, "--out", fav32)
    sips("--resampleWidth", "16", tmp, "--out", os.path.join(assets, "favicon-16.png"))
    png_to_ico(fav32, os.path.join(assets, "favicon.ico"), 32)
    os.remove(tmp)

    # OG image 1200x630 from the hero challah basket
    og_dir = os.path.join(DIST, "assets/og")
    ensure_dir(og_dir)
    hero = os.path.join(PUBLIC, "assets/images/hero/challah-basket-hero.jpg")
    og_tmp = os.path.join(og_dir, "_ogtmp.jpg")
    sips("--resampleWidth", "1200", "-s", "format", "jpeg", "-s", "formatOptions",
         "80", hero, "--out", og_tmp)
    sips("-c", "630", "1200", og_tmp, "--out", os.path.join(og_dir, "uncle-mimis-og.jpg"))
    os.remove(og_tmp)


def copy_static():
    assets = os.path.join(DIST, "assets")
    ensure_dir(assets)
    shutil.copy(os.path.join(SRC, "styles/main.css"), os.path.join(assets, "main.css"))
    shutil.copy(os.path.join(SRC, "scripts/menu.js"), os.path.join(assets, "menu.js"))
    shutil.copytree(os.path.join(PUBLIC, "assets/fonts"),
                    os.path.join(assets, "fonts"), dirs_exist_ok=True)


def write_seo_files(site, year):
    with open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: " + site["url"] + "sitemap.xml\n")
    lastmod = date.today().isoformat()
    with open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                f'  <url>\n    <loc>{site["url"]}</loc>\n'
                f'    <lastmod>{lastmod}</lastmod>\n'
                '    <changefreq>monthly</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
                '</urlset>\n')
    with open(os.path.join(DIST, "site.webmanifest"), "w", encoding="utf-8") as f:
        json.dump(WEBMANIFEST, f, ensure_ascii=False, indent=2)
    # GitHub Pages custom-domain file — derived from site.json so it can
    # never silently disappear on a rebuild (dist/ is wiped every build).
    hostname = urlparse(site["url"]).hostname
    if hostname:
        with open(os.path.join(DIST, "CNAME"), "w", encoding="utf-8") as f:
            f.write(hostname + "\n")


def write_asset_manifest():
    with open(os.path.join(ROOT, "asset-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(MANIFEST, f, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    site = load("site.json")
    story = load("story.json")
    products = load("products.json")
    locations = load("locations.json")
    team = load("team.json")
    extras = load("extras.json")

    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    ensure_dir(DIST)

    print("• generating responsive images …")
    hero_img = make_image("assets/images/hero/challah-basket-hero.jpg",
                          [800, 1200, 1600, 2000], "hero", "Challah basket hero")
    sign_img = make_image(story["sign"]["src"], [640, 1000, 1062], "story",
                          story["sign"]["alt"])
    product_imgs = {
        p["id"]: make_image(p["image"]["src"], [400, 600, 800, 1100], "products",
                            p["image"]["alt"])
        for p in products
    }
    location_imgs = {
        s["id"]: make_image(s["image"]["src"], [420, 700, 900], "locations",
                            s["image"]["alt"])
        for s in locations["stores"]
    }
    team_imgs = {
        m["id"]: make_image(m["image"]["src"], [400, 600, 800], "team",
                            m["image"]["alt"])
        for m in team["members"]
    }
    imgs = {"products": product_imgs, "locations": location_imgs, "team": team_imgs}

    logo_img = make_logo(site)
    hero_logo_img = make_hero_logo(site)
    print("• logo:", "using owner file" if logo_img else "wordmark fallback (no logo file yet)")

    print("• favicons + social image …")
    build_favicons_and_og(site)

    print("• static assets (css/js/fonts) …")
    copy_static()

    year = date.today().year
    print("• rendering index.html …")
    page = render_page(site, story, products, locations, team, extras, imgs,
                       hero_img, sign_img, logo_img, hero_logo_img, year)
    with open(os.path.join(DIST, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)

    print("• seo files + manifest …")
    write_seo_files(site, year)
    write_asset_manifest()
    print("✓ build complete →", DIST)


if __name__ == "__main__":
    main()
