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
  4. Click "Build Final Newsletter" -> only approved (and possibly edited)
     items are included in the final HTML draft

Run locally (requires Ollama running: `ollama serve` in a separate terminal):
    streamlit run streamlit_app.py
"""

import streamlit as st

from newsletter_generator import (
    build_newsletter_section,
    build_newsletter_section_from_topic,
    build_newsletter_section_from_rss,
    format_newsletter_html,
    load_used_links,
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
    value="Suomen eOppimiskeskus Newsletter",
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

    # Tag each entry with a stable id, and default-approve only items that
    # scored 3+ on relevance (clearly-irrelevant items start unchecked,
    # but can still be manually included - nothing is ever silently hidden).
    for section in sections:
        for i, entry in enumerate(section["entries"]):
            entry["id"] = f"{section['section_title']}_{i}"
            entry["approved"] = entry.get("relevance", 3) >= 3

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
        "Uncheck anything that shouldn't go out. Edit any summary directly "
        "if it needs correcting."
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

    if st.button("Build Final Newsletter", type="primary"):
        final_sections = []
        for section in st.session_state.generated_sections:
            approved_entries = [e for e in section["entries"] if e["approved"]]
            final_sections.append({
                "section_title": section["section_title"],
                "entries": approved_entries,
            })

        total_approved = sum(len(s["entries"]) for s in final_sections)

        if total_approved == 0:
            st.error("No items are approved. Check at least one item above.")
        else:
            with st.spinner("Translating approved items to Finnish for the language toggle..."):
                for section in final_sections:
                    for entry in section["entries"]:
                        # Translate the final (possibly human-edited) English
                        # text, so the Finnish version matches any corrections
                        # made during review.
                        title_fi, summary_fi = translate_to_finnish(
                            entry["title"], entry["summary"]
                        )
                        entry["title_fi"] = title_fi
                        entry["summary_fi"] = summary_fi

            html = format_newsletter_html(
                final_sections, newsletter_title=newsletter_title or "Newsletter"
            )

            with open("newsletter_draft.html", "w") as f:
                f.write(html)

            st.success(f"Final newsletter built with {total_approved} approved item(s).")

            st.subheader("Final Preview")
            st.components.v1.html(html, height=700, scrolling=True)

            st.download_button(
                label="Download final newsletter (HTML)",
                data=html,
                file_name="newsletter_draft.html",
                mime="text/html",
            )

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