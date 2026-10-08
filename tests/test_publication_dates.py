from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import newsletter_generator as g
from publication_dates import publication_date, exclusion_reason

START = date(2026, 9, 1)
END = date(2026, 9, 30)
ANALYSIS = dict(summary='Summary', relevance=4, reason='Relevant', topics=[])


class PublicationTests(TestCase):
    def test_parsing_and_boundaries(self):
        self.assertEqual(publication_date('2026-09-01T00:30:00+03:00'), START)
        self.assertEqual(publication_date('Tue, 01 Sep 2026 12:00:00 GMT'), START)
        self.assertIsNone(publication_date('not a date'))
        for day in (START, END):
            self.assertIsNone(exclusion_reason(day, START, END, False))
        self.assertEqual(exclusion_reason(date(2026, 8, 31), START, END), 'outside_range')
        self.assertEqual(exclusion_reason(date(2026, 10, 1), START, END), 'outside_range')
        self.assertEqual(exclusion_reason(None, START, END, False), 'unknown_date')
        self.assertIsNone(exclusion_reason(None, START, END, True))
        with self.assertRaises(ValueError):
            exclusion_reason(START, END, START)

    def test_manual_filter_before_ai(self):
        articles = [('Title', 'text ' * 60, '', day) for day in
                    (date(2026, 8, 31), START, END, None)]
        with patch.object(g, 'get_article_text', side_effect=articles), \
             patch.object(g, 'analyze_and_summarise', return_value=ANALYSIS) as ai:
            result = g.build_newsletter_section('Events', [f'https://example.org/{i}' for i in range(4)],
                                                start_date=START, end_date=END, include_undated=False)
        self.assertEqual(ai.call_count, 2)
        self.assertEqual(result['date_excluded'], dict(outside_range=1, unknown_date=1))
        self.assertEqual([e['published_date'] for e in result['entries']], ['2026-09-01', '2026-09-30'])

    def test_rss_date_survives_scraping_failure(self):
        entries = [dict(title='Title', link=f'https://example.org/{i}', source='example.org',
                        description='Feed summary ' * 20, published_date=day)
                   for i, day in enumerate((date(2026, 8, 1), START, None))]
        with patch.object(g, 'fetch_rss_entries', return_value=entries), \
             patch.object(g, 'get_article_text', side_effect=ValueError('blocked')) as fetch, \
             patch.object(g, 'analyze_and_summarise', return_value=ANALYSIS) as ai:
            result = g.build_newsletter_section_from_rss('Events', ['feed'], start_date=START,
                                                         end_date=END, include_undated=False)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(ai.call_count, 1)
        self.assertEqual(result['entries'][0]['published_date'], '2026-09-01')

    def test_feed_publication_not_updated_date(self):
        feed = SimpleNamespace(entries=[dict(link='https://example.org/item',
                               published='Tue, 01 Sep 2026 12:00:00 GMT'),
                               dict(link='https://example.org/updated', updated='2026-09-30')], bozo=False)
        with patch('feedparser.parse', return_value=feed), patch.object(g, 'load_used_links', return_value=set()):
            results = g.fetch_rss_entries(['feed'])
        self.assertEqual(results[0]['published_date'], START)
        self.assertIsNone(results[1]['published_date'])

    def test_topic_passes_date_options(self):
        with patch.object(g, 'search_topic_for_links', return_value=['https://example.org/article']), \
             patch.object(g, 'build_newsletter_section', return_value={}) as build:
            g.build_newsletter_section_from_topic('Events', 'education', start_date=START,
                                                  end_date=END, include_undated=False)
        self.assertEqual(build.call_args.kwargs, dict(start_date=START, end_date=END, include_undated=False))

    def test_calendar_validation_and_changed_settings(self):
        with patch('local_auth.require_login'), patch.object(g, 'build_newsletter_section',
             return_value=dict(section_title='Events', entries=[])) as build:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit_app.py')).run()
            app.checkbox(key='filter_dates').check().run()
            app.date_input(key='published_from').set_value(END)
            app.date_input(key='published_through').set_value(START).run()
            generate = lambda: next(b for b in app.button if b.label == 'Generate Draft')
            self.assertTrue(generate().disabled)
            app.date_input(key='published_from').set_value(START)
            app.date_input(key='published_through').set_value(END).run()
            generate().click().run()
            self.assertFalse(app.exception)
            self.assertEqual(build.call_args.kwargs, dict(start_date=START, end_date=END, include_undated=False))
            app.checkbox(key='filter_dates').uncheck().run()
            self.assertTrue(any('Date settings changed' in w.value for w in app.warning))
