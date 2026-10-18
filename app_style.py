"""Shared visual skin. Native Streamlit widgets retain their behaviour.

Redesign notes (Oct 2026): the previous version had grown three overlapping
layers of overrides for the same selectors (h1/h2/h3, .workflow-strip,
.section-eyebrow, ...), each with a different size, which is why text looked
inconsistent across the app. This version defines every selector exactly
once. Theme colours still come from one `palette` dict so light/dark mode
stay in sync.
"""
import streamlit as st


def apply_style(dark=False):
    # Structural / layout rules that don't depend on the colour theme.
    st.markdown('''<style>
:root {color-scheme:light;}
*{box-sizing:border-box;}
[data-testid="stApp"] {font-family:Arial,Helvetica,sans-serif;}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stMainBlockContainer"] {max-width:1120px;padding:1.75rem 2.25rem 4rem;}

/* ---- Type scale: defined once, used everywhere ---- */
[data-testid="stApp"] h1,[data-testid="stApp"] h2,[data-testid="stApp"] h3 {letter-spacing:-.03em;font-weight:700;margin:0;}
[data-testid="stApp"] h1 {font-size:clamp(1.9rem,3vw,2.5rem);font-weight:760;line-height:1.15;margin-bottom:.4rem;}
[data-testid="stApp"] h2 {font-size:1.3rem;font-weight:700;}
[data-testid="stApp"] h3 {font-size:1.05rem;font-weight:700;}
[data-testid="stWidgetLabel"] p {font-size:.85rem;font-weight:600;}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea {font-size:14.5px!important;}

[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stTextInput"] [data-baseweb="base-input"],
[data-testid="stTextArea"] [data-baseweb="textarea"] {border-radius:10px;}
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
[data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within {box-shadow:0 0 0 3px #24634f1f;}
[data-testid="stApp"] button[kind="primary"],
[data-testid="stApp"] [data-testid="stBaseButton-primaryFormSubmit"] {border-radius:9px;min-height:44px;font-weight:650;font-size:14px;}
[data-testid="stApp"] button[kind="secondary"] {border-radius:9px;font-size:14px;}
[data-testid="stApp"] button:focus-visible {outline:3px solid #bd813a;outline-offset:3px;}
[data-testid="stApp"] [data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;}
[data-testid="stApp"] button[kind="primary"] [data-testid="stMarkdownContainer"] p,
[data-testid="stApp"] [data-testid="stBaseButton-primaryFormSubmit"] [data-testid="stMarkdownContainer"] p {color:#fff!important;}

/* ---- Page header: breadcrumb + title + step strip ---- */
.brand-kicker {display:inline-flex;align-items:center;gap:7px;font-size:11.5px;letter-spacing:1.4px;text-transform:uppercase;font-weight:720;margin:0 0 16px;padding:6px 14px 6px 11px;border-radius:30px;}
.brand-kicker::before {content:"";width:6px;height:6px;border-radius:50%;flex-shrink:0;}
.workspace-intro {max-width:640px;margin:0 0 26px;font-size:14.5px;line-height:1.6;}

.workflow-strip {display:flex;gap:0;margin:4px 0 32px;padding:0;list-style:none;border-bottom:1px solid;}
.workflow-strip a {flex:1;display:flex;align-items:center;gap:9px;padding:0 10px 14px;text-decoration:none!important;font-size:12.5px;font-weight:650;white-space:nowrap;border-bottom:2px solid transparent;margin-bottom:-1px;}
.workflow-strip span {width:22px;height:22px;flex-shrink:0;display:inline-grid;place-items:center;border-radius:50%;font-size:10px;font-weight:700;margin:0!important;}

/* ---- Section labels inside the main form ---- */
.section-eyebrow {font-size:10.5px;letter-spacing:1.6px;text-transform:uppercase;font-weight:720;margin:28px 0 6px;}
.section-eyebrow:first-of-type {margin-top:0;}
.section-heading {font-size:1.2rem;font-weight:720;letter-spacing:-.03em;margin:0 0 14px;}

/* ---- Login screen ---- */
.st-key-login_shell {max-width:1040px;margin:6vh auto;border-radius:22px;overflow:hidden;box-shadow:0 22px 70px #203d3514;}
.st-key-login_shell [data-testid="stHorizontalBlock"] {gap:0;align-items:stretch;}
.st-key-login_shell [data-testid="stColumn"]:first-child {background:#173f35;}
.login-brand {padding:52px 42px;color:#f6f4eb;min-height:520px;display:flex;flex-direction:column;justify-content:space-between;}
.login-brand .wordmark {font-size:20px;font-weight:700;letter-spacing:-.6px;line-height:1.4;max-width:260px;}
.login-brand .brand-label {font-size:10px;letter-spacing:2.4px;text-transform:uppercase;color:#e4bb84;margin-bottom:18px;}
.login-brand .brand-headline {font-family:Georgia,serif;font-size:44px;font-weight:400;line-height:1.12;letter-spacing:-1.3px;margin:0 0 20px;}
.login-brand .brand-description {font-size:13.5px;line-height:1.75;color:#d2dfd3;max-width:300px;}
.login-brand .brand-footer {border-top:1px solid #ffffff30;padding-top:18px;font-size:10.5px;color:#d2dfd3;letter-spacing:.3px;}
.st-key-login_card {padding:46px 44px;}
.st-key-login_card h1 {font-size:2.1rem!important;margin:4px 0 6px!important;}
.st-key-login_card [data-testid="stForm"] {border:0;padding:12px 0 0;}
.st-key-login_card [data-testid="stFormSubmitButton"] button {width:100%;margin-top:10px;}
.st-key-login_card [data-testid="stTextInput"] input {min-height:46px;}

@media(max-width:760px){
  [data-testid="stMainBlockContainer"]{padding:1.2rem 1rem 3rem;}
  .st-key-login_shell{margin:0 auto;}
  .st-key-login_shell [data-testid="stHorizontalBlock"]{flex-direction:column;}
  .st-key-login_shell [data-testid="stColumn"]{width:100%!important;flex:1 1 auto!important;}
  .login-brand{padding:28px;min-height:0;gap:24px;}
  .login-brand .brand-headline{font-size:32px;}
  .login-brand .brand-description,.login-brand .brand-footer{display:none;}
  .st-key-login_card{padding:26px;}
  .workflow-strip{overflow-x:auto;}
}
</style>''', unsafe_allow_html=True)

    # Colour theme. Every colour-bearing rule lives here so light/dark stay
    # in sync; the structural block above never hardcodes a theme colour.
    palette = (
        {"bg": "#181d1a", "side": "#202822", "surface": "#252e28", "field": "#2b352e",
         "text": "#e9ede6", "muted": "#c6d3c8", "border": "#3e4b40", "accent": "#a8c7aa",
         "accent_text": "#17251a", "hover": "#303d33", "card": "#252e28"}
        if dark else
        {"bg": "#f5f3ed", "side": "#e9eee5", "surface": "#ffffff", "field": "#ffffff",
         "text": "#203d35", "muted": "#4c6055", "border": "#d8e0d4", "accent": "#24634f",
         "accent_text": "#ffffff", "hover": "#e1e9dd", "card": "#ffffff"}
    )
    css = """
    <style>
    :root { color-scheme: THEME_SCHEME; }
    [data-testid="stApp"], [data-testid="stAppViewContainer"] {background: BG!important;color: TEXT!important;}
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {background: SIDE!important;color: TEXT!important;}
    [data-testid="stSidebar"] {border-right:1px solid BORDER!important;min-width:272px!important;max-width:292px!important;}
    [data-testid="stSidebarUserContent"] {padding:0 1.1rem 1.4rem!important;}

    [data-testid="stApp"] h1,[data-testid="stApp"] h2,[data-testid="stApp"] h3,
    [data-testid="stApp"] p,[data-testid="stApp"] label,
    [data-testid="stApp"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] p {color:TEXT;}

    /* Accessible contrast for captions and helper text. */
    [data-testid="stApp"] [data-testid="stCaptionContainer"],
    [data-testid="stApp"] [data-testid="stCaptionContainer"] p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
    [data-testid="stApp"] [data-testid="stWidgetLabel"] small,
    [data-testid="stApp"] [data-testid="stMarkdownContainer"] small,
    [data-testid="stApp"] [data-testid="stAlert"] p,
    .workspace-intro {color:MUTED!important;opacity:1!important;}

    [data-testid="stApp"] [data-testid="stTextInput"] input,
    [data-testid="stApp"] [data-testid="stTextArea"] textarea,
    [data-testid="stApp"] [data-baseweb="select"] > div,
    [data-testid="stApp"] [data-baseweb="input"],
    [data-testid="stApp"] [data-baseweb="textarea"] {background:FIELD!important;color:TEXT!important;border-color:BORDER!important;caret-color:ACCENT;}
    [data-testid="stApp"] input::placeholder,[data-testid="stApp"] textarea::placeholder {color:MUTED!important;}

    [data-testid="stApp"] button[kind="primary"],
    [data-testid="stApp"] [data-testid="stBaseButton-primaryFormSubmit"] {background:ACCENT!important;border-color:ACCENT!important;}
    [data-testid="stApp"] button[kind="primary"]:hover,
    [data-testid="stApp"] [data-testid="stBaseButton-primaryFormSubmit"]:hover {filter:brightness(.93);}
    [data-testid="stApp"] button[kind="primary"] p,
    [data-testid="stApp"] [data-testid="stBaseButton-primaryFormSubmit"] p {color:ACCENT_TEXT!important;}
    [data-testid="stApp"] button[kind="secondary"] {background:SURFACE!important;border-color:BORDER!important;color:TEXT!important;}
    [data-testid="stApp"] button[kind="secondary"] p {color:TEXT!important;}

    [data-testid="stApp"] [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stApp"] [data-testid="stExpander"],
    [data-testid="stApp"] [data-testid="stForm"] {border-color:BORDER!important;}
    [data-testid="stMain"] [data-testid="stExpander"] {background:SURFACE!important;border-radius:10px!important;}
    [data-testid="stMain"] [data-testid="stTextInput"] input {min-height:42px!important;}
    [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] {gap:8px;}
    [data-testid="stMain"] [data-testid="stRadio"] label {border:1px solid BORDER;border-radius:9px;padding:9px 13px;background:SURFACE;font-size:12.5px!important;}
    [data-testid="stMain"] [data-testid="stRadio"] label:has(input:checked) {border-color:ACCENT;background:HOVER;}
    [data-testid="stApp"] [data-testid="stTabs"] [role="tablist"] {gap:10px;border-bottom:1px solid BORDER;}
    [data-testid="stApp"] [data-testid="stTabs"] button[role="tab"] {font-weight:650;font-size:13px;padding:10px 16px;}

    /* Breadcrumb kicker + step strip, tied to the accent colour. */
    .brand-kicker {color:ACCENT;background:HOVER;}
    .brand-kicker::before {background:ACCENT;}
    .workflow-strip {border-bottom-color:BORDER;}
    .workflow-strip a {color:MUTED;}
    .workflow-strip span {background:HOVER;color:MUTED;}
    .workflow-strip a:first-child {color:TEXT;border-bottom-color:ACCENT;}
    .workflow-strip a:first-child span {background:ACCENT;color:ACCENT_TEXT;}
    .section-eyebrow {color:MUTED;}
    .section-heading {color:TEXT;}

    /* Login screen */
    .st-key-login_shell {background:SURFACE!important;border:1px solid BORDER;}
    .st-key-login_card {background:SURFACE!important;}
    .st-key-login_card [data-testid="stMarkdownContainer"] p {color:MUTED!important;}

    /* ---- Sidebar brand lockup ---- */
    .sidebar-brand {display:flex;align-items:center;gap:12px;padding:2px 2px 20px;margin:-40px 0 16px;border-bottom:1px solid BORDER;}
    .sidebar-brand-mark {display:grid;grid-template-columns:repeat(2,9px);grid-template-rows:repeat(2,9px);gap:3px;width:38px;height:38px;align-content:center;justify-content:center;background:#204e42;border-radius:10px;flex-shrink:0;transform:rotate(-4deg);}
    .sidebar-brand-mark span {display:block;border-radius:2px;background:#f5f3ed;}
    .sidebar-brand-mark span:nth-child(2) {opacity:.45;}
    .sidebar-brand-mark span:nth-child(3) {opacity:.65;}
    .sidebar-brand-copy {min-width:0;}
    .sidebar-brand-name {font-size:18px;font-weight:750;letter-spacing:-.6px;line-height:1.1;color:TEXT;white-space:nowrap;}
    .sidebar-brand-name span {display:block;}
    .sidebar-brand-tagline {font-size:9.5px;font-weight:720;letter-spacing:1.5px;color:MUTED;margin-top:6px;}

    .sidebar-nav-caption {font-size:11.5px;letter-spacing:1.3px;text-transform:uppercase;font-weight:750;color:MUTED;margin:0 0 10px 2px;}
    .memory-heading {font-size:10px;letter-spacing:1.5px;text-transform:uppercase;font-weight:720;color:MUTED;margin:18px 0 8px 2px;}

    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {gap:3px;}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {padding:9px 11px;border:1px solid transparent;border-radius:8px;background:transparent;transition:background .15s,box-shadow .15s;}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {background:HOVER;}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {background:HOVER;box-shadow:inset 3px 0 ACCENT;}
    [data-testid="stSidebar"] [data-testid="stRadio"] label p {font-size:13.5px!important;font-weight:650!important;color:TEXT!important;}
    [data-testid="stSidebar"] [data-testid="stRadio"] label [data-testid="stMarkdownContainer"] {flex:1;}
    .sidebar-only-page {padding:10px 12px;border-left:3px solid ACCENT;border-radius:7px;background:HOVER;color:TEXT;font-weight:650;font-size:13.5px;}

    [data-testid="stSidebar"] [data-testid="stExpander"] {background:transparent!important;border:1px solid BORDER!important;border-radius:10px!important;margin-top:16px!important;}
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {font-size:12.5px!important;padding:8px 10px!important;}
    .past-links-heading {display:none;}
    .past-link {display:flex;flex-direction:column;gap:1px;background:transparent;border-bottom:1px solid BORDER;padding:7px 3px;margin:0;text-decoration:none!important;min-width:0;}
    .past-link:hover {background:HOVER;}
    .past-link-domain {font-size:12.5px;font-weight:650;color:TEXT;overflow-wrap:anywhere;}
    .past-link-url {font-size:10.5px;color:MUTED;overflow-wrap:anywhere;line-height:1.25;max-height:1.25em;overflow:hidden;}

    /* Stretch the sidebar content column to viewport height so the theme
       toggle sits pinned at the bottom, with link history scrollable above
       it. Streamlit nests vertical-block wrappers, hence the chain below. */
    [data-testid="stSidebarUserContent"] {min-height:calc(100dvh - 3rem);display:flex;flex-direction:column;}
    [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] {flex:1;display:flex;flex-direction:column;min-height:calc(100dvh - 3rem);}
    [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {flex:1;display:flex;flex-direction:column;}
    [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {flex:1;display:flex;flex-direction:column;}
    [data-testid="stSidebar"] .st-key-sidebar_bottom_spacer {flex:1 1 auto;min-height:20px;}

    /* Two distinct footer blocks (each with its own divider), placed
       right after the flexible spacer above so both sit at the very
       bottom of the sidebar: the account card, then appearance. */
    [data-testid="stSidebar"] .st-key-sidebar_account {border-top:1px solid BORDER;padding:16px 2px 14px;}
    [data-testid="stSidebar"] .st-key-theme_toggle_panel {border-top:1px solid BORDER;margin-top:4px;padding:14px 2px 4px;}
    .st-key-theme_toggle_panel label p {font-weight:650!important;font-size:13px!important;color:TEXT!important;}

    .st-key-sidebar_account [data-testid="stMarkdownContainer"] {display:block;}
    .account-row {display:flex;align-items:center;gap:10px;margin-bottom:11px;line-height:1;}
    .account-avatar {width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12.5px;line-height:1;font-weight:750;flex-shrink:0;background:ACCENT;color:ACCENT_TEXT;}
    .account-copy {min-width:0;display:flex;flex-direction:column;justify-content:center;gap:5px;}
    .account-name {font-size:13px;line-height:1.1;font-weight:650;color:TEXT;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:168px;}
    .account-role {display:inline-block;width:fit-content;font-size:9px;line-height:1.3;font-weight:720;letter-spacing:.5px;text-transform:uppercase;color:ACCENT;background:HOVER;padding:2px 7px;border-radius:20px;}
    .st-key-sidebar_account [data-testid="stButton"] button {min-height:32px!important;font-size:12px!important;padding:5px 10px!important;}

    @media(max-width:760px){
      .workflow-strip a{font-size:11.5px!important;}
      .workflow-strip span{width:20px;height:20px;}
    }
    </style>
    """
    # Longest keys first, so "accent_text" is substituted before the shorter
    # "accent" token inside it gets replaced out from under it.
    for key, value in sorted(palette.items(), key=lambda kv: -len(kv[0])):
        css = css.replace(key.upper(), value)
    css = css.replace("THEME_SCHEME", "dark" if dark else "light")
    st.markdown(css, unsafe_allow_html=True)


def login_brand():
    st.markdown('''<div class="login-brand"><div class="wordmark">Suomen<br>eOppimiskeskus ry</div>
<div><div class="brand-label">The newsletter workspace</div><div class="brand-headline">Good ideas.<br>Shared together.</div>
<div class="brand-description">A little less searching. More time for the stories that matter to your learning community.</div></div>
<div class="brand-footer">Discover · Curate · Share</div></div>''', unsafe_allow_html=True)


def workspace_header():
    st.markdown('<div class="brand-kicker">eOppimiskeskus &nbsp;/&nbsp; Newsletter workspace</div>', unsafe_allow_html=True)
    st.title('Create a new issue.')
    st.markdown('''<p class="workspace-intro">Your next newsletter starts here. Collect, curate, and publish with clarity.</p>
<nav class="workflow-strip" aria-label="Newsletter workflow"><a href="#collect"><span>01</span>Collect</a><a href="#review"><span>02</span>Review</a><a href="#design"><span>03</span>Design</a><a href="#export"><span>04</span>Export</a></nav>
<div id="collect"></div>''', unsafe_allow_html=True)
