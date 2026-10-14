"""Small regression checks for safe source filtering and AI response validation."""
import json
import unittest
from unittest.mock import Mock, patch

import newsletter_generator as generator


class CleanupReliabilityTests(unittest.TestCase):
    def test_blocked_domains_match_real_hosts_only(self):
        self.assertTrue(generator.is_blocked_domain('https://www.reddit.com/r/test'))
        self.assertTrue(generator.is_blocked_domain('https://old.reddit.com/r/test'))
        self.assertFalse(generator.is_blocked_domain('https://notreddit.com/article'))
        self.assertFalse(generator.is_blocked_domain('https://reddit.com.evil.example/article'))

    def test_preferred_domain_matches_suffix(self):
        self.assertTrue(generator.is_preferred_domain('https://www.oph.fi/news'))
        self.assertFalse(generator.is_preferred_domain('https://oph.fi.evil.example/news'))

    def test_invalid_ai_fields_do_not_crash_batch(self):
        response = Mock()
        response.json.return_value = {'response': json.dumps({
            'title_en': 'Headline', 'relevance': 7, 'reason': 'Reason',
            'summary': 'Summary', 'topics': []
        })}
        with patch.object(generator.requests, 'post', return_value=response):
            result = generator.analyze_and_summarise('Title', 'Article text')
        self.assertEqual(result['relevance'], 0)
        self.assertEqual(result['summary'], '')

    def test_valid_ai_fields(self):
        response = Mock()
        response.json.return_value = {'response': json.dumps({
            'title_en': 'Headline', 'relevance': 4, 'reason': 'Relevant',
            'summary': 'A factual summary.', 'topics': ['Digital learning']
        })}
        with patch.object(generator.requests, 'post', return_value=response):
            result = generator.analyze_and_summarise('Title', 'Article text')
        self.assertEqual(result['relevance'], 4)
        self.assertEqual(result['summary'], 'A factual summary.')


if __name__ == '__main__':
    unittest.main()
