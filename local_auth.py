
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
from urllib.parse import urlparse

import streamlit as st
from app_style import login_brand

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


def save_accounts(accounts):
    """Persist password hashes in the existing private local account store."""
    path = accounts_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as file:
        json.dump(accounts, file, indent=2)
    temporary.replace(path)
    path.chmod(0o600)


def local_setup_allowed():
    """Do not expose unauthenticated first-user signup on a public deployment."""
    try:
        host = (urlparse(st.context.url).hostname or '').lower()
        return host in ('localhost', '127.0.0.1', '::1')
    except (AttributeError, ValueError):
        return False


def valid_new_user(username, password, confirmation, accounts):
    if not username or len(username) > 40 or not all(c.isalnum() or c in '_-' for c in username):
        return 'Use a username of 1–40 letters, numbers, underscores or hyphens.'
    if username in accounts:
        return 'This username already exists.'
    if len(password) < 12:
        return 'Password must be at least 12 characters.'
    if password != confirmation:
        return 'Passwords do not match.'
    return None


def create_account_form(accounts, form_key, first=False):
    with st.form(form_key, clear_on_submit=True):
        username = st.text_input('New username', key=f'{form_key}_username')
        password = st.text_input('New password (12+ characters)', type='password', key=f'{form_key}_password')
        confirmation = st.text_input('Confirm password', type='password', key=f'{form_key}_confirm')
        submitted = st.form_submit_button('Create account', type='primary')
    if submitted:
        username = username.strip()
        error = valid_new_user(username, password, confirmation, accounts)
        if error:
            st.error(error)
            return
        latest = load_accounts()
        if latest and first:
            st.error('An account was already created. Refresh and sign in.')
            return
        if username in latest:
            st.error('This username already exists.')
            return
        latest[username] = hash_password(password)
        try:
            save_accounts(latest)
        except OSError:
            st.error('Could not save the account. Check folder permissions.')
            return
        st.success('Account created. You can now sign in.' if first else f'Account created for {username}.')
        if first:
            st.rerun()


def is_admin(username, accounts=None):
    """For the existing account format, the first stored user is the administrator."""
    if accounts is None:
        accounts = load_accounts()
    return bool(accounts) and username == next(iter(accounts))


def render_account_management():
    """Administrator-only account overview and creation page."""
    accounts = load_accounts()
    current_user = st.session_state.get('auth_user')
    if not is_admin(current_user, accounts):
        st.error('Only the administrator can manage accounts.')
        st.stop()

    st.markdown('<div class="brand-kicker">Suomen eOppimiskeskus ry / Administration</div>', unsafe_allow_html=True)
    st.title('Manage accounts')
    st.write('View everyone who can sign in and create accounts for colleagues.')
    st.subheader(f'Accounts ({len(accounts)})')
    st.dataframe(
        [{'Username': username,
          'Role': 'Administrator' if is_admin(username, accounts) else 'User',
          'Current account': 'Yes' if username == current_user else ''}
         for username in accounts],
        hide_index=True,
        use_container_width=True,
    )
    st.caption('The first account created is the administrator. Passwords are never displayed.')
    st.divider()
    st.subheader('Create a new account')
    create_account_form(accounts, 'admin_page_create_user')


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
                if is_admin(user, accounts):
                    st.caption('Role: Administrator')
                else:
                    st.caption('Role: User')
            return
        clear_session()

    with st.container(key='login_shell'):
        brand, center = st.columns([1, 1.12], gap='small')
        with brand:
            login_brand()
        with center:
            card = st.container(key='login_card')
    with card:
        st.markdown('<div class="brand-kicker">Your editorial space</div>', unsafe_allow_html=True)
        st.title('Welcome back')
        st.write('Sign in to bring your next issue to life.')
        if not accounts:
            if local_setup_allowed():
                st.info('First time here? Create your administrator account below.')
                create_account_form(accounts, 'initial_setup', first=True)
            else:
                st.warning('Initial account setup is available only on localhost. Set up the first account locally before deploying this app.')
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
    save_accounts(accounts)
    print(f'Account created for {username}. Refresh the app to sign in.')


if __name__ == '__main__':
    main()
