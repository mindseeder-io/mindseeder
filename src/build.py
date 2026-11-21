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
        'canonical': canonical, 'app_url': f'{APP}?lang={lang}', 'guide_href': 'guide/',
        # 첫 화면 보조 버튼·메뉴 첫 카드: 파일럿 예시(아폴로)로 바로 — 앱은 lang으로 첫 화면 언어를, sample로 그 편을 맨 위에 둔다(사용자 11/21 진입 개선)
        'app_sample_url': f'{APP}?sample=apollo11-1202&lang={lang}',
        'cta_sample_note_html': f'<p class="t-small muted" style="flex-basis: 100%; margin: 0">{esc(s["cta_sample_note"])}</p>' if s.get('cta_sample_note') else '', 'font_href': FONTS[lang], 'font_extra': ', "Gothic A1"' if lang == 'ko' else '',
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
    special = {'canonical': canonical, 'app_url': f'{APP}?lang={lang}', 'font_href': FONTS[lang], 'font_extra': ', "Gothic A1"' if lang == 'ko' else '',
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


def build_edition(lang: str, slug: str) -> None:
    """정원 한 편(웹 글) — src/edition.html 틀 + src/edition.<slug>.<lang>.json. 묶음 이름은 strings.<lang>.json의 collection_name 하나에서 온다"""
    s = json.loads((ROOT / f'src/edition.{slug}.{lang}.json').read_text())
    s['collection_name'] = json.loads((ROOT / f'src/strings.{lang}.json').read_text())['collection_name']
    tpl = (ROOT / 'src/edition.html').read_text()
    canonical = 'https://mindseeder.io/' + s['path']
    utm = 'utm_source=mindseeder.io&utm_medium=edition&utm_campaign=' + s.get('campaign', f'{slug}-1')
    app_href = f'{APP}?sample={s["sample"]}&lang={lang}&{utm}'
    next_href = f'{APP}?sample={s["next_sample"]}&lang={lang}&{utm}'
    picks = '\n'.join(f'          <label><input type="radio" name="first-look" value="{i}">{esc(p)}</label>' for i, p in enumerate(s['picks']))
    do = '\n'.join(f'        <li>{esc(t)}</li>' for t in s['do'])
    sources = '\n'.join(f'        <li>{esc(t)}<span class="links">' + ''.join(f'<a class="link" href="{esc(u)}" rel="noopener">{esc(n)}</a>' for n, u in links) + '</span></li>'
                        for t, links in s['sources'])
    how = '\n'.join(f'        <dt>{esc(a)}</dt><dd>{esc(b)}</dd>' for a, b in s['how'])
    meta = esc(s['meta']) + (f' <b>{esc(s["notes_lang"])}</b>' if s.get('notes_lang') else '')
    art = lambda name, url, date: {'@type': 'VisualArtwork', 'name': name, 'creator': {'@type': 'Person', 'name': 'Katsushika Hokusai'},
                                   'dateCreated': date, 'artform': 'Woodblock print', 'url': url, 'license': 'https://creativecommons.org/publicdomain/zero/1.0/'}
    jsonld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': s['h1'], 'description': s['description'], 'inLanguage': lang,
              'url': canonical, 'datePublished': s['published'], 'image': 'https://mindseeder.io/img/' + s['og_image'],
              'isPartOf': {'@type': 'CreativeWorkSeries', 'name': s['collection_name']},
              'publisher': {'@type': 'Organization', 'name': 'mindseeder', 'url': 'https://mindseeder.io/'},
              'about': [art('Under the Wave off Kanagawa (The Great Wave)', 'https://www.metmuseum.org/art/collection/search/45434', 'ca. 1830–32'),
                        art('South Wind, Clear Sky (Red Fuji)', 'https://www.metmuseum.org/art/collection/search/36490', 'ca. 1830–32')]}
    special = {'canonical': canonical, 'app_url': f'{APP}?lang={lang}', 'font_href': FONTS[lang], 'font_extra': ', "Gothic A1"' if lang == 'ko' else '',
               'app_href': esc(app_href), 'next_href': esc(next_href), 'picks_html': picks, 'do_html': do, 'sources_html': sources,
               'how_html': how, 'meta_html': meta, 'jsonld': json.dumps(jsonld, ensure_ascii=False).replace('</', '<\\/')}
    def rep(m):
        k = m.group(1)
        if k in special: return special[k]
        if k not in s: raise KeyError(f'edition {slug} {lang}: missing {k}')
        return esc(s[k])
    out = re.sub(r'\{\{(\w+)\}\}', rep, tpl)
    dest = ROOT / s['path'] / 'index.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    print('wrote', dest.relative_to(ROOT), len(out))


for lang in ('en', 'ko'):
    build(lang)
    build_guide(lang)
    build_edition(lang, 'hokusai')
