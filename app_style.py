"""Shared visual skin. Native Streamlit widgets retain their behaviour."""
import streamlit as st


def apply_style():
    st.markdown('''<style>
/* Set our palette explicitly as well as in config.toml, including dark-mode browsers. */
:root {color-scheme:light;}
[data-testid="stApp"] {background:#f5f3ed;color:#203d35;font-family:Arial,Helvetica,sans-serif;}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stMainBlockContainer"] {max-width:1240px;padding-top:3rem;padding-bottom:4rem;}
[data-testid="stSidebar"] {background:#e9eee5;border-right:1px solid #d8e0d4;}
[data-testid="stApp"] h1,[data-testid="stApp"] h2,[data-testid="stApp"] h3 {color:#203d35;letter-spacing:-.04em;}
[data-testid="stApp"] h1 {font-family:Georgia,serif;font-weight:400;font-size:2.8rem;}
[data-testid="stWidgetLabel"] p {color:#203d35;font-size:.85rem;font-weight:600;}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea {color:#203d35!important;background:#fff!important;caret-color:#24634f;}
[data-testid="stTextInput"] [data-baseweb="input"], [data-testid="stTextInput"] [data-baseweb="base-input"], [data-testid="stTextArea"] [data-baseweb="textarea"] {background:#fff!important;border-color:#cbd6c9!important;border-radius:10px;}
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,[data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within {border-color:#24634f!important;box-shadow:0 0 0 3px #24634f18;}
[data-testid="stApp"] button[kind="primary"], [data-testid="stApp"] [data-testid="stBaseButton-primaryFormSubmit"] {background:#24634f!important;border-color:#24634f!important;color:#fff!important;border-radius:9px;min-height:44px;font-weight:600;}
[data-testid="stApp"] button[kind="primary"]:hover {background:#184d3c!important;border-color:#184d3c!important;}
[data-testid="stApp"] button:focus-visible {outline:3px solid #bd813a;outline-offset:3px;}
[data-testid="stApp"] button[kind="secondary"] {color:#245440;background:#fff;border-color:#ced8c9;border-radius:9px;}
[data-testid="stApp"] [data-testid="stCaptionContainer"] {color:#637369;}
[data-testid="stApp"] [data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;}
.brand-kicker {font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:700;color:#687c69;margin-bottom:8px;}
.workspace-intro {color:#637369;max-width:690px;margin:0 0 20px;font-size:15px;line-height:1.7;}
.workflow-strip {display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:8px 0 28px;}
.workflow-strip a {background:#fff;border:1px solid #dce2d6;border-radius:12px;padding:16px;color:#244b3c;text-decoration:none;font-size:14px;font-weight:600;}
.workflow-strip a:hover {border-color:#24634f;}
.workflow-strip span {color:#b47a36;font-size:11px;letter-spacing:1px;margin-right:9px;}
.st-key-login_shell {max-width:1080px;margin:5vh auto;background:#fff;border:1px solid #dce2d6;border-radius:22px;overflow:hidden;box-shadow:0 22px 70px #203d3510;}
.st-key-login_shell [data-testid="stHorizontalBlock"] {gap:0;align-items:stretch;}
.st-key-login_shell [data-testid="stColumn"]:first-child {background:#173f35;}
.login-brand {padding:54px 42px;color:#f6f4eb;min-height:530px;display:flex;flex-direction:column;justify-content:space-between;}
.login-brand .wordmark {font-size:21px;font-weight:700;letter-spacing:-.7px;line-height:1.4;max-width:270px;}
.login-brand .brand-label {font-size:10px;letter-spacing:2.5px;text-transform:uppercase;color:#e4bb84;margin-bottom:20px;}
.login-brand .brand-headline {font-family:Georgia,serif;font-size:47px;font-weight:400;line-height:1.12;letter-spacing:-1.5px;margin:0 0 22px;}
.login-brand .brand-description {font-size:14px;line-height:1.8;color:#d2dfd3;max-width:310px;}
.login-brand .brand-footer {border-top:1px solid #ffffff30;padding-top:20px;font-size:11px;color:#d2dfd3;letter-spacing:.3px;}
.st-key-login_card {padding:48px 44px;}
.st-key-login_card h1 {font-size:2.4rem!important;margin-top:4px;}
.st-key-login_card [data-testid="stForm"] {border:0;padding:14px 0 0;}
.st-key-login_card [data-testid="stFormSubmitButton"] button {width:100%;margin-top:12px;}
.st-key-login_card [data-testid="stTextInput"] input {min-height:46px;}
.st-key-login_card [data-testid="stMarkdownContainer"] p {color:#65756b;}
/* Streamlit nests button labels inside Markdown paragraphs. */
[data-testid="stApp"] button[kind="primary"] [data-testid="stMarkdownContainer"] p,
[data-testid="stApp"] [data-testid="stBaseButton-primaryFormSubmit"] [data-testid="stMarkdownContainer"] p {color:#fff!important;}
@media(max-width:700px){[data-testid="stMainBlockContainer"]{padding:2rem 1rem;}.st-key-login_shell{margin:0 auto;}.st-key-login_shell [data-testid="stHorizontalBlock"]{flex-direction:column;}.st-key-login_shell [data-testid="stColumn"]{width:100%!important;flex:1 1 auto!important;}.login-brand{padding:30px;min-height:0;gap:26px;}.login-brand .brand-headline{font-size:34px;}.login-brand .brand-description,.login-brand .brand-footer{display:none;}.st-key-login_card{padding:28px;}.workflow-strip{grid-template-columns:repeat(2,1fr);}}
</style>''', unsafe_allow_html=True)


def login_brand():
    st.markdown('''<div class="login-brand"><div class="wordmark">Suomen<br>eOppimiskeskus ry</div>
<div><div class="brand-label">The newsletter workspace</div><div class="brand-headline">Good ideas.<br>Shared together.</div>
<div class="brand-description">A little less searching. More time for the stories that matter to your learning community.</div></div>
<div class="brand-footer">Discover · Curate · Share</div></div>''', unsafe_allow_html=True)


def workspace_header():
    st.markdown('<div class="brand-kicker">Suomen eOppimiskeskus ry / Editorial workspace</div>', unsafe_allow_html=True)
    st.title('Your next newsletter starts here.')
    st.markdown('''<p class="workspace-intro">Find something worth sharing. Review the stories, make them your own, and bring your next issue together.</p>
<nav class="workflow-strip" aria-label="Newsletter workflow"><a href="#collect"><span>01</span>Collect</a><a href="#review"><span>02</span>Review</a><a href="#design"><span>03</span>Design</a><a href="#export"><span>04</span>Export</a></nav>
<div id="collect"></div>''', unsafe_allow_html=True)
