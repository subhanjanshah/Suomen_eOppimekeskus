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
        return f'<a class="read-more" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc("Read more at " + host)} <span aria-hidden="true">↗</span></a>'

    def story(entry, idx, feature=False, event=False):
        visual = photo(entry)
        kind = 'featured' if feature else ('event' if event else 'story')
        tag = esc('Featured story') if feature else f'{idx:02d}'
        return f'''<article class="{kind} {'with-image' if visual else 'text-only'} {'reverse' if idx % 2 == 0 else ''}">
          <div class="article-copy"><div class="eyebrow">{tag}</div>
          <h3>{esc(entry['title'])}</h3>
          <p>{esc(entry['summary'])}</p>
          {source_link(entry)}</div>{visual}</article>'''

    body = ''
    if featured:
        body += '<section class="feature-section">' + story(featured, 1, feature=True) + '</section>'
    for section in sections:
        remaining = [e for e in section['entries'] if e is not featured]
        if not remaining:
            continue
        event = section['section_title'] == 'Events'
        body += f'<section class="content-section"><header class="section-heading"><h2>{esc(section["section_title"])}</h2><span>{len(remaining):02d}</span></header>'
        body += '<div class="events-grid">' if event else '<div>'
        body += ''.join(story(e, i + 1, event=event) for i, e in enumerate(remaining)) + '</div></section>'
    cover_image = photo(featured, cover=True) if featured else ''
    tags = ''.join(f'<span class="topic">{esc(t)}</span>' for t in topics)
    css = CSS
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(newsletter_title)}</title><style>{css}</style></head>
<body><main class="newsletter"><header class="cover">
<div class="topline"><span class="brand">Suomen eOppimiskeskus ry</span></div>
<div class="issue">{esc(issue_label)} <span>•</span> For our learning community</div>
<h1>{esc(newsletter_title)}<span class="title-dot">.</span></h1>
<div class="cover-bottom"><p class="cover-intro">Ideas, people and perspectives shaping learning.</p><div class="issue-topics"><div class="eyebrow">In this issue</div><div class="topics">{tags}</div></div></div>
{cover_image}<div class="cover-foot"><span>Learning together. Looking ahead.</span><span>↓</span></div></header>
{body}<footer><strong>Suomen eOppimiskeskus ry</strong><p>AI-assisted draft · Reviewed by you before sharing</p><span>{esc(issue_label)}</span></footer></main>
</body></html>'''


CSS = '''
*{box-sizing:border-box}
body{margin:0;background:#e9e7e0;color:#203d35;font-family:Arial,Helvetica,sans-serif;line-height:1.65}
.newsletter{max-width:1040px;margin:32px auto;background:#faf9f5;box-shadow:0 12px 60px #203d3510;border-radius:20px;overflow:hidden}
.cover{position:relative;overflow:hidden;padding:44px 56px 0;background:radial-gradient(900px 480px at 18% -15%,#2a5747 0%,rgba(42,87,71,0) 65%),#163f35;color:#f7f5eb}
.topline{display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid #ffffff40;padding-bottom:24px}
.brand{font-size:23px;font-weight:700;letter-spacing:-.7px}
.issue{margin-top:35px;font-size:11px;letter-spacing:1.6px;text-transform:uppercase;color:#d6dfd4}
.issue span{margin:0 5px}
h1{font-family:Georgia,serif;font-weight:400;font-size:clamp(64px,10vw,120px);letter-spacing:-6px;line-height:1.1;margin:14px 0 28px}
.title-dot{color:#C6004B}
.cover-bottom{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:start;margin-bottom:34px}
.cover-intro{font-family:Georgia,serif;font-size:24px;line-height:1.4;margin:0;max-width:330px}
.eyebrow{text-transform:uppercase;letter-spacing:2px;font-size:10px;font-weight:700;color:#a45e2a;margin-bottom:14px}
.cover .eyebrow{color:#C6004B}
.topics{display:flex;flex-wrap:wrap;gap:8px}
.topic{border:1px solid #ffffff45;border-radius:30px;padding:4px 12px;font-size:12px}
.topics .topic:nth-child(4n+1){background:#C6004B2e;border-color:#C6004B66}
.topics .topic:nth-child(4n+2){background:#ffffff1f;border-color:#ffffff50}
.topics .topic:nth-child(4n+3){background:#e8b26e2e;border-color:#e8b26e66}
.topics .topic:nth-child(4n+4){background:#7fc7b02e;border-color:#7fc7b066}
figure{margin:0;min-width:0}
figure[hidden]{display:none}
img{display:block;width:100%;object-fit:contain;background:#eeeee4}
.cover-photo img{height:360px;background:#0f2d26}
.cover-photo figcaption{color:#d6dfd4}
.cover-foot{display:flex;justify-content:space-between;align-items:center;padding:20px 0;font-size:11px;letter-spacing:.5px}
.cover-foot>span:last-child{font-size:24px;color:#C6004B}
.feature-section,.content-section{padding:48px 56px}
.feature-section{position:relative;overflow:hidden;background:#eeeee4}
.feature-section::before{content:"\\201C";position:absolute;top:-60px;left:24px;font-family:Georgia,serif;font-size:320px;line-height:1;color:#20302508;pointer-events:none;z-index:0}
.featured,.story,.event.with-image{display:grid;grid-template-columns:1.1fr 1fr;gap:36px;align-items:center}
.featured{position:relative;z-index:1}
.text-only{grid-template-columns:1fr}
.text-only .article-copy{max-width:740px}
.featured h3{font-size:36px}
.article-copy h3{font-family:Georgia,serif;font-weight:400;line-height:1.2;letter-spacing:-.5px;margin:0 0 18px}
.article-copy p{font-size:15px;color:#52645d;margin:0 0 22px;white-space:pre-line}
.featured .article-copy p::first-letter{float:left;font-family:Georgia,serif;font-size:68px;line-height:.78;font-weight:700;color:#C6004B;padding:4px 10px 0 0}
.article-photo img{height:280px;border-radius:14px}
figcaption{font-size:10px;color:#66776e;padding-top:8px;overflow-wrap:anywhere}
.read-more{display:inline-flex;align-items:center;gap:6px;color:#163f35;background:#e7ece3;font-size:12px;font-weight:700;text-decoration:none;border-radius:30px;padding:9px 16px 9px 18px;transition:background .15s ease}
.read-more:hover{background:#d7e2d1}
.section-heading{display:flex;justify-content:space-between;align-items:center;border-top:2px solid #284f40;border-bottom:1px solid #cbd2c6;padding:14px 0;margin-bottom:32px}
.section-heading h2{display:flex;align-items:center;gap:8px;font-size:12px;letter-spacing:2px;text-transform:uppercase;margin:0}
.section-heading h2::before{content:"";width:7px;height:7px;border-radius:50%;background:#C6004B;display:inline-block}
.section-heading>span{font-size:12px;color:#7b887c}
.story{padding:28px 0 36px;border-bottom:1px solid #dce0d6}
.story:first-child{padding-top:0}
.story:last-child{border:0;padding-bottom:0}
.story h3{font-size:29px}
.story.reverse.with-image .article-copy{order:2}
.content-section .story .eyebrow,.content-section .event .eyebrow{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;font-size:11px;letter-spacing:0;text-transform:none;color:#fff;margin-bottom:14px}
.content-section .story .eyebrow{background:#1f4738}
.content-section .event .eyebrow{background:#C6004B}
.events-grid{display:grid;grid-template-columns:1fr;gap:22px}
.event{padding:26px;background:#eeeee4;border-radius:14px;border-left:4px solid #C6004B;box-shadow:0 3px 14px #1f3a2f12}
.event h3{font-size:25px}
.event .article-photo img{height:220px;border-radius:12px}
.content-section+.content-section{padding-top:0}
footer{background:#e1e7dc;padding:48px 56px 34px;font-size:12px;clip-path:polygon(0% 14px,4% 0,8% 14px,12% 0,16% 14px,20% 0,24% 14px,28% 0,32% 14px,36% 0,40% 14px,44% 0,48% 14px,52% 0,56% 14px,60% 0,64% 14px,68% 0,72% 14px,76% 0,80% 14px,84% 0,88% 14px,92% 0,96% 14px,100% 0,100% 100%,0% 100%)}
footer strong{font-size:17px}
footer p{margin:8px 0;color:#52645d}
footer>span{font-size:10px;letter-spacing:2px}
h3,p,a,.topic{overflow-wrap:anywhere}
@media(max-width:640px){
.newsletter{margin:0;border-radius:0}
.cover{padding:28px 24px 0}
.brand{font-size:18px}
h1{letter-spacing:-3px;font-size:64px}
.cover-bottom{grid-template-columns:1fr;gap:22px}
.cover-intro{font-size:22px}
.cover-photo img{height:240px}
.feature-section,.content-section{padding:32px 24px}
.featured,.story,.event.with-image,.events-grid{grid-template-columns:1fr;gap:22px}
.story.reverse.with-image .article-copy{order:0}
.featured h3{font-size:30px}
.story h3{font-size:26px}
.article-photo img{height:240px}
footer{padding:40px 24px 24px}
}
@media print{
body{background:white}
.newsletter{margin:0;box-shadow:none;max-width:none;border-radius:0}
.cover{break-after:page;print-color-adjust:exact}
.story,.event,figure{break-inside:avoid}
footer{print-color-adjust:exact}
}
'''