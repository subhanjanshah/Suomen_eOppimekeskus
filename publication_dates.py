"""Publication calendar dates; retain the source's calendar day, not an event date."""
from datetime import date, datetime
from email.utils import parsedate_to_datetime


def publication_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).date()
    except ValueError:
        try:
            return parsedate_to_datetime(value).date()
        except (ValueError, TypeError, OverflowError):
            return None


def validate_range(start_date, end_date):
    if start_date and end_date and start_date > end_date:
        raise ValueError('The start date must be on or before the end date.')


def exclusion_reason(published, start_date=None, end_date=None, include_undated=True):
    validate_range(start_date, end_date)
    if not start_date and not end_date:
        return None
    if published is None:
        return None if include_undated else 'unknown_date'
    if (start_date and published < start_date) or (end_date and published > end_date):
        return 'outside_range'
    return None


def date_evidence(value, source='Article extractor'):
    """Accept either extraction evidence or the legacy date-only result."""
    if isinstance(value, dict):
        return value
    day = publication_date(value)
    return {'date': day, 'source': source if day else 'Unknown', 'candidates': (
        [{'date': day.isoformat(), 'source': source}] if day else []), 'conflict': False}


def combine_evidence(primary, secondary):
    primary, secondary = date_evidence(primary), date_evidence(secondary)
    chosen = primary if primary['date'] else secondary
    candidates = primary['candidates'] + secondary['candidates']
    return dict(chosen, candidates=candidates,
                conflict=len({item['date'] for item in candidates}) > 1)


def extract_publication_date(html, fallback=None):
    """Read explicitly published dates without another network request.

    Only article JSON-LD nodes at the document/graph/mainEntity level qualify;
    dates from events and related-story ItemLists are deliberately ignored.
    """
    import json
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html if isinstance(html, str) else '', 'html.parser')
    candidates = []

    def add(value, source):
        day = publication_date(value)
        if day:
            item = {'date': day.isoformat(), 'source': source}
            if item not in candidates:
                candidates.append(item)

    published_keys = {'article:published_time', 'og:published_time', 'datepublished',
                      'pubdate', 'publishdate', 'publication_date', 'parsely-pub-date',
                      'dc.date.issued', 'dcterms.issued', 'citation_publication_date'}
    modified_values = []
    for meta in soup.find_all('meta'):
        key = str(meta.get('property') or meta.get('name') or meta.get('itemprop') or '').lower()
        if key in published_keys:
            add(meta.get('content'), 'Article metadata')
        elif key in {'article:modified_time', 'datemodified', 'og:updated_time'}:
            modified_values.append(meta.get('content'))

    def nodes(value):
        if isinstance(value, list):
            for child in value:
                yield from nodes(child)
        elif isinstance(value, dict):
            yield value
            for key in ('@graph', 'mainEntity'):
                yield from nodes(value.get(key))

    types = {'Article', 'NewsArticle', 'BlogPosting', 'ScholarlyArticle', 'Report', 'TechArticle'}
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue
        for node in nodes(data):
            kind = node.get('@type', [])
            if isinstance(kind, str):
                kind = [kind]
            if not isinstance(kind, list) or not any(str(k).rsplit('/', 1)[-1] in types for k in kind):
                continue
            add(node.get('datePublished'), 'Article JSON-LD')
            modified_values.append(node.get('dateModified'))

    for element in soup.select('[itemprop="datePublished"], time[pubdate]'):
        if not element.find_parent(['nav', 'footer', 'aside']):
            add(element.get('content') or element.get('datetime') or element.get_text(strip=True),
                'Publication time element')

    # Do not let a library's inferred update date become a publication date.
    if not candidates and publication_date(fallback) not in {
            publication_date(v) for v in modified_values if publication_date(v)}:
        add(fallback, 'Article extractor (fallback)')
    chosen = candidates[0] if candidates else None
    return {'date': publication_date(chosen['date']) if chosen else None,
            'source': chosen['source'] if chosen else 'Unknown', 'candidates': candidates,
            'conflict': len({item['date'] for item in candidates}) > 1}
