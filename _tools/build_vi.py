#!/usr/bin/env python3
"""Build the Vietnamese site (vi/) from the English pages, and refresh the footer
language switcher on every page.

    python3 _tools/build_vi.py

- English pages: index.html, contact.html, <app>/index.html, <app>/privacy.html.
- Each one becomes vi/<same path>, with text translated from _tools/vi.json
  (exact English string → Vietnamese), html lang="vi", and links rewritten:
  page links stay inside vi/, asset links (images, CSS, JS) point back to the
  shared English files.
- Strings with no translation are listed at the end; add them to vi.json and rerun.
"""
import glob
import json
import os
import posixpath
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..'))
VI = json.load(open(os.path.join(ROOT, '_tools', 'vi.json'), encoding='utf-8'))
VI.pop('_comment', None)

# Text that is the same in both languages (names, brands, contact details).
KEEP = {'J-Studio', 'App Store', 'Google Play', 'J-Kids', '1000 Words', 'New Word Learning',
        'Daily Task', 'Lấy số Vietlott', 'Subsum', 'kenn.bhl@gmail.com', '+84 856 011 093',
        'English', 'Tiếng Việt'}

GLOBE = ('<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="8" cy="8" r="6.25" stroke="currentColor" stroke-width="1.3"/>'
         '<path d="M1.75 8h12.5M8 1.75c1.7 1.8 2.5 3.9 2.5 6.25S9.7 12.45 8 14.25C6.3 12.45 5.5 10.35 5.5 8S6.3 3.55 8 1.75Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>')


def english_pages():
    pages = ['index.html', 'contact.html']
    pages += sorted(glob.glob('*/index.html', root_dir=ROOT) + glob.glob('*/privacy.html', root_dir=ROOT))
    return [p for p in pages if not p.startswith(('vi/', '_')) and os.path.exists(os.path.join(ROOT, p))]


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


def lang_switch(here, en_path, lang):
    vi_path = 'vi/' + en_path
    items = []
    for code, label, target in (('en', 'English', en_path), ('vi', 'Tiếng Việt', vi_path)):
        cur = ' aria-current="page"' if code == lang else ''
        items.append(f'                  <li><a class="link" href="{rel_link(here, target)}" hreflang="{code}" lang="{code}"{cur}>{label}</a></li>')
    aria = 'Ngôn ngữ' if lang == 'vi' else 'Language'
    return ('\n              <nav class="lang-switch" aria-label="' + aria + '">\n                ' + GLOBE +
            '\n                <ul class="t-compact">\n' + '\n'.join(items) + '\n                </ul>\n              </nav>')


def set_lang_switch(html, here, en_path, lang):
    html = re.sub(r'\n\s*<nav class="lang-switch".*?</nav>', '', html, flags=re.S)
    m = re.search(r'(<div class="footer-brand">\s*<a class="brand link".*?</a>)', html, flags=re.S)
    if not m:
        raise SystemExit(f'{here}: footer-brand not found')
    return html[:m.end()] + lang_switch(here, en_path, lang) + html[m.end():]


def rewrite_url(u, en_path, vi_path):
    if not u or re.match(r'(https?:|mailto:|tel:|data:|//|#)', u):
        return u
    base, sep, frag = u.partition('#')
    base, qsep, query = base.partition('?')
    en_dir = posixpath.dirname(en_path)
    target = posixpath.normpath(posixpath.join(en_dir, base)) if base else posixpath.normpath(en_dir or '.')
    is_dir = base == '' or base.endswith('/') or base in ('.', '..')
    is_page = is_dir or base.endswith('.html')
    if is_page:
        target = posixpath.normpath(posixpath.join('vi', target))
    vi_dir = posixpath.dirname(vi_path)
    r = posixpath.relpath(target, vi_dir)
    if is_dir:
        r = './' if r == '.' else r + '/'
    if base == '' and not is_page:
        r = ''
    return r + (qsep + query if qsep else '') + (sep + frag if sep else '')


def translate(html, missing, page):
    def text(m):
        raw = m.group(1)
        key = ' '.join(raw.split())
        if not key:
            return m.group(0)
        if key in VI:
            lead = raw[:len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()):]
            return '>' + lead + VI[key] + trail + '<'
        if key not in KEEP and re.search(r'[A-Za-z]', key):
            missing.setdefault(key, page)
        return m.group(0)

    def attr(m):
        name, val = m.group(1), m.group(2)
        if val in VI:
            return f'{name}="{VI[val]}"'
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


def build():
    missing = {}
    pages = english_pages()
    for en_path in pages:
        full = os.path.join(ROOT, en_path)
        en = open(full, encoding='utf-8').read()
        en = set_lang_switch(en, en_path, en_path, 'en')
        open(full, 'w', encoding='utf-8').write(en)

        vi_path = 'vi/' + en_path
        vi = re.sub(r'<html lang="en">', '<html lang="vi">', en, count=1)
        vi = re.sub(r'\n\s*<nav class="lang-switch".*?</nav>', '', vi, flags=re.S)
        vi = re.sub(r'\b(href|src)="([^"]*)"', lambda m: f'{m.group(1)}="{rewrite_url(m.group(2), en_path, vi_path)}"', vi)
        vi = re.sub(r'(<meta property="og:image" content=")([^"]*)(")',
                    lambda m: m.group(1) + rewrite_url(m.group(2), en_path, vi_path) + m.group(3), vi)
        vi = translate(vi, missing, en_path)
        vi = set_lang_switch(vi, vi_path, en_path, 'vi')
        out = os.path.join(ROOT, vi_path)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'w', encoding='utf-8').write(vi)
    print(f'built {len(pages)} Vietnamese pages')
    if missing:
        print('\nNo translation yet (add to _tools/vi.json):')
        for k, p in missing.items():
            print(f'  [{p}] {k}')


if __name__ == '__main__':
    build()
