
"""
Streamlit UI for the Newsletter Draft Generator
--------------------------------------------------
Workflow:
  1. Paste links OR type a topic per section (News & Insights / Events)
  2. Click "Generate Draft" -> AI downloads + summarises each item
  3. REVIEW STEP: each item is shown individually with an Approve checkbox
     and an editable summary box, so a human can correct/reject anything
     before it goes out (matches the client's requirement: AI gathers,
     human verifies, then it's sent)
  4. Build the newsletter from approved article titles and summaries
     -> only approved (and possibly edited)
     items are included in the final HTML draft

Run locally (requires Ollama running: `ollama serve` in a separate terminal):
    streamlit run streamlit_app.py
"""

import base64
import html
from urllib.parse import urlparse
from datetime import date, timedelta
from io import BytesIO
from PIL import Image
from newsletter_design import safe_url
from copy import deepcopy

import streamlit as st
from local_auth import require_login, is_admin, render_account_management, load_accounts
from app_style import apply_style, workspace_header

from newsletter_generator import (
    build_newsletter_section,
    build_newsletter_section_from_topic,
    build_newsletter_section_from_rss,
    format_newsletter_html,
    load_used_links,
    mark_links_as_used,
    clear_used_links,
    CLIENT_TRUSTED_SOURCES,
    RSS_FEEDS,
)


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="memory-heading">RECENTLY USED LINKS</div>', unsafe_allow_html=True)
        used = load_used_links()
        st.caption(f"{len(used)} saved links · Previously used articles are skipped during topic searches.")
        if used:
            with st.expander(f"Past links ({len(used)})", expanded=False):
                st.markdown('<div class="past-links-heading">Previously included sources</div>', unsafe_allow_html=True)
                for url in sorted(used):
                    # Only make safe web URLs clickable; escape every user-supplied value.
                    parsed = urlparse(url)
                    if parsed.scheme in ("http", "https") and parsed.netloc:
                        label = html.escape(parsed.netloc.removeprefix("www."))
                        href = html.escape(url, quote=True)
                        st.markdown(
                            f'<a class="past-link" href="{href}" target="_blank" rel="noopener noreferrer">'
                            f'<span class="past-link-domain">↗ {label}</span>'
                            f'<span class="past-link-url">{html.escape(url)}</span></a>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.code(url)
        if st.button("Clear link history", key="clear_link_history", use_container_width=True,
                     help="Allow previously used articles to appear in future searches."):
            clear_used_links()
            st.success("History cleared.")
            st.rerun()


def parse_links(raw_text):
    if not raw_text:
        return []
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def source_input(label, key_prefix, date_options=None):
    """Render collection controls and return a builder with shared date settings."""
    date_options = date_options or {}
    mode = st.radio(
        f"{label} - source",
        ["Paste links", "Search by topic", "RSS feeds"],
        key=f"{key_prefix}_mode",
        horizontal=True,
    )

    if mode == "Paste links":
        links_text = st.text_area(
            f"{label} links (one per line)",
            height=140,
            key=f"{key_prefix}_links",
            placeholder="https://example.com/some-article",
        )

        def build():
            return build_newsletter_section(label, parse_links(links_text), **date_options)

        return build

    elif mode == "RSS feeds":
        feed_names = st.multiselect(
            "Check these RSS feeds",
            options=list(RSS_FEEDS.keys()),
            key=f"{key_prefix}_feeds",
            help="Pulls the latest entries directly from each feed - more "
                 "reliable than scanning a homepage for sites that "
                 "publish RSS.",
        )
        custom_feed_url = st.text_input(
            "Or a custom feed URL (optional)",
            key=f"{key_prefix}_custom_feed",
            placeholder="e.g. https://example.com/feed/rss",
        )
        limit_per_feed = st.slider(
            "Max entries per feed",
            min_value=1, max_value=20, value=10,
            key=f"{key_prefix}_rss_limit",
        )

        def build():
            feed_urls = [RSS_FEEDS[name] for name in feed_names]
            if custom_feed_url.strip():
                feed_urls.append(custom_feed_url.strip())
            if not feed_urls:
                return {"section_title": label, "entries": []}
            return build_newsletter_section_from_rss(
                label, feed_urls, limit_per_feed=limit_per_feed, **date_options
            )

        return build

    else:
        topic = st.text_input(
            f"Topic to search for ({label})",
            key=f"{key_prefix}_topic",
            placeholder="e.g. digital pedagogy Finland",
        )

        source_names = st.multiselect(
            "Check these trusted sources (leave empty to search the whole web)",
            options=list(CLIENT_TRUSTED_SOURCES.keys()),
            key=f"{key_prefix}_sources",
            help="These are the sources the team already uses. Selecting "
                 "one or more restricts the search to just those sites - "
                 "the same sites can be checked every newsletter cycle "
                 "without repeating articles already used before.",
        )
        custom_domain = st.text_input(
            "Or a custom domain (optional)",
            key=f"{key_prefix}_custom_site",
            placeholder="e.g. some-other-trusted-site.fi",
        )

        num_results = st.slider(
            "Number of articles wanted",
            help="We check replacement links until this many summaries are ready or the search limit is reached.",
            min_value=1, max_value=10, value=5,
            key=f"{key_prefix}_num",
        )

        def build():
            if not topic.strip():
                return {"section_title": label, "entries": []}

            sites = [CLIENT_TRUSTED_SOURCES[name] for name in source_names]
            if custom_domain.strip():
                sites.append(custom_domain.strip())

            return build_newsletter_section_from_topic(
                label, topic, max_results=num_results,
                sites=sites or None, **date_options,
            )

        return build


st.set_page_config(page_title="Newsletter Draft Generator", layout="wide")
# The theme is kept in the user's Streamlit session; no browser setting is required.
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
apply_style(dark=st.session_state.dark_mode)
require_login()

with st.sidebar:
    st.markdown('<div class="sidebar-app-title">eOppimisRadar</div>'
                '<div class="sidebar-app-subtitle">Editorial workspace</div>', unsafe_allow_html=True)
    if is_admin(st.session_state.get("auth_user"), load_accounts()):
        page = st.radio("Workspace", ["Newsletter Generator", "Manage Accounts"],
                        key="main_page", label_visibility="collapsed")
    else:
        page = "Newsletter Generator"
        st.markdown('<div class="sidebar-only-page">▣ &nbsp; Newsletter Generator</div>',
                    unsafe_allow_html=True)

# Show history on both pages, with the appearance control anchored at the sidebar bottom.
render_sidebar()
with st.sidebar:
    st.container(key="sidebar_bottom_spacer")
    with st.container(key="theme_toggle_panel"):
        st.toggle("🌙 Dark mode" if not st.session_state.dark_mode else "☀️ Light mode",
                  key="dark_mode", help="Switch the appearance of this workspace")

if page == "Manage Accounts":
    render_account_management()
    st.stop()

workspace_header()

# Session state holds the generated (but not-yet-approved) sections across
# button clicks, since Streamlit reruns the whole script on every interaction.
if "generated_sections" not in st.session_state:
    st.session_state.generated_sections = None

newsletter_title = st.text_input(
    "Newsletter title",
    value="Newsletter",
)

st.subheader("Article publication dates")
filter_dates = st.checkbox("Filter by publication date", key="filter_dates")
date_options = {}
date_valid = True
if filter_dates:
    start_col, end_col = st.columns(2)
    with start_col:
        start = st.date_input("Published from", value=date.today() - timedelta(days=30),
                              min_value=date(1900, 1, 1), max_value=date.today(), key="published_from")
    with end_col:
        end = st.date_input("Published through", value=date.today(),
                            min_value=date(1900, 1, 1), max_value=date.today(), key="published_through")
    undated = st.checkbox("Also include articles with unknown publication dates", value=False,
                          key="include_undated")
    date_valid = start is not None and end is not None and start <= end
    if not date_valid:
        st.error("Select both dates, with the start on or before the end.")
    date_options = dict(start_date=start, end_date=end, include_undated=undated)
    st.caption("Both dates are included. This checks article publication dates, not event dates. "
               "Filtering happens before AI analysis; search results and feeds may not contain every article in the range.")

highlights_tab, events_tab = st.tabs(["News & Insights", "Events"])
st.caption("Set up each section in its tab. Generate Draft collects both sections into one newsletter.")

with highlights_tab:
    st.subheader("News & Insights")
    highlights_builder = source_input("News & Insights", "highlights", date_options)

with events_tab:
    st.subheader("Events")
    events_builder = source_input("Events", "events", date_options)

if st.button("Generate Draft", type="primary", disabled=not date_valid):
    with st.status("Collecting and summarising articles (this can take several minutes)...", expanded=True) as progress:
        st.write("Processing News & Insights...")
        highlights_section = highlights_builder()
        st.write("Processing Events...")
        events_section = events_builder()
        sections = [highlights_section, events_section]
        progress.update(label="Draft collection finished", state="complete", expanded=False)

    # Clear widget state before rendering a new batch, including empty batches.
    for key in list(st.session_state):
        if key.startswith(("approve_", "summary_", "image_", "design_")):
            del st.session_state[key]
    for key in ("final_html", "final_snapshot"):
        st.session_state.pop(key, None)
    for section in sections:
        for i, entry in enumerate(section["entries"]):
            entry["id"] = f"{section['section_title']}_{i}"
            entry["approved"] = False

    st.session_state.generated_sections = sections
    st.session_state.generated_date_options = dict(date_options)

if st.session_state.generated_sections:
    total = sum(len(section["entries"]) for section in st.session_state.generated_sections)
    if not total:
        st.warning("No draft articles were produced. See the collection results below for the reasons.")
    with st.expander("Collection results", expanded=not total):
        for section in st.session_state.generated_sections:
            requested = section.get("requested_count")
            if requested and len(section["entries"]) < requested:
                st.warning(f"{section['section_title']}: found {len(section['entries'])} of {requested} requested articles. "
                           "The search limit was reached before enough usable articles were found. "
                           "Your source and publication-date requirements were kept. See the results below.")
            if "collection_results" not in section and section["entries"]:
                st.write(f"**{section['section_title']}** — {len(section['entries'])} summaries created.")
                st.info("Collection details are unavailable for this draft. It may have been generated "
                        "before the latest update. Restart the app and generate a new draft to use "
                        "the updated collection logic and see its results.")
                continue
            results = section.get("collection_results", [])
            st.write(f"**{section['section_title']}** — {len(results)} candidates checked; "
                     f"{len(section['entries'])} summaries created.")
            if results:
                st.dataframe(results, hide_index=True, use_container_width=True)
                if any(row["Result"] == "Unknown publication date" for row in results):
                    st.info("Some publication dates could not be verified. You can include unknown dates "
                            "to review those articles, but they may fall outside your selected range.")
            else:
                st.caption("No candidates reached processing. The section may have no input, "
                           "or discovery returned no eligible links. Check the terminal for search or feed errors.")

# --- REVIEW STEP ---
if st.session_state.generated_sections:
    st.divider()
    st.markdown('<div id="review"></div>', unsafe_allow_html=True)
    st.header("Review before sending")
    if st.session_state.get("generated_date_options", {}) != date_options:
        st.warning("Date settings changed. Click Generate Draft to apply them; the articles below are from the previous run.")
    applied = st.session_state.get("generated_date_options", {})
    if applied:
        st.caption(f"Collected for publication dates {applied['start_date']} to {applied['end_date']} (inclusive).")
    for section in st.session_state.generated_sections:
        excluded = section.get("date_excluded", {})
        if sum(excluded.values()):
            st.caption(f"{section['section_title']}: excluded {excluded.get('outside_range', 0)} outside the date range "
                       f"and {excluded.get('unknown_date', 0)} with unknown publication dates.")
    st.markdown(
        "Review the titles and summaries, select the articles to include, "
        "then build the newsletter."
    )

    for section in st.session_state.generated_sections:
        if not section["entries"]:
            continue

        st.subheader(section["section_title"])

        sorted_entries = sorted(
            section["entries"], key=lambda e: e.get("relevance", 0), reverse=True
        )

        for entry in sorted_entries:
            with st.container(border=True):
                approve_col, content_col = st.columns([1, 8])

                with approve_col:
                    entry["approved"] = st.checkbox(
                        "Include",
                        value=entry["approved"],
                        key=f"approve_{entry['id']}",
                    )

                with content_col:
                    relevance = entry.get("relevance", 0)
                    badge = {5: "🟢", 4: "🟢", 3: "🟡", 2: "🟠", 1: "🔴", 0: "⚪"}.get(relevance, "⚪")
                    st.markdown(f"**{entry['title']}**  {badge} Relevance: {relevance}/5")

                    if entry.get("reason"):
                        st.caption(f"Why: {entry['reason']}")

                    entry["summary"] = st.text_area(
                        "Summary (editable)",
                        value=entry["summary"],
                        key=f"summary_{entry['id']}",
                        height=90,
                        label_visibility="collapsed",
                    )

                    if entry.get("topics"):
                        st.caption("Topics: " + ", ".join(entry["topics"]))

                    st.caption("Published: " + (entry.get("published_date") or "Unknown — check the source"))
                    if entry.get("published_date"):
                        st.caption("Date source: " + entry.get("date_source", "Article extractor"))
                    if entry.get("date_conflict"):
                        candidates = "; ".join(f"{c['date']} ({c['source']})" for c in entry.get("date_candidates", []))
                        st.warning("Conflicting publication dates — verify against the source. " + candidates)
                    st.caption(f"Source: {entry['source_url']}")

    st.divider()

    final_sections = [
        {"section_title": section["section_title"],
         "entries": [e for e in section["entries"] if e["approved"]]}
        for section in st.session_state.generated_sections
    ]
    selected = [e for section in final_sections for e in section["entries"]]

    design = {}
    if selected:
        st.markdown('<div id="design"></div>', unsafe_allow_html=True)
        st.subheader("Newsletter design")
        feature = st.selectbox(
            "Featured story and cover image", options=[e["id"] for e in selected],
            format_func=lambda entry_id: next(e["title"] for e in selected if e["id"] == entry_id),
            key="design_feature")
        suggested_topics = list(dict.fromkeys(
            str(topic) for e in selected for topic in (e.get("topics") or [])))[:4]
        st.caption("Suggested themes: " + (", ".join(suggested_topics) or "Add your own below."))
        topic_text = st.text_input(
            "Cover themes (comma-separated; leave blank to use suggested themes)",
            key="design_topics", help="These themes appear on the newsletter cover.")
        issue = st.text_input("Issue date or label", value=date.today().strftime("%m / %Y"), key="design_issue")
        design = dict(issue_label=issue, cover_topics=(
            [t.strip() for t in topic_text.split(",") if t.strip()][:4]
            if topic_text.strip() else suggested_topics),
            featured_url=next(e["source_url"] for e in selected if e["id"] == feature))
        st.caption("Choose images you are authorised to reuse and add any required credit. "
                   "Without an image, the layout uses a spacious text treatment.")
        for entry in selected:
            with st.expander("Image: " + entry["title"], expanded=True):
                entry_id = entry["id"]
                image_url = st.text_input("Article image URL", value=entry.get("image_url", ""),
                                          key=f"image_url_{entry_id}")
                upload = st.file_uploader("Or upload an image", type=["png", "jpg", "jpeg", "webp"],
                                          key=f"image_upload_{entry_id}")
                chosen_image = safe_url(image_url, image=True)
                if image_url and not chosen_image:
                    st.warning("Use an http or https image URL.")
                if upload:
                    try:
                        with Image.open(upload) as uploaded_image:
                            uploaded_image.thumbnail((1600, 1600))
                            image_buffer = BytesIO()
                            uploaded_image.convert("RGB").save(image_buffer, format="JPEG", quality=88)
                        chosen_image = "data:image/jpeg;base64," + base64.b64encode(image_buffer.getvalue()).decode()
                    except (OSError, ValueError, Image.DecompressionBombError):
                        chosen_image = ""
                        st.error("This image could not be read. Try a different image.")
                # A replacement image needs its own inclusion decision.
                if entry.get("chosen_image") != chosen_image:
                    st.session_state[f"image_ok_{entry_id}"] = False
                entry["chosen_image"] = chosen_image
                entry["image_url"] = chosen_image
                if not chosen_image:
                    st.info("No image is available for this article. Paste a direct image URL "
                            "or upload a picture above. Articles gathered before the design update "
                            "need an image added here or a fresh Generate Draft run.")
                if chosen_image:
                    st.image(base64.b64decode(chosen_image.split(",", 1)[1])
                             if chosen_image.startswith("data:") else chosen_image, width=320)
                entry["image_credit"] = st.text_input("Image credit", key=f"image_credit_{entry_id}")
                entry["image_alt"] = st.text_input("Image description (accessibility)", key=f"image_alt_{entry_id}")
                entry["image_approved"] = st.checkbox(
                    "Include this image — I have checked permission and credit",
                    key=f"image_ok_{entry_id}", disabled=not chosen_image)

        included_images = sum(bool(e.get("image_approved") and e.get("image_url")) for e in selected)
        st.caption(f"Images included: {included_images} of {len(selected)} articles.")
        featured_entry = next(e for e in selected if e["id"] == feature)
        if not (featured_entry.get("image_approved") and featured_entry.get("image_url")):
            st.warning("The cover currently has no image. Add or select a picture for the featured "
                       "story above and check ‘Include this image’ to show it on the cover.")

    # Approved original-language content is ready for export; no translation step.
    ready = bool(selected)

    # A saved export must match the current selection, title, and edits.
    snapshot = {"title": newsletter_title, "sections": final_sections, "design": design}
    if not ready or st.session_state.get("final_snapshot") != snapshot:
        st.session_state.pop("final_html", None)
        st.session_state.pop("final_snapshot", None)

    st.markdown('<div id="export"></div>', unsafe_allow_html=True)
    if st.button("Build Final Newsletter", type="primary", disabled=not ready):
        html = format_newsletter_html(
            final_sections, newsletter_title=newsletter_title or "Newsletter", **design)
        try:
            with open("newsletter_draft.html", "w", encoding="utf-8") as f:
                f.write(html)
            mark_links_as_used([e["source_url"] for e in selected])
        except OSError as exc:
            st.error(f"Could not save the newsletter and its used-link history: {exc}")
        else:
            st.session_state.final_html = html
            st.session_state.final_snapshot = deepcopy(snapshot)
            st.rerun()

    if "final_html" in st.session_state:
        st.success(f"Final newsletter built with {len(selected)} reviewed item(s).")
        st.subheader("Final Preview")
        st.components.v1.html(st.session_state.final_html, height=700, scrolling=True)
        st.download_button(
            label="Download final newsletter (HTML)",
            data=st.session_state.final_html, file_name="newsletter_draft.html",
            mime="text/html")
