"""Local prototype authentication; account storage is configurable for deployment."""
import argparse
import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import time

import streamlit as st

ITERATIONS = 600_000
SESSION_SECONDS = 8 * 60 * 60
DEFAULT_ACCOUNTS = Path(__file__).resolve().parent / '.local' / 'accounts.json'


def accounts_path():
    return Path(os.environ.get('NEWSLETTER_ACCOUNTS_FILE', str(DEFAULT_ACCOUNTS))).expanduser()


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), ITERATIONS).hex()
    return f'pbkdf2_sha256${ITERATIONS}${salt}${digest}'


def verify_password(password, encoded):
    try:
        algorithm, rounds, salt, expected = encoded.split('$')
        if algorithm != 'pbkdf2_sha256' or not 100_000 <= int(rounds) <= 2_000_000:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, AttributeError):
        return False


def load_accounts():
    path = accounts_path()
    if not path.exists():
        return {}
    accounts = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(accounts, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in accounts.items()):
        raise ValueError('Invalid account file')
    return accounts


def clear_session():
    for key in list(st.session_state):
        del st.session_state[key]


def require_login():
    try:
        accounts = load_accounts()
    except (OSError, ValueError):
        st.error('The account configuration could not be read. Check the local account file.')
        st.stop()
    user = st.session_state.get('auth_user')
    if user:
        current_hash = accounts.get(user, '')
        if (time.time() - st.session_state.get('auth_started', 0) < SESSION_SECONDS
                and current_hash and hmac.compare_digest(
                    hashlib.sha256(current_hash.encode()).hexdigest(),
                    st.session_state.get('auth_version', ''))):
            with st.sidebar:
                st.caption(f'Signed in as {user}')
                st.button('Log out', on_click=clear_session)
            return
        clear_session()

    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown('### Suomen eOppimiskeskus ry')
        st.title('Welcome back')
        st.write('Sign in to your newsletter workspace.')
        if not accounts:
            st.info('Create your first local account in the terminal, then refresh this page.')
            st.code('.venv/bin/python local_auth.py add-user YOUR_USERNAME', language='bash')
            st.caption('The terminal will ask for a password without displaying it.')
            st.stop()
        with st.form('login', clear_on_submit=True):
            username = st.text_input('Username', key='login_username')
            password = st.text_input('Password', type='password', key='login_password')
            submitted = st.form_submit_button('Sign in', type='primary')
        if submitted:
            now = time.time()
            if now < st.session_state.get('auth_retry_after', 0):
                st.error('Too many attempts. Wait 30 seconds before trying again.')
            else:
                username = username.strip()
                encoded = accounts.get(username)
                # Equal-cost work for unknown accounts as well.
                candidate = encoded or f'pbkdf2_sha256${ITERATIONS}${"00" * 16}${"00" * 32}'
                if verify_password(password, candidate) and encoded:
                    clear_session()
                    st.session_state.auth_user = username
                    st.session_state.auth_started = now
                    st.session_state.auth_version = hashlib.sha256(encoded.encode()).hexdigest()
                    st.rerun()
                else:
                    failures = st.session_state.get('auth_failures', 0) + 1
                    st.session_state.auth_failures = failures
                    if failures >= 5:
                        st.session_state.auth_retry_after = now + 30
                        st.session_state.auth_failures = 0
                    st.error('Incorrect username or password.')
    st.stop()


def main():
    parser = argparse.ArgumentParser(description='Manage local newsletter accounts')
    parser.add_argument('action', choices=['add-user'])
    parser.add_argument('username')
    args = parser.parse_args()
    username = args.username.strip()
    if not username:
        parser.error('Username cannot be empty')
    accounts = load_accounts()
    if username in accounts:
        parser.error('This username already exists; choose another username.')
    password = getpass.getpass('Password (at least 12 characters): ')
    if len(password) < 12:
        parser.error('Use at least 12 characters')
    if password != getpass.getpass('Confirm password: '):
        parser.error('Passwords do not match')
    accounts[username] = hash_password(password)
    path = accounts_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as file:
        json.dump(accounts, file, indent=2)
    temporary.replace(path)
    path.chmod(0o600)
    print(f'Account created for {username}. Refresh the app to sign in.')


if __name__ == '__main__':
    main()
