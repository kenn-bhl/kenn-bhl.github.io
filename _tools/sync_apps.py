"""Sync _data/apps.json -> index.html (app grid, story row) and the footer app columns on every page.

    python3 _tools/sync_apps.py && python3 _tools/build_i18n.py
"""
import json, re, html, sys, os
root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..'))
data = json.load(open(f'{root}/_data/apps.json', encoding='utf-8'))['apps']
page = open(f'{root}/index.html', encoding='utf-8').read()
e = lambda s: html.escape(s, quote=True)

def ico(n):
    d = re.search(r'<path d="([^"]+)"', open(f'{root}/assets/img/{n}.svg').read()).group(1)
    return f'<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="{d}"/></svg>'
ICON = {'appstore': ico('appstore'), 'googleplay': ico('googleplay')}
LABEL = {'appstore': 'App Store', 'googleplay': 'Google Play'}
STYLE = {'appstore': 'btn-inverse', 'googleplay': 'btn-tertiary'}
REGION = {'vi': 'Vietnam'}

def store_url(u):
    # Apple links: drop the {locale} segment; apps.apple.com redirects to the visitor's storefront.
    return u.replace('/{locale}/', '/')

def region_label(a, pad=''):
    r = (a.get('special_available') or '').strip()
    return f'{pad}<span class="img-label tr">Only available in {REGION.get(r, r.upper())}</span>' if r else ''

def stores(a, pad):
    out = []
    for key, field in (('appstore', 'appStoreUrl'), ('googleplay', 'googlePlayUrl')):
        u = (a.get(field) or '').strip()
        if not u:
            continue
        if u == 'coming_soon':
            out.append(f'<span class="btn btn-tertiary is-soon" aria-disabled="true" title="{LABEL[key]}: coming soon">{ICON[key]}Coming soon</span>')
        else:
            out.append(f'<a class="btn {STYLE[key]}" href="{e(store_url(u))}" target="_blank" rel="noopener">{ICON[key]}{LABEL[key]}</a>')
    if not out and not region_label(a):
        out.append('<span class="btn btn-tertiary is-soon" aria-disabled="true">Coming soon</span>')
    inner = ''.join(f'\n{pad}  {x}' for x in out)
    return f'{pad}<div class="stores">{inner}\n{pad}</div>'

def linked(a, inner, main=False):
    """Wrap inner HTML in a link to the app's landing page, if it has one.
    Only the name link is focusable; image/logo links are duplicates for mouse/touch."""
    if not a.get('landing'):
        return inner
    extra = '' if main else ' tabindex="-1" aria-hidden="true"'
    cls = ' class="link"' if main else ''
    return f'<a{cls} href="{e(a["landing"])}"{extra}>{inner}</a>'

def grid_card(a):
    p = '                '
    return f'''{p}<article class="app-card">
{p}  <div class="head">
{p}    <div class="icon">{linked(a, f'<img src="{e(a["logo"])}" alt="{e(a["name"])} icon" />')}</div>
{p}    <h4 class="t-feature-bold">{linked(a, e(a['name']), True)}</h4>
{p}    <p class="t-compact muted desc">{e(a['shortDescription'])}</p>
{stores(a, p + '    ')}
{p}  </div>
{p}  <div class="media"><span class="img-label tl">{e(a['age'])}</span>{region_label(a)}{linked(a, f'<img src="{e(a["main"])}" alt="{e(a["name"])} screenshot" />')}</div>
{p}</article>
'''

def story_card(a):
    p = '              '
    return f'''{p}<article class="story">
{p}  <div class="media">
{p}    <div class="shot">{linked(a, f'<img src="{e(a["main"])}" alt="{e(a["name"])} screenshot" />')}</div>
{region_label(a, p + "    ")}
{p}    {linked(a, f'<img class="logo" src="{e(a["logo"])}" alt="{e(a["name"])} logo" width="128" height="128" />')}
{p}  </div>
{p}  <div class="body">
{p}    <h3 class="t-feature-bold">{linked(a, e(a['name']), True)}</h3>
{p}    <p class="t-compact muted">{e(a['shortDescription'])}</p>
{stores(a, p + '    ')}
{p}  </div>
{p}</article>
'''

def replace_block(page, open_tag, inner, indent):
    i = page.index(open_tag) + len(open_tag)
    # find matching close of this div
    depth, j = 1, i
    for m in re.finditer(r'<(/?)div\b', page[i:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            j = i + m.start(); break
    return page[:i] + '\n' + inner + indent + page[j:]

data = sorted(data, key=lambda a: a.get('position', float('inf')))  # stable: ties keep JSON order
edu = [a for a in data if a['group'] == 'Education']
life = [a for a in data if a['group'] == 'Life']
page = replace_block(page, '<div class="app-grid" id="education">', ''.join(map(grid_card, edu)), '            ')
page = re.sub(r'<div class="story-row"[^>]*>', '<div class="story-row" id="lifestyle">', page, count=1)
page = replace_block(page, '<div class="story-row" id="lifestyle">', ''.join(map(story_card, life)), '            ')

open(f'{root}/index.html', 'w', encoding='utf-8').write(page)

def sync_footers():
    """Footer columns on every page: only apps with a landing page, paths relative to the page."""
    import glob, os
    pages = [f'{root}/index.html', f'{root}/contact.html'] + sorted(glob.glob(f'{root}/*/index.html') + glob.glob(f'{root}/*/privacy.html'))
    pages = [p for p in pages if os.path.relpath(p, root).split(os.sep)[0] not in ('vi',) and not os.path.relpath(p, root).startswith('_')]
    for path in pages:
        rel = os.path.relpath(path, root)
        folder = os.path.dirname(rel)
        prefix = '../' if folder else ''
        html = open(path, encoding='utf-8').read()
        if '<footer class="site-footer' not in html:
            continue
        def items(apps):
            out = []
            for a in apps:
                if not a.get('landing'):
                    continue
                href, cur = prefix + a['landing'], ''
                if folder and a['landing'].rstrip('/') == folder:
                    href = './'
                    if rel.endswith('index.html'):
                        cur = ' aria-current="page"'
                out.append(f'                <li><a class="link" href="{e(href)}"{cur}>{e(a["name"])}</a></li>')
            return '\n'.join(out)
        for label, apps in (('Education', edu), ('Lifestyle', life)):
            html = re.sub(rf'(<p class="t-compact muted">{label}</p>\s*<ul class="t-body">\n).*?(\s*</ul>)',
                          lambda m: m.group(1) + items(apps) + m.group(2), html, count=1, flags=re.S)
        open(path, 'w', encoding='utf-8').write(html)

sync_footers()

print('education:', [a['name'] for a in edu], 'life:', [a['name'] for a in life])
