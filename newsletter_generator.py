"""
Newsletter Draft Generator
---------------------------
Matches the client's (Finnish e-learning association) actual workflow:
  - They gather info from web pages / social posts about EVENTS and FIELD HIGHLIGHTS
  - They currently post interesting finds to a Telegram channel, then manually
    decide what to include in the newsletter
  - This script automates the "summarize" step: give it a list of links,
    it produces a short, original summary for each (not a copy of the source),
    plus the source link, organized by section (Events / Field Highlights)
  - Uses qwen2.5:7b via Ollama, running fully locally -> no per-request cost

Run locally (requires Ollama running: `ollama serve` in a separate terminal):
    python3 newsletter_generator.py
"""

import json
from pathlib import Path
from urllib.parse import urlparse

import requests
from newspaper import Article
from ddgs import DDGS


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"

# --- Source reliability settings ---

# Sites that are either crowd-edited (Wikipedia), not primary sources, or
# generally not appropriate to cite in a professional newsletter.
# Add/remove domains here as your team decides what counts as reliable.
BLOCKED_DOMAINS = {
    "wikipedia.org",
    "pinterest.com",
    "quora.com",
    "reddit.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "medium.com",  # often personal/unreviewed opinion pieces
}

# Domains/suffixes that get priority when present in search results -
# EU institutions, research bodies, and established European sources.
PREFERRED_DOMAIN_HINTS = [
    ".europa.eu", "cordis.europa.eu", "eurydice", "oecd.org",
    "elearningeuropa.info", ".ac.uk", ".edu",
    ".fi", ".de", ".fr", ".nl", ".se", ".dk", ".no",
]

# The client's own curated list of trusted sources they currently check
# manually (from sources.xlsx, provided directly by the client).
# name -> domain, used to populate a pick-list in the UI so the team can
# select sources instead of typing domains from memory.
CLIENT_TRUSTED_SOURCES = {
    "YLE (Finnish national broadcaster)": "yle.fi",
    "OPH - Finnish National Agency for Education": "oph.fi",
    "Ministry of Education and Culture (Finland)": "minedu.fi",
    "Ministry of Economic Affairs (Finland)": "tem.fi",
    "Theseus - AMK thesis repository": "theseus.fi",
    "Aalto University - News": "aalto.fi",
    "LUT University - News": "lut.fi",
    "HAMK Unlimited Journal": "unlimited.hamk.fi",
    "Aikuiskasvatus (adult education journal)": "aikuiskasvatus.fi",
    "Sitra (Finnish Innovation Fund)": "sitra.fi",
    "Karvi (Finnish Education Evaluation Centre)": "karvi.fi",
    "Association of Finnish Municipalities": "kuntaliitto.fi",
    "Finnish Institute of Occupational Health": "ttl.fi",
    "AOE - Finnish Open Educational Resources": "aoe.fi",
    "UNESCO Institute for Lifelong Learning": "uil.unesco.org",
    "UNICEF Education": "unicef.org",
    "Kopiosto (Finnish copyright org news)": "kopiosto.fi",
    "EDEN - European Distance & E-Learning Network": "eden-europe.eu",
    "ICDE - International Council for Open & Distance Education": "icde.org",
    "ALT - UK Association for Learning Technology": "alt.ac.uk",
    "Fleksibel Utdanning Norge (Norwegian, needs translation)": "fleksibelutdanning.no",
    "Gartner - Learning & Development": "gartner.com",
}

# File used to remember which URLs have already been used, so repeat
# searches for the same topic don't keep surfacing the same old article.
USED_LINKS_FILE = Path("used_links.json")


def ensure_scheme(url):
    """Add https:// to a URL if the person typed it without one
    (e.g. 'yle.fi' -> 'https://yle.fi'). Without this, requests/newspaper3k
    fail with a confusing 'no connection adapters' error."""
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def _get_domain(url):
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def is_blocked_domain(url):
    domain = _get_domain(url)
    return any(blocked in domain for blocked in BLOCKED_DOMAINS)


def is_preferred_domain(url):
    domain = _get_domain(url)
    return any(hint in domain for hint in PREFERRED_DOMAIN_HINTS)


def load_used_links():
    """Load the set of URLs already used in a previous newsletter."""
    if USED_LINKS_FILE.exists():
        try:
            return set(json.loads(USED_LINKS_FILE.read_text()))
        except Exception:
            return set()
    return set()


def mark_links_as_used(urls):
    """Add URLs to the persistent 'already used' memory."""
    used = load_used_links()
    used.update(urls)
    USED_LINKS_FILE.write_text(json.dumps(sorted(used), indent=2))


def clear_used_links():
    """Reset the duplicate-avoidance memory (e.g. for a fresh testing run)."""
    if USED_LINKS_FILE.exists():
        USED_LINKS_FILE.unlink()

# Anti-hallucination, copyright-safe instructions:
# - "in your own words" -> avoids copying source text directly (copyright)
# - "only use facts explicitly stated" -> reduces hallucination risk
# - short length -> keeps it a newsletter blurb, not a reproduction
# - explicit "in English" -> keeps the base summary language consistent
#   regardless of source article language, so translation to Finnish
#   (for the bilingual toggle) always translates FROM a known language.
SUMMARY_INSTRUCTION = (
    "Summarise this in 2-3 sentences, in English, in your own words, "
    "suitable for a newsletter blurb. Only use facts explicitly stated "
    "in the article above. Do not invent names, numbers, or details "
    "that are not in the text. Do not copy sentences directly from the "
    "article - rewrite in your own words."
)

TRANSLATE_INSTRUCTION = (
    "Translate the following newsletter title and summary into Finnish. "
    "Keep the meaning accurate and the tone natural for a newsletter. "
    "Respond in exactly this format, with nothing else before or after:\n"
    "TITLE_FI: <translated title>\n"
    "SUMMARY_FI: <translated summary>"
)

# Static translations for the section labels used in the app (Events /
# Field Highlights). If your team adds new section names, add their
# Finnish equivalent here too - otherwise the English name is reused.
SECTION_TITLE_FI = {
    "Events": "Tapahtumat",
    "Field Highlights": "Alan kohokohdat",
}


def get_article_text(url):
    """Download and extract the readable text of an article from a URL."""
    article = Article(url)
    article.download()
    article.parse()
    return article.title, article.text


def looks_like_homepage_or_section(url):
    """Heuristic: a URL with no real path (e.g. https://yle.fi or
    https://yle.fi/) is almost certainly a homepage/listing page,
    not a single article."""
    path = urlparse(url).path.strip("/")
    return path == ""


def discover_articles_from_source(homepage_url, limit=5):
    """
    Given a site's homepage/section URL (e.g. https://yle.fi), scan it for
    links to individual articles, using newspaper3k's built-in site-crawling
    (newspaper.build). Returns a list of article URLs found on that page.
    """
    from newspaper import build as build_source

    print(f"  {homepage_url} looks like a homepage - scanning for articles...")
    try:
        source = build_source(homepage_url, memoize_articles=False)
        urls = [a.url for a in source.articles]
        print(f"  Found {len(urls)} article links on the page.")
        return urls[:limit]
    except Exception as e:
        print(f"  Could not scan {homepage_url} for articles: {e}")
        return []


def expand_homepage_links(links, limit_per_site=5, avoid_repeats=True):
    """
    Given a mixed list of links, expand any homepage/section URLs into the
    individual article URLs found on them, so the client can paste a site
    like https://yle.fi directly instead of hunting for one specific
    article link themselves. Also applies the same blocklist + duplicate
    filtering used in topic search, for consistency.
    """
    used_links = load_used_links() if avoid_repeats else set()
    expanded = []

    for link in links:
        if looks_like_homepage_or_section(link):
            discovered = discover_articles_from_source(link, limit=limit_per_site)
            for url in discovered:
                if is_blocked_domain(url) or url in used_links:
                    continue
                expanded.append(url)
        else:
            expanded.append(link)

    return expanded


def summarise_with_qwen(title, text):
    """Two-step chat: send article as context, then ask for a summary."""
    # Trim very long articles - smaller local models are less reliable
    # on very long inputs (we saw this cause hallucination in testing)
    max_chars = 6000
    trimmed_text = text[:max_chars]

    messages = [
        {"role": "user", "content": f"Title: {title}\n\nArticle: {trimmed_text}"},
        {"role": "user", "content": SUMMARY_INSTRUCTION},
    ]

    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": messages, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def translate_to_finnish(title_en, summary_en):
    """
    Translate an English title + summary into Finnish, for the bilingual
    newsletter toggle. Returns (title_fi, summary_fi). Falls back to the
    English versions if translation fails or the response can't be parsed,
    so the newsletter still works even if this step has an issue.
    """
    prompt = f"Title: {title_en}\n\nSummary: {summary_en}\n\n{TRANSLATE_INSTRUCTION}"

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        raw = response.json()["message"]["content"].strip()

        title_fi, summary_fi = title_en, summary_en
        for line in raw.splitlines():
            if line.strip().startswith("TITLE_FI:"):
                title_fi = line.split(":", 1)[1].strip()
            elif line.strip().startswith("SUMMARY_FI:"):
                summary_fi = line.split(":", 1)[1].strip()

        return title_fi, summary_fi

    except Exception as e:
        print(f"  Translation to Finnish failed, using English as fallback: {e}")
        return title_en, summary_en


def search_topic_for_links(topic, max_results=5, avoid_repeats=True, restrict_to_site=None):
    """
    Search the web for a topic and return a list of candidate URLs.
    Uses DuckDuckGo via the free `ddgs` library - no API key, no cost.

    Args:
        restrict_to_site: optional domain (e.g. "theseus.fi") to limit
            results to just that site - useful for trusted repositories
            you want to monitor specifically, rather than the open web.

    Applies three filters:
      1. Removes blocked/low-reliability domains (e.g. Wikipedia)
      2. Skips URLs already used in a previous newsletter (if avoid_repeats)
      3. Sorts remaining results so preferred EU/research domains come first

    Note: this only finds *links* (discovery). Downloading + summarising
    each one still uses get_article_text() and summarise_with_qwen() below,
    same as the manual-link workflow.
    """
    query = f"site:{restrict_to_site} {topic}" if restrict_to_site else topic
    print(f"Searching the web for: {query}")

    # Fetch extra results up front since some will get filtered out below.
    fetch_count = max_results * 4

    try:
        results = DDGS().text(query, max_results=fetch_count)
    except Exception as e:
        print(f"  Search failed: {e}")
        return []

    raw_urls = [r["href"] for r in results if r.get("href")]

    used_links = load_used_links() if avoid_repeats else set()

    filtered = []
    for url in raw_urls:
        if is_blocked_domain(url):
            continue
        if url in used_links:
            continue
        filtered.append(url)

    # Preferred (EU/research/edu) domains first, otherwise keep search order.
    filtered.sort(key=lambda u: 0 if is_preferred_domain(u) else 1)

    final_urls = filtered[:max_results]

    skipped_blocked = len(raw_urls) - len([u for u in raw_urls if not is_blocked_domain(u)])
    skipped_repeats = len([u for u in raw_urls if not is_blocked_domain(u) and u in used_links])

    print(f"  Found {len(raw_urls)} raw results -> "
          f"{skipped_blocked} blocked, {skipped_repeats} already used, "
          f"{len(final_urls)} kept.")

    return final_urls


def search_multiple_sites_for_links(topic, sites, max_results_total=5, avoid_repeats=True):
    """
    Search for a topic across several specific trusted sites at once
    (e.g. the client's curated source list), combining and deduplicating
    results. Each site already-used-link filtering applies per site, then
    results are combined and trimmed to max_results_total overall.

    Args:
        sites: list of domains, e.g. ["theseus.fi", "oph.fi"]
    """
    if not sites:
        return search_topic_for_links(topic, max_results=max_results_total, avoid_repeats=avoid_repeats)

    # Split the total budget roughly evenly across the selected sites.
    per_site = max(1, -(-max_results_total // len(sites)))  # ceil division

    combined = []
    seen = set()
    for site in sites:
        site_links = search_topic_for_links(
            topic, max_results=per_site, avoid_repeats=avoid_repeats, restrict_to_site=site
        )
        for url in site_links:
            if url not in seen:
                combined.append(url)
                seen.add(url)

    return combined[:max_results_total]


def build_newsletter_section_from_topic(section_title, topic, max_results=5,
                                         restrict_to_site=None, sites=None):
    """Search for a topic, then build a newsletter section from the results
    (combines discovery + summarisation in one step).

    Provide either `restrict_to_site` (a single domain) or `sites`
    (a list of domains to search across, e.g. the client's trusted list).
    """
    if sites:
        links = search_multiple_sites_for_links(topic, sites, max_results_total=max_results)
    else:
        links = search_topic_for_links(topic, max_results=max_results, restrict_to_site=restrict_to_site)

    # Remember these links immediately, so re-running the same topic later
    # (e.g. next newsletter cycle) surfaces fresh results instead of the
    # same ones - even though the same websites get checked every time.
    if links:
        mark_links_as_used(links)

    return build_newsletter_section(section_title, links)


def build_newsletter_section(section_title, links):
    """Process a list of links into one newsletter section (e.g. 'Events').

    Any link that looks like a homepage/section page (e.g. https://yle.fi)
    is automatically expanded into the individual article links found on
    that page - so pasting a site's homepage works, not just direct
    article URLs.
    """
    print(f"\n--- Processing section: {section_title} ---")

    links = [ensure_scheme(link) for link in links if link.strip()]
    links = expand_homepage_links(links)
    if links:
        mark_links_as_used(links)

    entries = []

    for url in links:
        try:
            print(f"Downloading: {url}")
            title, text = get_article_text(url)

            if not text or len(text) < 200:
                print(f"  Skipped (too little text extracted): {url}")
                continue

            print("  Summarising...")
            summary = summarise_with_qwen(title, text)

            entries.append({
                "title": title,
                "summary": summary,
                "source_url": url,
            })
            print("  Done.")

        except Exception as e:
            print(f"  Failed to process {url}: {e}")

    return {"section_title": section_title, "entries": entries}


def format_newsletter_markdown(sections):
    """Turn the processed sections into a readable draft, ready for human review."""
    lines = ["# Newsletter Draft (AI-generated - please review before sending)\n"]

    for section in sections:
        lines.append(f"## {section['section_title']}\n")
        if not section["entries"]:
            lines.append("_No items processed for this section._\n")
            continue

        for entry in section["entries"]:
            lines.append(f"### {entry['title']}")
            lines.append(entry["summary"])
            lines.append(f"[Read more]({entry['source_url']})\n")

    return "\n".join(lines)


def format_newsletter_html(sections, newsletter_title="Association Newsletter"):
    """
    Turn the processed sections into a styled, bilingual HTML newsletter.

    Each entry may have English fields (title, summary) and, optionally,
    Finnish fields (title_fi, summary_fi) added by translate_to_finnish().
    Both versions are embedded in the same page; a toggle button (top
    right) switches which one is visible via CSS, no page reload needed.
    If Finnish fields are missing on an entry, the English text is used
    for both, so the toggle never shows something blank.
    """

    def entry_html(entry):
        title_fi = entry.get("title_fi") or entry["title"]
        summary_fi = entry.get("summary_fi") or entry["summary"]
        return f"""
        <div class="entry">
          <h3>
            <span class="lang-en">{entry['title']}</span>
            <span class="lang-fi">{title_fi}</span>
          </h3>
          <p>
            <span class="lang-en">{entry['summary']}</span>
            <span class="lang-fi">{summary_fi}</span>
          </p>
          <a class="read-more" href="{entry['source_url']}" target="_blank">
            <span class="lang-en">Read the full source &rarr;</span>
            <span class="lang-fi">Lue koko l&auml;hde &rarr;</span>
          </a>
        </div>"""

    def section_html(section):
        title_fi = SECTION_TITLE_FI.get(section["section_title"], section["section_title"])
        if not section["entries"]:
            body = (
                '<p class="empty">'
                '<span class="lang-en">No items in this section yet.</span>'
                '<span class="lang-fi">Ei kohteita t&auml;ss&auml; osiossa viel&auml;.</span>'
                '</p>'
            )
        else:
            body = "".join(entry_html(e) for e in section["entries"])
        return f"""
      <section>
        <div class="section-label">
          <span class="lang-en">{section['section_title']}</span>
          <span class="lang-fi">{title_fi}</span>
        </div>
        {body}
      </section>"""

    sections_markup = "".join(section_html(s) for s in sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{newsletter_title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Lora:wght@500;600&family=Inter:wght@400;500&display=swap');

  body {{
    margin: 0;
    padding: 48px 20px;
    background: #EFEAE0;
    font-family: 'Inter', sans-serif;
    color: #1F2A24;
  }}

  .newsletter {{
    max-width: 620px;
    margin: 0 auto;
    background: #FBFAF7;
    padding: 48px 44px;
    border: 1px solid #DCD7CA;
    position: relative;
  }}

  .lang-toggle {{
    position: absolute;
    top: 24px;
    right: 24px;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 500;
    background: #FBFAF7;
    color: #2F6F62;
    border: 1px solid #2F6F62;
    border-radius: 999px;
    padding: 6px 14px;
    cursor: pointer;
  }}

  .lang-toggle:hover {{
    background: #2F6F62;
    color: #FBFAF7;
  }}

  /* Language visibility: English shows by default, Finnish hidden,
     JS below flips a class on <body> to swap them. */
  .lang-fi {{ display: none; }}
  body.show-fi .lang-en {{ display: none; }}
  body.show-fi .lang-fi {{ display: inline; }}

  .masthead {{
    text-align: left;
    border-bottom: 2px solid #2F6F62;
    padding-bottom: 20px;
    margin-bottom: 36px;
    padding-right: 90px; /* keep title clear of the toggle button */
  }}

  .masthead h1 {{
    font-family: 'Lora', serif;
    font-weight: 600;
    font-size: 28px;
    margin: 0 0 6px 0;
    color: #1F2A24;
  }}

  .masthead .note {{
    font-size: 13px;
    color: #6B7268;
  }}

  section {{
    margin-bottom: 40px;
  }}

  .section-label {{
    font-family: 'Lora', serif;
    font-size: 15px;
    font-weight: 600;
    color: #C98A3E;
    margin-bottom: 18px;
    padding-bottom: 8px;
    border-bottom: 1px solid #DCD7CA;
  }}

  .entry {{
    margin-bottom: 26px;
  }}

  .entry:last-child {{
    margin-bottom: 0;
  }}

  .entry h3 {{
    font-family: 'Lora', serif;
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: #1F2A24;
    line-height: 1.35;
  }}

  .entry p {{
    font-size: 15px;
    line-height: 1.6;
    margin: 0 0 10px 0;
    color: #2E362F;
  }}

  .read-more {{
    font-size: 13px;
    color: #2F6F62;
    text-decoration: none;
    font-weight: 500;
  }}

  .read-more:hover {{
    text-decoration: underline;
  }}

  .empty {{
    font-size: 14px;
    color: #6B7268;
    font-style: italic;
  }}

  .footer-note {{
    margin-top: 36px;
    padding-top: 20px;
    border-top: 1px solid #DCD7CA;
    font-size: 12px;
    color: #6B7268;
  }}
</style>
</head>
<body>
  <div class="newsletter">
    <button class="lang-toggle" onclick="toggleLanguage()" id="langToggleBtn">FI</button>

    <div class="masthead">
      <h1>{newsletter_title}</h1>
      <div class="note">
        <span class="lang-en">AI-assisted draft &mdash; please review before sending</span>
        <span class="lang-fi">Teko&auml;lyavusteinen luonnos &mdash; tarkista ennen l&auml;hett&auml;mist&auml;</span>
      </div>
    </div>
    {sections_markup}
    <div class="footer-note">
      <span class="lang-en">Summaries generated locally with qwen2.5:7b via Ollama. Each item links back to its original source.</span>
      <span class="lang-fi">Yhteenvedot luotu paikallisesti qwen2.5:7b-mallilla Ollaman kautta. Jokainen kohta linkitt&auml;&auml; alkuper&auml;iseen l&auml;hteeseen.</span>
    </div>
  </div>

  <script>
    function toggleLanguage() {{
      const body = document.body;
      const btn = document.getElementById('langToggleBtn');
      body.classList.toggle('show-fi');
      btn.textContent = body.classList.contains('show-fi') ? 'EN' : 'FI';
    }}
  </script>
</body>
</html>"""


if __name__ == "__main__":
    # --- EDIT THESE: replace with real links your team gathers each cycle ---
    events_links = [
        # "https://example.com/some-upcoming-event",
    ]

    field_highlight_links = [
        "https://www.hamk.fi/julkaisut/opiskeluhyvinvointi-ammattikorkeakoulussa-opiskelijoiden-kokemuksia-voimavaroista-ja-vaatimuksista/",
    ]
    # --------------------------------------------------------------------

    sections = [
        build_newsletter_section("Events", events_links),
        build_newsletter_section("Field Highlights", field_highlight_links),
    ]

    draft = format_newsletter_markdown(sections)

    print("\n\n=== FULL NEWSLETTER DRAFT ===\n")
    print(draft)

    with open("newsletter_draft.md", "w") as f:
        f.write(draft)
    print("\nSaved to newsletter_draft.md - open it, review, and edit before sending.")

    html_draft = format_newsletter_html(sections)
    with open("newsletter_draft.html", "w") as f:
        f.write(html_draft)
    print("Saved to newsletter_draft.html - open this one in a browser to see the visual version.")