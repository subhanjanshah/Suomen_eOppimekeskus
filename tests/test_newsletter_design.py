import unittest
from newsletter_design import format_newsletter_html
from unittest.mock import patch
import newsletter_generator as generator


class DesignTests(unittest.TestCase):
    def test_article_image_extraction(self):
        with patch.object(generator, 'Article') as article:
            article.return_value.title = 'Title'
            article.return_value.text = 'Text'
            article.return_value.top_image = 'https://example.org/photo.jpg'
            self.assertEqual(generator.get_article_text('https://example.org'), ('Title', 'Text'))
            self.assertEqual(generator.get_article_text('https://example.org', include_image=True),
                             ('Title', 'Text', 'https://example.org/photo.jpg'))

    def test_images_escaping_and_empty_sections(self):
        entry = dict(title='<script>bad</script>', summary='A & B', source_url='javascript:bad',
                     image_url='https://example.org/image.jpg', image_approved=False,
                     topics=['Learning'], title_fi='Oppiminen')
        sections = [dict(section_title='Events', entries=[]),
                    dict(section_title='Field Highlights', entries=[entry])]
        html = format_newsletter_html(sections)
        self.assertNotIn('<script>bad</script>', html)
        self.assertNotIn('javascript:bad', html)
        self.assertNotIn('<img', html)
        self.assertNotIn('>Events<', html)
        self.assertIn('Oppiminen', html)
        entry.update(image_approved=True, image_credit='Photo credit')
        html = format_newsletter_html(sections)
        self.assertEqual(html.count('<img'), 2)
        self.assertIn('Photo credit', html)
        entry['image_url'] = 'javascript:bad'
        self.assertNotIn('<img', format_newsletter_html(sections))

    def test_feature_and_alternating_rows(self):
        entries = [dict(title=f'Story {i}', summary='Summary', source_url=f'https://example.org/{i}',
                        image_url='https://example.org/photo.jpg', image_approved=True) for i in range(4)]
        html = format_newsletter_html([dict(section_title='Field Highlights', entries=entries)],
                                     featured_url=entries[2]['source_url'], cover_topics=['AI', 'Education'])
        self.assertEqual(html.count('Story 2</span>'), 2)  # English + Finnish fallback, one story
        self.assertIn('story with-image reverse', html)
        self.assertIn('class="topic">AI', html)


if __name__ == '__main__':
    unittest.main()
