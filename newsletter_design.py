"""Responsive editorial HTML renderer for reviewed newsletter content."""
from datetime import date
from html import escape
from urllib.parse import urlparse


def safe_url(value, image=False):
    value = str(value or '').strip()
    if image and value.startswith(('data:image/png;base64,', 'data:image/jpeg;base64,', 'data:image/webp;base64,')):
        return value
    return value if urlparse(value).scheme in ('https', 'http') else ''


def format_newsletter_html(sections, newsletter_title='Newsletter', issue_label=None,
                           cover_topics=None, featured_url=None):
    def esc(value):
        return escape(str(value or ''), quote=True)

    def bilingual(en, fi=None):
        return f'<span class="lang-en">{esc(en)}</span><span class="lang-fi">{esc(fi or en)}</span>'

    entries = [e for s in sections for e in s['entries']]
    featured = next((e for e in entries if e['source_url'] == featured_url), None)
    if featured is None and entries:
        featured = next((e for s in sections if s['section_title'] != 'Events' for e in s['entries']), entries[0])
    topics = cover_topics if cover_topics is not None else list(dict.fromkeys(
        str(t) for e in entries for t in (e.get('topics') or []) if str(t).strip()))[:4]
    issue_label = issue_label if issue_label is not None else date.today().strftime('%m / %Y')

    def photo(entry, cover=False):
        src = safe_url(entry.get('image_url'), image=True) if entry.get('image_approved') else ''
        if not src:
            return ''
        credit = entry.get('image_credit', '')
        return (f'<figure class="{"cover-photo" if cover else "article-photo"}">'
                f'<img src="{esc(src)}" alt="{esc(entry.get("image_alt") or entry["title"])}" '
                'onerror="this.closest(\'figure\').hidden=true">'
                f'<figcaption>{esc(credit)}</figcaption></figure>')

    def source_link(entry):
        url = safe_url(entry['source_url'])
        host = urlparse(url).netloc.removeprefix('www.')
        return f'<a class="read-more" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{bilingual("Read more at " + host, "Lue lisää: " + host)} <span aria-hidden="true">↗</span></a>'

    def story(entry, idx, feature=False, event=False):
        visual = photo(entry)
        kind = 'featured' if feature else ('event' if event else 'story')
        tag = bilingual('Featured story', 'Nosto') if feature else f'{idx:02d}'
        return f'''<article class="{kind} {'with-image' if visual else 'text-only'} {'reverse' if idx % 2 == 0 else ''}">
          <div class="article-copy"><div class="eyebrow">{tag}</div>
          <h3>{bilingual(entry['title'], entry.get('title_fi'))}</h3>
          <p>{bilingual(entry['summary'], entry.get('summary_fi'))}</p>
          {source_link(entry)}</div>{visual}</article>'''

    body = ''
    if featured:
        body += '<section class="feature-section">' + story(featured, 1, feature=True) + '</section>'
    labels = {'Events': 'Tapahtumat', 'Field Highlights': 'Alan kohokohdat'}
    for section in sections:
        remaining = [e for e in section['entries'] if e is not featured]
        if not remaining:
            continue
        event = section['section_title'] == 'Events'
        body += f'<section class="content-section"><header class="section-heading"><h2>{bilingual(section["section_title"], labels.get(section["section_title"]))}</h2><span>{len(remaining):02d}</span></header>'
        body += '<div class="events-grid">' if event else '<div>'
        body += ''.join(story(e, i + 1, event=event) for i, e in enumerate(remaining)) + '</div></section>'
    cover_image = photo(featured, cover=True) if featured else ''
    tags = ''.join(f'<span class="topic">{esc(t)}</span>' for t in topics)
    css = CSS
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(newsletter_title)}</title><style>{css}</style></head>
<body><main class="newsletter"><header class="cover">
<div class="topline"><span class="brand">Suomen eOppimiskeskus ry</span><button onclick="toggleLanguage()" id="langToggleBtn" aria-label="Switch to Finnish">FI</button></div>
<div class="issue">{esc(issue_label)} <span>•</span> {bilingual('For our learning community', 'Oppimisen yhteisöllemme')}</div>
<h1>{esc(newsletter_title)}<span class="title-dot">.</span></h1>
<div class="cover-bottom"><p class="cover-intro">{bilingual('Ideas, people and perspectives shaping learning.', 'Ideoita, ihmisiä ja näkökulmia oppimiseen.')}</p><div class="issue-topics"><div class="eyebrow">{bilingual('In this issue', 'Tässä numerossa')}</div><div class="topics">{tags}</div></div></div>
{cover_image}<div class="cover-foot"><span>{bilingual('Learning together. Looking ahead.', 'Opitaan yhdessä. Katsotaan eteenpäin.')}</span><span>↓</span></div></header>
{body}<footer><strong>Suomen eOppimiskeskus ry</strong><p>{bilingual('AI-assisted draft · Reviewed by you before sharing', 'Tekoälyavusteinen luonnos · Tarkista ennen jakamista')}</p><span>{esc(issue_label)}</span></footer></main>
<script>function toggleLanguage(){{const fi=document.body.classList.toggle('show-fi');document.documentElement.lang=fi?'fi':'en';const b=document.getElementById('langToggleBtn');b.textContent=fi?'EN':'FI';b.setAttribute('aria-label',fi?'Switch to English':'Switch to Finnish');}}</script></body></html>'''


CSS = '''
*{box-sizing:border-box}body{margin:0;background:#e9e7e0;color:#203d35;font-family:Arial,Helvetica,sans-serif;line-height:1.65}.newsletter{max-width:1040px;margin:32px auto;background:#faf9f5;box-shadow:0 12px 60px #203d3510}.cover{padding:44px 56px 0;background:#163f35;color:#f7f5eb}.topline{display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid #ffffff40;padding-bottom:24px}.brand{font-size:23px;font-weight:700;letter-spacing:-.7px}button{border:1px solid #ffffff70;color:inherit;background:transparent;border-radius:30px;padding:7px 16px;cursor:pointer}.issue{margin-top:35px;font-size:11px;letter-spacing:1.6px;text-transform:uppercase;color:#d6dfd4}.issue span{margin:0 5px}h1{font-family:Georgia,serif;font-weight:400;font-size:clamp(64px,10vw,120px);letter-spacing:-6px;line-height:1.1;margin:14px 0 28px}.title-dot{color:#e8b26e}.cover-bottom{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:start;margin-bottom:34px}.cover-intro{font-family:Georgia,serif;font-size:24px;line-height:1.4;margin:0;max-width:330px}.eyebrow{text-transform:uppercase;letter-spacing:2px;font-size:10px;font-weight:700;color:#a45e2a;margin-bottom:14px}.cover .eyebrow{color:#e8b26e}.topics{display:flex;flex-wrap:wrap;gap:8px}.topic{border:1px solid #ffffff45;border-radius:30px;padding:4px 12px;font-size:12px}figure{margin:0;min-width:0}figure[hidden]{display:none}img{display:block;width:100%;object-fit:cover}.cover-photo img{height:360px}.cover-photo figcaption{color:#d6dfd4}.cover-foot{display:flex;justify-content:space-between;align-items:center;padding:20px 0;font-size:11px;letter-spacing:.5px}.cover-foot>span:last-child{font-size:24px;color:#e8b26e}.feature-section,.content-section{padding:48px 56px}.feature-section{background:#eeeee4}.featured,.story{display:grid;grid-template-columns:1.1fr 1fr;gap:36px;align-items:center}.text-only{grid-template-columns:1fr}.text-only .article-copy{max-width:740px}.featured h3{font-size:36px}.article-copy h3{font-family:Georgia,serif;font-weight:400;line-height:1.2;letter-spacing:-.5px;margin:0 0 18px}.article-copy p{font-size:15px;color:#52645d;margin:0 0 22px;white-space:pre-line}.article-photo img{height:280px;border-radius:2px}figcaption{font-size:10px;color:#66776e;padding-top:8px;overflow-wrap:anywhere}.read-more{color:#275a47;font-size:12px;font-weight:700;text-decoration:none;border-bottom:1px solid #b5c8b6;padding-bottom:5px}.read-more:hover{border-color:#275a47}.section-heading{display:flex;justify-content:space-between;align-items:center;border-top:2px solid #284f40;border-bottom:1px solid #cbd2c6;padding:14px 0;margin-bottom:32px}.section-heading h2{font-size:12px;letter-spacing:2px;text-transform:uppercase;margin:0}.section-heading>span{font-size:12px;color:#7b887c}.story{padding:28px 0 36px;border-bottom:1px solid #dce0d6}.story:first-child{padding-top:0}.story:last-child{border:0;padding-bottom:0}.story h3{font-size:29px}.story.reverse.with-image .article-copy{order:2}.events-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.event{padding:26px;background:#eeeee4;border-top:3px solid #c18b4e}.event h3{font-size:25px}.event .article-photo{margin-top:22px}.event .article-photo img{height:190px}.content-section+.content-section{padding-top:0}footer{background:#e1e7dc;padding:34px 56px;font-size:12px}footer strong{font-size:17px}footer p{margin:8px 0;color:#52645d}footer>span{font-size:10px;letter-spacing:2px}.lang-fi{display:none}body.show-fi .lang-en{display:none}body.show-fi .lang-fi{display:inline}h3,p,a,.topic{overflow-wrap:anywhere}
@media(max-width:640px){.newsletter{margin:0}.cover{padding:28px 24px 0}.brand{font-size:18px}h1{letter-spacing:-3px;font-size:64px}.cover-bottom{grid-template-columns:1fr;gap:22px}.cover-intro{font-size:22px}.cover-photo img{height:240px}.feature-section,.content-section{padding:32px 24px}.featured,.story,.events-grid{grid-template-columns:1fr;gap:22px}.story.reverse.with-image .article-copy{order:0}.featured h3{font-size:30px}.story h3{font-size:26px}.article-photo img{height:240px}footer{padding:28px 24px}}
@media print{body{background:white}.newsletter{margin:0;box-shadow:none;max-width:none}.cover{break-after:page;print-color-adjust:exact}.story,.event,figure{break-inside:avoid}button{display:none}footer{print-color-adjust:exact}}
'''
