# Content Migration Checklist

Side‑by‑side verification against the original Weebly site
(`https://unclemimi.weebly.com/`). Every original section, image, location, and
contact method is accounted for. An automated check confirms all 34 original
copy strings are present verbatim in the built `dist/index.html`.

## Text sections

| Original content | New location | Status |
|---|---|---|
| Site name "Uncle Mimi's Kitchen" | Header wordmark, hero `<h1>`, footer, `<title>` | ✅ Preserved |
| Tagline "Artisan baked goods made fresh on Martha's Vineyard." | Hero subtitle | ✅ Preserved |
| "Our Story" — chef/baker + small‑batch paragraph | `#story` lead + body | ✅ Preserved |
| "Our Story" — the "Mimi" name origin | `#story` body | ✅ Preserved |
| "Uncle Mimi's Restaurant" sign explanation | `#story` + sign figure caption | ✅ Preserved |
| Blue Ribbon Challah name + description | `#products` card | ✅ Preserved (ribbon badge added later — see below) |
| Focaccia name + blue‑ribbon award description | `#products` card + ribbon badge | ✅ Preserved |
| Granola name + description | `#products` card + "Vegan" tag | ✅ Preserved |
| Cranberry Orange Scones name + description | `#products` card | ✅ Preserved |
| Cinnamon Brown Sugar Coffee Cake name + description | `#products` card | ✅ Preserved |
| Delicious Apple Cake name + description | `#products` card | ✅ Preserved |
| "Inquiries & Custom Orders" heading | `#contact` eyebrow | ✅ Preserved |
| Email `orders@thesloans.net` | `#contact` + footer (`mailto:`) | ✅ Preserved (decoded from Cloudflare obfuscation) |
| Phone (917) 567‑5134 | `#contact` + footer (`tel:`) | ✅ Preserved |
| "where to find us on island" heading | `#locations` eyebrow | ✅ Preserved |
| "Contact & Location" section | Merged into `#contact` + `#locations` | ✅ Preserved |

## Retail locations

| Store | Address | Phone | Map | Status |
|---|---|---|---|---|
| Chilmark General Store | 7 State Road, Chilmark, MA 02535 | (508) 645‑3739 | Embed + directions from address (orig. coords 41.3420, −70.7450) | ✅ |
| Katama General Store | 170 Katama Road, Edgartown, MA 02539 | (508) 627‑5071 | Embed + directions from address (orig. coords 41.3818, −70.5177) | ✅ |
| North Tisbury Farm Stand | 632 State Rd, West Tisbury, MA 02575 | (508) 696‑4664 | Embed + directions from address (orig. coords 41.4073, −70.6735) | ✅ |

## Images

All 11 in‑use photographs migrated and stored locally with descriptive names and
accurate alt text — see [`ASSET-MANIFEST.md`](ASSET-MANIFEST.md). Two Weebly
theme stock backgrounds were intentionally omitted; one brand artwork file 404'd
at the source (documented in `UNRESOLVED.md`).

## Contact links — functional

- ✅ `mailto:orders@thesloans.net`
- ✅ `tel:+19175675134` (bakery)
- ✅ `tel:+15086453739`, `tel:+15086275071`, `tel:+15086964664` (stores)
- ✅ Google Maps "Get directions" + "Open in Google Maps" per store
- ✅ Keyless Google Maps embed per store, lazy‑loaded, with titled iframes and a
  visible fallback link if the embed cannot load.

## Intentional changes (copyedits only — no factual claims altered)

| Original | New | Type |
|---|---|---|
| "small batch, artisanal" | "small‑batch, artisanal" | Hyphenation |
| "highest quality ingredients" | "highest‑quality ingredients" | Hyphenation |
| "origins…." | "origins." | Punctuation cleanup |
| Straight quotes around Mimi / restaurant | Curly quotes | Typography |
| (added) availability note in Locations | New sentence | **Added** — see `UNRESOLVED.md` #4 |
| (added) "Blue Ribbon Winner — 1st place, MV Agricultural Fair" badge on Challah, Scones, Coffee Cake, and Apple Cake | New badge + tooltip | **Added, owner‑provided** — the original site only documented this award for Focaccia. The other four were added at the owner's explicit direction in a later session, not migrated from the original site or inferred by the builder. Instagram (`@unclemimiskitchen`) was added the same way. |

## Not present on the original — therefore **not** invented

Prices · ingredient lists · allergen/dietary claims (beyond the existing "vegan"
granola line) · business hours · shipping/delivery options · online ordering ·
testimonials/ratings · a bakery street address. (Awards beyond the original
focaccia claim were later added at the owner's explicit direction — see row
above — not invented by the builder.)
