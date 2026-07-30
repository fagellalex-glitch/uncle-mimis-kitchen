# Unresolved Items — Owner Input Needed

None of these block the site from working; each is a place where I avoided
guessing. All are quick to resolve.

### 1. Final domain name  🔧 *edit `src/data/site.json` → `"url"`*
I used `https://unclemimiskitchen.com/` as a **placeholder** canonical URL (the
original lives at `unclemimi.weebly.com`, which shouldn't be the canonical for a
migrated site). Set the real domain, then rebuild — it feeds the canonical link,
Open Graph tags, `sitemap.xml`, and structured data.

### 2. Brand logo — resolved ✅
The original Weebly header artwork (`published/untitled-artwork.jpg`) 404'd, and
your hand‑drawn "UNCLE MIMI" wordmark first reached me only as a pasted‑image
preview (no retrievable file). Once you saved it to your Desktop
(`IMG_9882.png`), I located it, precisely cropped the largest of your three
sketched variants directly from its real pixels, made the background
transparent, and installed it at
`public/assets/images/brand/uncle-mimi-logo.png`. The header now shows **your
exact original drawing** — not a recreation. The build automatically prefers
this file whenever it's present; delete it to fall back to the typographic
wordmark.

### 3. Availability note — please confirm wording  🔧 *`src/data/locations.json` → `"note"`*
The original site made no statement about stock. To avoid implying items are
always available, I added a neutral line:
> "Uncle Mimi's baked goods are made in small batches and delivered fresh, so the
> selection at each store varies by day and season. To be sure of a specific
> item, call the store or reach out to us before you visit."
Confirm this is accurate, or reword/remove it.

### 4. Email address — resolved ✅
The original site's address (`orders@thesloans.net`, decoded from Cloudflare
obfuscation) has been replaced with `unclemimiskitchen@gmail.com` at the
owner's request.

### 5. Instagram — added, please verify the account
No social links existed on the original Weebly site. You provided
`instagram.com/unclemimiskitchen` directly, so it's now live in the footer and
the "Inquiries" contact card, and listed in the `Bakery` structured data
(`sameAs`). Please confirm this is the correct, currently‑active account before
launch — I did not independently verify ownership.

### 6. Map pins — spot‑check
Embeds and directions use each store's **exact street address** (and the
original's coordinates are preserved in the JSON as `lat`/`lng`). Open each map
once to confirm the pin lands on the right storefront.

### 7. Modern image formats (optional)
The build emits optimized responsive **JPEG** (no WebP/AVIF encoder was available
here). Adding WebP/AVIF would trim payload further — see README →
"Adding WebP/AVIF". Not required; JPEGs are already optimized and lazy‑loaded.

### 8. Blue ribbon icon — custom vector, not a scan of an actual fair ribbon
The Focaccia card now shows a blue prize‑rosette icon (hover/tap reveals "Blue
Ribbon Winner — First place, professional yeast bread, Martha's Vineyard
Agricultural Fair"). I drew this as a simple original SVG rather than sourcing a
photo of a real ribbon online, since a scraped image would carry unknown
copyright/licensing and wouldn't match the site's crisp, scalable graphics. If
you have a photo of the actual award ribbon Uncle Mimi's won, send it and I can
swap it in.

### 9. Naming nuance (informational)
Your site lists **"North Tisbury Farm Stand"** (preserved as‑is), while the store's
own sign in the photo reads **"North Tisbury Farm & Market."** The alt text
describes the sign accurately; the business name follows your original copy. Let
me know if you'd prefer the site use the store's current name.
