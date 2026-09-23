import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import newsletter_generator as generator
from streamlit.testing.v1 import AppTest


class ReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(os.chdir, self.cwd)

    def test_collection_does_not_consume_links(self):
        analysis = {'summary': 'Summary', 'relevance': 4, 'reason': 'Relevant', 'topics': []}
        with patch.object(generator, 'get_article_text', return_value=('Title', 'article ' * 50, '')), \
             patch.object(generator, 'analyze_and_summarise', return_value=analysis), \
             patch.object(generator, 'search_topic_for_links', return_value=['https://example.org/article']), \
             patch.object(generator, 'fetch_rss_entries', return_value=[dict(title='Title', link='https://example.org/rss', description='text', source='example.org')]):
            generator.build_newsletter_section('Events', ['https://example.org/manual'])
            generator.build_newsletter_section_from_topic('Events', 'learning')
            generator.build_newsletter_section_from_rss('Events', ['feed'])
        self.assertEqual(generator.load_used_links(), set())
        with patch.object(generator, 'get_article_text', side_effect=ValueError('download failed')):
            generator.build_newsletter_section('Events', ['https://example.org/failed'])
        self.assertEqual(generator.load_used_links(), set())

    def test_review_export_and_new_batch(self):
        def build(label, links):
            return {'section_title': label, 'entries': [dict(
                title='Article', summary='Original summary', source_url='https://example.org/article',
                relevance=4, reason='Relevant', topics=[]), dict(
                title='Rejected article', summary='Not selected', source_url='https://example.org/rejected',
                relevance=2, reason='Weak connection', topics=[])] if label == 'Events' else []}
        with patch('local_auth.require_login'), \
             patch.object(generator, 'build_newsletter_section', side_effect=build), \
             patch.object(generator, 'translate_to_finnish', return_value=('Otsikko', 'Yhteenveto')):
            app = AppTest.from_file(str(ROOT / 'streamlit_app.py')).run()
            def button(label):
                return next(b for b in app.button if b.label == label)
            button('Generate Draft').click().run()
            self.assertFalse(app.exception)
            self.assertFalse(app.checkbox(key='approve_Events_0').value)
            self.assertTrue(button('Build Final Newsletter').disabled)
            app.checkbox(key='approve_Events_0').check().run()
            button('Prepare Finnish translations').click().run()
            self.assertTrue(button('Build Final Newsletter').disabled)
            app.checkbox(key='fi_review_Events_0').check().run()
            button('Build Final Newsletter').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(generator.load_used_links(), {'https://example.org/article'})
            self.assertIn('Otsikko', app.session_state['final_html'])
            app.run()
            self.assertIn('Otsikko', app.session_state['final_html'])
            app.text_input(key='image_url_Events_0').set_value('https://example.org/photo.jpg').run()
            self.assertNotIn('final_html', app.session_state.filtered_state)
            self.assertFalse(app.checkbox(key='image_ok_Events_0').value)
            app.checkbox(key='image_ok_Events_0').check().run()
            button('Build Final Newsletter').click().run()
            self.assertEqual(app.session_state['final_html'].count('<img'), 2)
            app.text_input(key='image_url_Events_0').set_value('https://example.org/replacement.jpg').run()
            self.assertFalse(app.checkbox(key='image_ok_Events_0').value)
            self.assertNotIn('final_html', app.session_state.filtered_state)
            app.text_input(key='design_topics').set_value('Oppiminen, Tekoäly').run()
            self.assertNotIn('final_html', app.session_state.filtered_state)
            button('Build Final Newsletter').click().run()
            self.assertIn('Oppiminen', app.session_state['final_html'])
            app.text_area(key='fi_summary_Events_0').set_value('Edited Finnish').run()
            self.assertFalse(app.checkbox(key='fi_review_Events_0').value)
            self.assertTrue(button('Build Final Newsletter').disabled)
            self.assertNotIn('final_html', app.session_state.filtered_state)
            app.text_area(key='summary_Events_0').set_value('Changed English').run()
            self.assertTrue(button('Build Final Newsletter').disabled)
            button('Prepare Finnish translations').click().run()
            self.assertFalse(app.checkbox(key='fi_review_Events_0').value)
            button('Generate Draft').click().run()
            self.assertFalse(app.exception)
            self.assertFalse(app.checkbox(key='approve_Events_0').value)
            self.assertEqual(app.text_area(key='summary_Events_0').value, 'Original summary')
            self.assertNotIn('final_html', app.session_state.filtered_state)


if __name__ == '__main__':
    unittest.main()
