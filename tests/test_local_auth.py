import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from local_auth import hash_password, verify_password

ROOT = Path(__file__).resolve().parents[1]


class AuthenticationTests(unittest.TestCase):
    def test_password_hash(self):
        encoded = hash_password('test-password-only')
        self.assertTrue(verify_password('test-password-only', encoded))
        self.assertFalse(verify_password('wrong', encoded))
        self.assertFalse(verify_password('anything', 'broken'))
        self.assertNotEqual(encoded, hash_password('test-password-only'))

    def test_login_logout_and_missing_config(self):
        with tempfile.TemporaryDirectory() as directory:
            account_file = Path(directory) / 'accounts.json'
            with patch.dict(os.environ, {'NEWSLETTER_ACCOUNTS_FILE': str(account_file)}):
                app = AppTest.from_file(str(ROOT / 'streamlit_app.py')).run()
                self.assertFalse(app.exception)
                self.assertFalse(any(b.label == 'Generate Draft' for b in app.button))
                account_file.write_text(json.dumps({'editor': hash_password('test-password-only')}))
                app.run()
                app.text_input(key='login_username').set_value('editor')
                app.text_input(key='login_password').set_value('wrong')
                next(b for b in app.button if b.label == 'Sign in').click().run()
                self.assertTrue(app.error)
                self.assertFalse(any(b.label == 'Generate Draft' for b in app.button))
                app.text_input(key='login_username').set_value('editor')
                app.text_input(key='login_password').set_value('test-password-only')
                next(b for b in app.button if b.label == 'Sign in').click().run()
                self.assertFalse(app.exception)
                self.assertTrue(any(b.label == 'Generate Draft' for b in app.button))
                app.session_state['final_html'] = 'private draft'
                next(b for b in app.button if b.label == 'Log out').click().run()
                self.assertFalse(app.exception)
                self.assertNotIn('final_html', app.session_state.filtered_state)
                self.assertFalse(any(b.label == 'Generate Draft' for b in app.button))


if __name__ == '__main__':
    unittest.main()
