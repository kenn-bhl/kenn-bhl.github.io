#!/usr/bin/env python3
"""Build the translated site (vi/, ja/, …) from the English pages, and write the
header language dropdown on every page.

    python3 _tools/build_i18n.py

Which languages each page exists in:
- index.html, contact.html: `languages` in _data/site.json.
- <app>/index.html, <app>/privacy.html: `languages` of the app in _data/apps.json
  whose `landing` is that folder (falls back to the site languages).
English ("en") is always the source and always exists.

For each page and each of its languages (except en) it writes <lang>/<same path>:
- text translated with _tools/i18n/<lang>.json (exact English string → translation),
- html lang set, page links pointing at the same language when the target page
  exists in it, otherwise at the English page (marked hreflang="en"),
- images/CSS/JS pointing back to the shared files.
The dropdown on a page lists only the languages that page exists in.
Strings with no translation are listed at the end; add them to the JSON and rerun.
"""
import glob
import json
import os
import posixpath
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..'))
I18N_DIR = os.path.join(ROOT, '_tools', 'i18n')

# Name of each language in its own language, and the html lang attribute.
LANG_NAMES = {
    'en': 'English', 'vi': 'Tiếng Việt', 'fr': 'Français', 'da': 'Dansk', 'es': 'Español',
    'pt': 'Português', 'de': 'Deutsch', 'zh': '简体中文', 'ja': '日本語', 'ko': '한국어',
    'id': 'Bahasa Indonesia',
}
HTML_LANG = {'zh': 'zh-Hans'}
LANG_WORD = {
    'en': 'Language', 'vi': 'Ngôn ngữ', 'fr': 'Langue', 'da': 'Sprog', 'es': 'Idioma',
    'pt': 'Idioma', 'de': 'Sprache', 'zh': '语言', 'ja': '言語', 'ko': '언어', 'id': 'Bahasa',
}
ORDER = list(LANG_NAMES)

# Text that is the same in every language (names, brands, contact details).
KEEP = {'J-Studio', 'App Store', 'Google Play', 'J-Kids', '1000 Words', 'New Word Learning',
        'Daily Task', 'Lấy số Vietlott', 'Subsum', 'kenn.bhl@gmail.com', '+84 856 011 093',
        'Android:', 'Bui Trung Kien'} | set(LANG_NAMES.values())

GLOBE = ('<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="8" cy="8" r="6.25" stroke="currentColor" stroke-width="1.3"/>'
         '<path d="M1.75 8h12.5M8 1.75c1.7 1.8 2.5 3.9 2.5 6.25S9.7 12.45 8 14.25C6.3 12.45 5.5 10.35 5.5 8S6.3 3.55 8 1.75Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>')
CHEVRON = ('<svg class="chev" viewBox="0 0 16 16" fill="none" aria-hidden="true">'
           '<path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
MENU_RE = r'\n\s*<details class="lang-menu".*?</details>'
SCRIPT_RE = r'\n\s*<script src="[^"]*lang-menu\.js"[^>]*></script>'
OLD_FOOTER_RE = r'\n\s*<nav class="lang-switch".*?</nav>'


# ---------- Which languages a page exists in ----------

def load_json(path):
    return json.load(open(os.path.join(ROOT, path), encoding='utf-8'))


SITE_LANGS = load_json('_data/site.json')['languages']
APP_LANGS = {}
for _app in load_json('_data/apps.json')['apps']:
    if _app.get('landing'):
        APP_LANGS[_app['landing'].strip('/')] = _app.get('languages') or SITE_LANGS


def sort_langs(langs):
    langs = set(langs) | {'en'}
    unknown = langs - set(LANG_NAMES)
    if unknown:
        raise SystemExit(f'unknown language code(s): {sorted(unknown)} (add them to LANG_NAMES)')
    return [c for c in ORDER if c in langs]


def page_langs(en_path):
    """Languages the English page en_path (root-relative file path) exists in."""
    if en_path in ('index.html', 'contact.html'):
        return sort_langs(SITE_LANGS)
    folder = en_path.split('/')[0] if '/' in en_path else None
    if folder in APP_LANGS:
        return sort_langs(APP_LANGS[folder])
    return ['en']


def english_pages():
    pages = ['index.html', 'contact.html']
    pages += sorted(glob.glob('*/index.html', root_dir=ROOT) + glob.glob('*/privacy.html', root_dir=ROOT))
    return [p for p in pages if not p.split('/')[0] in LANG_NAMES and not p.startswith('_')
            and os.path.exists(os.path.join(ROOT, p))]


def out_path(en_path, lang):
    return en_path if lang == 'en' else f'{lang}/{en_path}'


# ---------- Links ----------

def page_url(path):
    """'j-kids/index.html' -> 'j-kids/', 'contact.html' -> 'contact.html', 'index.html' -> ''."""
    return path[:-len('index.html')] if path.endswith('index.html') else path


def rel_link(from_path, to_path):
    """Relative href from page from_path to page to_path (both root-relative file paths)."""
    from_dir = posixpath.dirname(from_path) or '.'
    to_url = page_url(to_path)
    if to_url == '' or to_url.endswith('/'):
        r = posixpath.relpath(to_url.rstrip('/') or '.', from_dir)
        return './' if r == '.' else r + '/'
    return posixpath.relpath(to_url, from_dir)


def rewrite_link(m, en_path, lang):
    """href/src in an English page → the same target as seen from its <lang> copy."""
    attr, u = m.group(1), m.group(2)
    if not u or re.match(r'(https?:|mailto:|tel:|data:|//|#)', u):
        return m.group(0)
    here = out_path(en_path, lang)
    base, sep, frag = u.partition('#')
    base, qsep, query = base.partition('?')
    suffix = (qsep + query if qsep else '') + (sep + frag if sep else '')
    en_dir = posixpath.dirname(en_path) or '.'
    target = posixpath.normpath(posixpath.join(en_dir, base)) if base else posixpath.normpath(en_dir)
    is_dir = base == '' or base.endswith('/') or base in ('.', '..')
    if not (is_dir or base.endswith('.html')):  # asset: point back to the shared file
        return f'{attr}="{posixpath.relpath(target, posixpath.dirname(here) or ".")}{suffix}"'
    target_file = 'index.html' if target == '.' else (f'{target}/index.html' if is_dir else target)
    target_lang = lang if lang in page_langs(target_file) else 'en'
    href = rel_link(here, out_path(target_file, target_lang))
    if base == '' and not qsep:  # same-page link such as href="#top"
        href = ''
    extra = ' hreflang="en"' if target_lang != lang and attr == 'href' else ''
    return f'{attr}="{href}{suffix}"{extra}'


# ---------- Language dropdown ----------

def lang_menu(en_path, lang):
    here = out_path(en_path, lang)
    current = LANG_NAMES[lang]
    items = []
    for code in page_langs(en_path):
        cur = ' aria-current="page"' if code == lang else ''
        items.append(f'            <li><a href="{rel_link(here, out_path(en_path, code))}" '
                     f'hreflang="{HTML_LANG.get(code, code)}" lang="{HTML_LANG.get(code, code)}"{cur}>{LANG_NAMES[code]}</a></li>')
    return ('\n        <details class="lang-menu">'
            f'\n          <summary aria-label="{LANG_WORD[lang]}: {current}">{GLOBE}<span class="lang-name">{current}</span>{CHEVRON}</summary>'
            '\n          <ul>\n' + '\n'.join(items) + '\n          </ul>\n        </details>')


def strip_lang_menu(html):
    for pattern in (MENU_RE, SCRIPT_RE, OLD_FOOTER_RE):
        html = re.sub(pattern, '', html, flags=re.S)
    return html


def set_lang_menu(html, en_path, lang):
    """Put the dropdown at the end of the header's nav-right, and load its script."""
    here = out_path(en_path, lang)
    html = strip_lang_menu(html)
    m = re.search(r'<div class="nav-right">.*?(?=\n\s*</div>)', html, flags=re.S)
    if not m:
        raise SystemExit(f'{here}: header nav-right not found')
    html = html[:m.end()] + lang_menu(en_path, lang) + html[m.end():]
    js = posixpath.relpath('assets/js/lang-menu.js', posixpath.dirname(here) or '.')
    return html.replace('</body>', f'  <script src="{js}" defer></script>\n</body>', 1)


# ---------- Text ----------

def translate(html, table, missing, page):
    def text(m):
        raw = m.group(1)
        key = ' '.join(raw.split())
        if not key:
            return m.group(0)
        if key in table:
            lead = raw[:len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()):]
            return '>' + lead + table[key] + trail + '<'
        if key not in KEEP and re.search(r'[A-Za-z]', key):
            missing.setdefault(key, page)
        return m.group(0)

    def attr(m):
        name, val = m.group(1), m.group(2)
        if val in table:
            return f'{name}="{table[val]}"'
        if val and val not in KEEP and re.search(r'[A-Za-z]{3}', val) and not re.match(r'(https?:|[\w./-]+\.(png|jpg|webp|svg)$|website$|width=device-width)', val):
            missing.setdefault(val, page)
        return m.group(0)

    # Leave <script>, <style> and <svg> alone: park them as comments, translate, put them back.
    kept = []
    def park(m):
        kept.append(m.group(0))
        return f'<!--keep{len(kept) - 1}-->'
    html = re.sub(r'<(script|style|svg)\b.*?</\1>', park, html, flags=re.S)
    html = re.sub(r'>([^<]+)<', text, html)
    html = re.sub(r'\b(alt|title|aria-label|content)="([^"]*)"', attr, html)
    return re.sub(r'<!--keep(\d+)-->', lambda m: kept[int(m.group(1))], html)


def load_table(lang):
    path = os.path.join(I18N_DIR, f'{lang}.json')
    table = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    table.pop('_comment', None)
    return table


# ---------- Build ----------

def build():
    pages = english_pages()
    langs_used = sorted({l for p in pages for l in page_langs(p) if l != 'en'}, key=ORDER.index)
    tables = {l: load_table(l) for l in langs_used}
    missing = {l: {} for l in langs_used}
    written = set()

    for en_path in pages:
        full = os.path.join(ROOT, en_path)
        en = set_lang_menu(open(full, encoding='utf-8').read(), en_path, 'en')
        open(full, 'w', encoding='utf-8').write(en)
        source = strip_lang_menu(en)

        for lang in page_langs(en_path):
            if lang == 'en':
                continue
            html = re.sub(r'<html lang="en">', f'<html lang="{HTML_LANG.get(lang, lang)}">', source, count=1)
            html = re.sub(r'\b(href|src)="([^"]*)"', lambda m: rewrite_link(m, en_path, lang), html)
            html = re.sub(r'(<meta property="og:image" content=")([^"]*)(")',
                          lambda m: m.group(1) + posixpath.relpath(
                              posixpath.normpath(posixpath.join(posixpath.dirname(en_path) or '.', m.group(2))),
                              posixpath.dirname(out_path(en_path, lang))) + m.group(3), html)
            html = translate(html, tables[lang], missing[lang], en_path)
            html = set_lang_menu(html, en_path, lang)
            out = os.path.join(ROOT, out_path(en_path, lang))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'w', encoding='utf-8').write(html)
            written.add(out_path(en_path, lang))

    # Remove translated pages whose English page or language was dropped.
    for lang in LANG_NAMES:
        if lang == 'en' or not os.path.isdir(os.path.join(ROOT, lang)):
            continue
        for path in glob.glob(f'{lang}/**/*.html', root_dir=ROOT, recursive=True):
            if path not in written:
                os.remove(os.path.join(ROOT, path))
                print(f'removed stale {path}')
        for d in sorted(glob.glob(f'{lang}/**/', root_dir=ROOT, recursive=True), key=len, reverse=True):
            if not os.listdir(os.path.join(ROOT, d)):
                os.rmdir(os.path.join(ROOT, d))

    print(f'built {len(written)} translated pages ({", ".join(langs_used)})')
    for lang in langs_used:
        if missing[lang]:
            print(f'\nNo translation yet in _tools/i18n/{lang}.json:')
            for k, p in missing[lang].items():
                print(f'  [{p}] {k}')


if __name__ == '__main__':
    build()
