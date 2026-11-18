#!/usr/bin/env python3
"""mindseeder.io 랜딩 빌드 — src/page.html 틀 + src/strings.<lang>.json → index.html(영어), ko/index.html(한국어).
정적 HTML이라 자바스크립트를 실행하지 않는 검색·AI 크롤러도 본문을 읽는다. 사용: python3 src/build.py"""
import html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = (ROOT / 'src/page.html').read_text()
APP = 'https://app.mindseeder.io/'
FONTS = {
    'en': 'https://fonts.googleapis.com/css2?family=Instrument+Sans:wdth,wght@75..100,400..700&family=DM+Mono:wght@400;500&display=swap',
    'ko': 'https://fonts.googleapis.com/css2?family=Instrument+Sans:wdth,wght@75..100,400..700&family=DM+Mono:wght@400;500&family=Gothic+A1:wght@400;500&display=swap',
}
TICK = '<span class="ui-file__check"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m4.5 8.2 2.3 2.3 4.7-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>'
STAGE_TONE = {'흙': 'soil', 'Soil': 'soil', '씨앗': 'seed', 'Seed': 'seed', '새싹': 'sprout', 'Sprout': 'sprout', '줄기': 'stem', 'Stem': 'stem',
              '꽃': 'flower', 'Flower': 'flower', '열매': 'fruit', 'Fruit': 'fruit'}
REDIRECT = """<script>(function(){try{var c=localStorage.getItem('ms-lang');if(!c&&/^ko\\b/i.test(navigator.language||'')&&!/bot|crawl|spider/i.test(navigator.userAgent)){location.replace('ko/'+location.search+location.hash);}}catch(e){}})();</script>"""


def esc(v: str) -> str:
    return html.escape(v, quote=True)


def build(lang: str) -> None:
    s = json.loads((ROOT / f'src/strings.{lang}.json').read_text())
    root = s['root']
    canonical = 'https://mindseeder.io/' + ('' if lang == 'en' else 'ko/')
    rows = []
    for tree, tone, title, stage, cls, age in s['rows']:
        av = tree.replace('+', '')
        rows.append(f'                  <li class="ui-win__row" data-row><span class="ui-avatar" data-tone="{tone}">{esc(av)}</span>'
                    f'<span class="ui-win__who">{esc(s["col_tree"])} {esc(tree)}</span><span class="ui-win__sub">{esc(title)}</span>'
                    f'<span class="ui-win__st {cls}" data-st>{esc(stage)}</span><span class="ui-win__age">{esc(age)}</span></li>')
    files = []
    for icon, name, kind in s['files']:
        files.append(f'                    <li class="ui-file is-done"><span class="ui-file__icon"><img data-icon="{icon}" src="{root}assets/icons/{icon}.svg" alt=""></span>'
                     f'<span class="ui-file__name">{esc(name)}</span><span class="ui-file__kind">{esc(kind)}</span><span class="ui-file__bar"><i></i></span>{TICK}</li>')
    faq = [f'          <div class="faq__item"><h3>{esc(q)}</h3><p>{esc(a)}</p></div>' for q, a in s['faq']]
    jsonld = [
        {'@context': 'https://schema.org', '@type': 'SoftwareApplication', 'name': 'mindseeder', 'url': canonical,
         'applicationCategory': 'ProductivityApplication', 'operatingSystem': 'Web browser', 'inLanguage': ['en', 'ko', 'ja', 'zh-Hans'],
         'description': s['description'], 'image': 'https://mindseeder.io/' + s['og_image'],
         'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
         'featureList': [s['ai_h'], s['trees_h'], s['f4_t'], s['f1_t'], s['f2_t'], s['f3_t']],
         'sameAs': ['https://app.mindseeder.io/']},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'inLanguage': lang,
         'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in s['faq']]},
    ]
    out = TPL
    special = {
        'canonical': canonical, 'app_url': APP, 'guide_href': 'guide/', 'font_href': FONTS[lang], 'font_extra': ', "Gothic A1"' if lang == 'ko' else '',
        'rows_html': '\n'.join(rows), 'files_html': '\n'.join(files), 'faq_html': '\n'.join(faq),
        'jsonld': json.dumps(jsonld, ensure_ascii=False).replace('</', '<\\/'),
        'lang_redirect': '',
        'ai_diagram': s['ai_diagram'],  # JSON inside <script type="application/json">: not HTML-escaped
        'why': s['why'],  # holds one <strong>
    }
    def rep(m):
        k = m.group(1)
        if k in special: return special[k]
        if k not in s: raise KeyError(f'{lang}: missing {k}')
        v = s[k]
        return esc(v) if isinstance(v, str) else str(v)
    out = re.sub(r'\{\{(\w+)\}\}', rep, out)
    dest = ROOT / ('index.html' if lang == 'en' else 'ko/index.html')
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(out)
    print('wrote', dest.relative_to(ROOT), len(out))


def build_guide(lang: str) -> None:
    """AI로 문서 만들기 안내(한·영) — 요청문은 src/prompts/<id>.<lang>.md를 그대로 싣는다"""
    s = json.loads((ROOT / f'src/guide.{lang}.json').read_text())
    tpl = (ROOT / 'src/guide.html').read_text()
    canonical = 'https://mindseeder.io/' + s['path']
    rows = '\n'.join(f'        <tr><th scope="row">{esc(a)}</th><td>{esc(b)}</td><td>{esc(c)}</td></tr>' for a, b, c in s['rows'])
    prompts = []
    for pid, name, desc in s['prompts']:
        body = (ROOT / f'src/prompts/{pid}.{lang}.md').read_text().strip()
        prompts.append(f'''    <section class="prompt" aria-labelledby="{pid}-h">
      <div class="prompt__head"><div><h3 id="{pid}-h">{esc(name)}</h3><p>{esc(desc)}</p></div>
        <button class="btn btn--secondary" type="button" data-copy="{pid}-text" data-copied="{esc(s['copied'])}">{esc(s['copy'])}</button></div>
      <pre id="{pid}-text">{esc(body)}</pre>
    </section>''')
    tips = '\n'.join(f'      <li>{esc(t)}</li>' for t in s['tips'])
    sources = '\n'.join(f'      <li><a class="link" href="{esc(u)}" rel="noopener">{esc(n)}</a></li>' for n, u in s['sources'])
    jsonld = {'@context': 'https://schema.org', '@type': 'HowTo', 'name': s['h1'], 'description': s['description'], 'inLanguage': lang,
              'url': canonical, 'step': [{'@type': 'HowToStep', 'position': i + 1, 'name': n, 'text': t} for i, (n, t) in
                                         enumerate([(s['s1_h'], s['s1']), (s['s2_h'], s['s2']), (s['s3_h'], s['s3']), (s['s4_h'], ' '.join(s['tips']))])]}
    special = {'canonical': canonical, 'font_href': FONTS[lang], 'font_extra': ', "Gothic A1"' if lang == 'ko' else '',
               'rows_html': rows, 'prompts_html': '\n'.join(prompts), 'tips_html': tips, 'sources_html': sources,
               'jsonld': json.dumps(jsonld, ensure_ascii=False).replace('</', '<\\/'), 'lead_short': s['lead'].split('. ')[0] + '.' if lang == 'en' else s['lead'].split('. ')[0] + '.'}
    def rep(m):
        k = m.group(1)
        if k in special: return special[k]
        if k not in s: raise KeyError(f'guide {lang}: missing {k}')
        return esc(s[k])
    out = re.sub(r'\{\{(\w+)\}\}', rep, tpl)
    dest = ROOT / s['path'] / 'index.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    print('wrote', dest.relative_to(ROOT), len(out))


for lang in ('en', 'ko'):
    build(lang)
    build_guide(lang)
