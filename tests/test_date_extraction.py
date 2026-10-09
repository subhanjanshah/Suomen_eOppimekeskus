import unittest
from datetime import date
from publication_dates import extract_publication_date, combine_evidence, date_evidence


class DateExtractionTests(unittest.TestCase):
    def test_metadata_and_conflict(self):
        html = '''<meta property="article:published_time" content="2026-09-02T00:30:00+03:00">
        <script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2026-09-03"}</script>'''
        result = extract_publication_date(html)
        self.assertEqual(result['date'], date(2026, 9, 2))
        self.assertEqual(result['source'], 'Article metadata')
        self.assertTrue(result['conflict'])

    def test_article_graph_excludes_event_and_related_items(self):
        html = '''<script type="application/ld+json">{"@graph":[
        {"@type":"Event","datePublished":"2026-10-01","startDate":"2026-10-01"},
        {"@type":"ItemList","itemListElement":[{"@type":"Article","datePublished":"2020-01-01"}]},
        {"@type":["Thing","BlogPosting"],"datePublished":"2026-09-12","dateModified":"2026-10-01"}]}</script>'''
        result = extract_publication_date(html)
        self.assertEqual(result['date'], date(2026, 9, 12))
        self.assertFalse(result['conflict'])
        self.assertEqual(len(result['candidates']), 1)

    def test_modified_and_unlabelled_dates_not_used(self):
        html = '''<meta property="article:modified_time" content="2026-10-01">
        <time datetime="2026-09-01">1 September</time><footer>Copyright 2026</footer>'''
        self.assertIsNone(extract_publication_date(html, date(2026, 10, 1))['date'])

    def test_semantic_time_and_malformed_json(self):
        html = '''<script type="application/ld+json">broken</script>
        <time itemprop="datePublished" datetime="2026-09-04">4 September</time>'''
        self.assertEqual(extract_publication_date(html)['date'], date(2026, 9, 4))
        self.assertIsNone(extract_publication_date('<script type="application/ld+json">null</script>')['date'])

    def test_fallback_and_rss_priority(self):
        fallback = extract_publication_date('', date(2026, 9, 7))
        self.assertEqual(fallback['source'], 'Article extractor (fallback)')
        merged = combine_evidence(date_evidence(date(2026, 9, 8), 'RSS publication date'), fallback)
        self.assertEqual(merged['date'], date(2026, 9, 8))
        self.assertTrue(merged['conflict'])
