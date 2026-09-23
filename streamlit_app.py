"""
Streamlit UI for the Newsletter Draft Generator
--------------------------------------------------
Workflow:
  1. Paste links OR type a topic per section (Events / Field Highlights)
  2. Click "Generate Draft" -> AI downloads + summarises each item
  3. REVIEW STEP: each item is shown individually with an Approve checkbox
     and an editable summary box, so a human can correct/reject anything
     before it goes out (matches the client's requirement: AI gathers,
     human verifies, then it's sent)
  4. Prepare and review Finnish translations, then build the newsletter
     -> only approved (and possibly edited)
     items are included in the final HTML draft

Run locally (requires Ollama running: `ollama serve` in a separate terminal):
    streamlit run streamlit_app.py
"""

import base64
from datetime import date
from io import BytesIO
from PIL import Image
from newsletter_design import safe_url
from copy import deepcopy

import streamlit as st
from local_auth import require_login

from newsletter_generator import (
    build_newsletter_section,
    build_newsletter_section_from_topic,
    build_newsletter_section_from_rss,
    format_newsletter_html,
    load_used_links,
    mark_links_as_used,
    clear_used_links,
    translate_to_finnish,
    ask_ai_about_entries,
    CLIENT_TRUSTED_SOURCES,
    RSS_FEEDS,
)


def render_sidebar():
    with st.sidebar:
        st.subheader("Search memory")
        used = load_used_links()
        st.caption(
            f"{len(used)} link(s) remembered as already used. "
            "Search-by-topic will skip these automatically."
        )
        if used:
            with st.expander("View remembered links"):
                for u in sorted(used):
                    st.write(u)
        if st.button("Clear search memory"):
            clear_used_links()
            st.success("Cleared. Next search will not skip any links.")
            st.rerun()


def parse_links(raw_text):
    if not raw_text:
        return []
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def source_input(label, key_prefix):
    """Renders the mode toggle (Paste links / Search by topic / RSS feeds)
    and returns a function that produces the section dict when called."""
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
            return build_newsletter_section(label, parse_links(links_text))

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
                label, feed_urls, limit_per_feed=limit_per_feed
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
            "Number of results to fetch",
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
                sites=sites or None,
            )

        return build


st.set_page_config(page_title="Newsletter Draft Generator", layout="wide")
require_login()

render_sidebar()

st.title("Newsletter Draft Generator")
st.markdown(
    "Either paste links directly, or type a topic and let the AI search "
    "the web for you. Every item must be reviewed and approved before it "
    "goes into the final draft."
)

# Session state holds the generated (but not-yet-approved) sections across
# button clicks, since Streamlit reruns the whole script on every interaction.
if "generated_sections" not in st.session_state:
    st.session_state.generated_sections = None

newsletter_title = st.text_input(
    "Newsletter title",
    value="Newsletter",
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Events")
    events_builder = source_input("Events", "events")

with col2:
    st.subheader("Field Highlights")
    highlights_builder = source_input("Field Highlights", "highlights")

if st.button("Generate Draft", type="primary"):
    with st.spinner("Searching, downloading, and summarising... this can take a minute or two."):
        sections = [events_builder(), highlights_builder()]

    # Clear widget state before rendering a new batch, including empty batches.
    for key in list(st.session_state):
        if key.startswith(("approve_", "summary_", "fi_title_", "fi_summary_", "fi_review_", "image_", "design_")):
            del st.session_state[key]
    for key in ("ai_answer", "ask_ai_question", "final_html", "final_snapshot"):
        st.session_state.pop(key, None)
    for section in sections:
        for i, entry in enumerate(section["entries"]):
            entry["id"] = f"{section['section_title']}_{i}"
            entry["approved"] = False

    st.session_state.generated_sections = sections

    total = sum(len(s["entries"]) for s in sections)
    if total == 0:
        st.error(
            "No items were generated. This can happen if: Ollama isn't "
            "running, the links/topic were empty, or - if you pasted a "
            "site homepage - the site's article links couldn't be found "
            "automatically (common on modern, JavaScript-heavy sites). "
            "If a homepage link didn't work, try 'Search by topic' with "
            "that site selected as a trusted source instead - it uses "
            "search-engine indexing, which handles these sites better "
            "than scanning the page's raw HTML."
        )

# --- REVIEW STEP ---
if st.session_state.generated_sections:
    st.divider()
    st.header("Review before sending")
    st.markdown(
        "Review the summaries and select the articles to include. Then prepare "
        "and review their Finnish translations before building the newsletter."
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
            key="design_topics", help="Use Finnish, English, or bilingual labels. These appear in both language views.")
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

    if st.button("Prepare Finnish translations", disabled=not selected):
        with st.spinner("Preparing Finnish translations for review..."):
            for entry in selected:
                source = (entry["title"], entry["summary"])
                # Preserve reviewed edits unless the English source changed.
                if entry.get("translation_source") == source:
                    continue
                title_fi, summary_fi = translate_to_finnish(*source)
                entry.update(title_fi=title_fi, summary_fi=summary_fi,
                             translation_source=source)
                st.session_state[f"fi_title_{entry['id']}"] = title_fi
                st.session_state[f"fi_summary_{entry['id']}"] = summary_fi
                st.session_state[f"fi_review_{entry['id']}"] = False

    def reset_finnish_review(entry_id):
        st.session_state[f"fi_review_{entry_id}"] = False

    ready = bool(selected)
    for entry in selected:
        source = (entry["title"], entry["summary"])
        if entry.get("translation_source") != source:
            st.info(f"Prepare Finnish translation for: {entry['title']}")
            ready = False
            continue
        with st.container(border=True):
            st.subheader("Finnish review: " + entry["title"])
            if (entry["title_fi"], entry["summary_fi"]) == source:
                st.warning("Translation may have fallen back to the original text. "
                           "Check and correct the Finnish text before approving.")
            entry["title_fi"] = st.text_input(
                "Finnish title", key=f"fi_title_{entry['id']}",
                on_change=reset_finnish_review, args=(entry["id"],))
            entry["summary_fi"] = st.text_area(
                "Finnish summary", key=f"fi_summary_{entry['id']}",
                on_change=reset_finnish_review, args=(entry["id"],))
            reviewed = st.checkbox("I have reviewed the Finnish title and summary",
                                   key=f"fi_review_{entry['id']}")
            if not reviewed or not entry["title_fi"].strip() or not entry["summary_fi"].strip():
                ready = False

    # A saved export must match the current selection, title, and edits.
    snapshot = {"title": newsletter_title, "sections": final_sections, "design": design}
    if not ready or st.session_state.get("final_snapshot") != snapshot:
        st.session_state.pop("final_html", None)
        st.session_state.pop("final_snapshot", None)

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

# --- ASK AI ---
if st.session_state.generated_sections:
    st.divider()
    st.header("Ask AI about the gathered articles")

    all_entries = [
        entry
        for section in st.session_state.generated_sections
        for entry in section["entries"]
    ]

    if all_entries:
        st.caption(f"AI has access to {len(all_entries)} gathered article(s).")
    else:
        st.info("No articles gathered yet - generate a draft first.")

    question = st.text_area(
        "Your question",
        placeholder="e.g. What trends do you see across these articles?",
        height=90,
        key="ask_ai_question",
    )

    if st.button("Ask AI"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("AI is thinking..."):
                answer = ask_ai_about_entries(question, all_entries)
            st.session_state["ai_answer"] = answer

    if "ai_answer" in st.session_state:
        st.subheader("AI response")
        st.write(st.session_state["ai_answer"])