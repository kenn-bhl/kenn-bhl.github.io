# J-Studio site

Static GitHub Pages site (plain HTML + `assets/css/style.css`, small vanilla scripts in `assets/js/`). No build step on the server, no API calls. All links relative so the site can move to a custom domain. Helper scripts live in `_tools/` (not published).

## App list database: `_data/apps.json`

`_data/apps.json` is the source of truth for the app list. The HTML stays static: when the JSON changes, an agent updates the HTML by hand to match. Nothing reads the JSON at runtime. The `_` prefix keeps the folder off the published site.

Fields per app:
- `id`: slug for the app (e.g. `1000-words`). Never change it once published.
- `group`: `Education` → shown in the app grid ("Education apps"); `Life` → shown in "Find something that fits your life." and the footer "Lifestyle" column.
- `name`, `shortDescription`: English, natural and correct (polish user-supplied copy, and write the fix back to the JSON).
- `age`: label on the top-left of the grid card image (`<span class="img-label tl">`), e.g. `Ages 4–6`, `All ages`, `18+`.
- `landing` (optional): path of the app's landing page, e.g. `1000-words/`. When set, the card's logo, main image and name (and the footer link) point to it; only the name link is keyboard-focusable (`tabindex="-1" aria-hidden="true"` on the image links). Without it, cards have no links and the app is left out of the footer.
- `logo`: square icon (512×512 is fine). `main`: main image, 3:2. Paths are relative to the site root (e.g. `1000-words/logo.png`) or full URLs.
- `appStoreUrl`, `googlePlayUrl`:
  - a URL → store button linking there. Apple URLs may contain `{locale}`; drop that segment (`apps.apple.com/app/...` redirects to the visitor's storefront).
  - `"coming_soon"` → disabled button with that store's icon + "Coming soon".
  - `""` → no button for that store.
- `position`: sort order within its group, ascending (lower number first). Apps without one go last; ties keep JSON order. Leave gaps (100, 200, …) so new apps can slot in between.
- `special_available` (optional): region code where the app is exclusively available (e.g. `vi` → "Only available in Vietnam"), shown as a label on the top-right of the main image (`<span class="img-label tr">Only available in Vietnam</span>`).
- If an app ends up with no buttons and no note, show a single generic "Coming soon" button.
- The App Store and Google Play buttons always appear together, everywhere (cards and landing pages), even when both are "coming soon".

## Syncing JSON → `index.html`

Apps are split by `group`, sorted by `position` within each:
1. **App grid** (`<div class="app-grid" id="education">`): one `<article class="app-card">` per `Education` app.
2. **"Find something that fits your life."** (`<div class="story-row" id="lifestyle">`): one `<article class="story">` per `Life` app.
3. **Footer** columns "Education" and "Lifestyle", on every page: one link per app that has a `landing` page; apps without one are left out.

Rules:
- Copy the markup of an existing card exactly; change only the data.
- Store buttons use one shared markup and CSS (`.stores`) in both places: App Store = `btn-inverse`, Google Play = `btn-tertiary`, each with its SVG from `assets/img/`. Coming soon = `<span class="btn btn-tertiary is-soon" aria-disabled="true">`.
- External store links: add `target="_blank" rel="noopener"`.
- After editing, check the HTML tags still balance.

## App landing pages
Every app landing page copies `1000-words/index.html` exactly: same sections, same markup, same CSS. Do not add or remove sections; only change text, images, store buttons and links. Sections and their images (paths relative to the app folder):
1. Hero: `logo.png`, headline, subtitle, store buttons, `landing_1.png` (about 2400×1100).
2. Quote + "How do … learn?" promo (grey): two reels of 5 images each, `section2/*.webp` at 1000×600 (5:3).
3. "Inside the app." cards (white, shared ticker): 5 cards, `app-functions/*.png` at about 1402×1122 (5:4); cards 1 and 4 are `dark`. A "Privacy policy" button below.
After adding a page, set `landing` in `_data/apps.json` and resync the home page and every page footer.

Always build the app's `privacy.html` together with its landing page, without asking: copy the layout of `1000-words/privacy.html` (legal head with app logo, "On this page" list, `legal-body`). If the app already has a policy, keep its text word for word; otherwise write one from what the app's code actually does (local storage, network calls, ads SDK, permissions).

Each app has its own folder named after its image folder (e.g. `1000-words/`): `index.html` is the landing page (URL `/1000-words/`) and `privacy.html` is the privacy policy. Landing pages reuse the home header, hero and footer markup, with every link and asset path prefixed `../` (the app's own images use `logo.png`, `main.png`). In the footer, the current app's link points to `./` (with `aria-current="page"` on its landing page).

## Shared ticker (`assets/js/ticker.js`)

Auto-scrolling rows (home "We're parents too" screenshots, landing "Inside the app" cards) use `<div data-ticker><track>items</track></div>` plus the script. Write each item once: the script clones them only when they overflow the screen, sets the loop speed (`data-speed`, px/s, default 50), and leaves a static, centred row when they fit or the visitor prefers reduced motion.

## Same-page links (`assets/js/anchors.js`)

Every page loads `anchors.js`. Links to a section on the same page (`href="#id"`) scroll smoothly without adding `#id` to the URL, and a hash in the URL on arrival (e.g. `../#education`) is removed after the jump. `#top` scrolls to the top of the page.

## Languages (`vi/`, `ja/`, …)

English pages are the source. Each translated page mirrors an English page at the same path under its language folder (`vi/index.html`, `ja/j-kids/index.html`, `de/j-kids/privacy.html`, …) and is generated, never edited by hand:

```
python3 _tools/sync_apps.py    # after changing _data/apps.json (home cards + every footer)
python3 _tools/build_i18n.py   # after changing any English page, a translation, or a languages list
```

Which languages a page exists in:
- `index.html`: `languages` in `_data/site.json`.
- `contact.html` (shared by every app): every language in `site.json` plus every app's `languages`, so adding a language to an app also needs the contact strings in that language's `_tools/i18n/<lang>.json`.
- An app's `index.html` and `privacy.html`: `languages` of that app in `_data/apps.json` (each app supports its own set; missing → the site languages). English always exists.

Rules the build applies:
- Text is translated with `_tools/i18n/<lang>.json` (exact English string, whitespace collapsed → translation; keep `&amp;` escaped). The build lists every string without a translation per language: add it (natural wording for that language) and rerun. App names follow the store listing of that language.
- A page link points at the same language when the target page exists in it; otherwise at the English page, marked `hreflang="en"`. Images/CSS/JS point back to the shared files.
- The header language dropdown (`<details class="lang-menu">` after the Contact link in `.nav-right`, current language marked `aria-current`, names written in their own language) lists only the languages that page exists in. `assets/js/lang-menu.js` closes it on an outside click or Escape. Never write the menu by hand.
- Translated pages whose English page or language was removed are deleted.
- A new language code must be added to `LANG_NAMES` and `LANG_WORD` in `build_i18n.py`.
