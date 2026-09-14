# AI-Assisted Newsletter Draft Generator

A local, free, privacy-respecting tool that helps a small team turn scattered web content into a reviewable newsletter draft — built as part of a university Service Design / Design Thinking project.

## The Problem

The client is a small non-profit association (education technology / digital pedagogy sector, Finland) that sends a members-only newsletter 2–3 times per month. Two staff members currently:

- Manually browse web pages, social media, and other newsletters for relevant news and events
- Post interesting finds to a Telegram channel
- Later decide what's worth including
- Write up the newsletter by hand and send it via their community platform or Mailchimp

With very limited staff time and a constant stream of information to monitor, this process doesn't scale well. The client asked for help exploring how AI and automation could assist — **without** losing sight of sustainability, cost, and copyright concerns.

## What This Project Explores

This repo is the output of the **Empathize → Define → Ideate → Prototype** stages of a Design Thinking process, followed by building a working technical prototype in Sprint 1.

Key constraints the client set, which shaped every design decision below:

- **Cost** — must be sustainable for a small non-profit (→ local, free AI instead of paid APIs)
- **Copyright** — AI must summarise in its own words, never reproduce source text, and always link back to the original (→ prompt design + source attribution)
- **Human oversight** — AI gathers, a human verifies before anything is sent (→ built-in review/approval step)

## Features

- **Web search by topic** — type a topic (e.g. "digital pedagogy Finland") instead of manually finding links
- **Manual link input** — paste specific URLs directly when you already know the source
- **Site-restricted search** — optionally limit search to one trusted domain (e.g. a specific research repository)
- **Source reliability filtering** — automatically excludes crowd-edited/low-reliability sources (e.g. Wikipedia, Reddit) and prioritises EU institutions, universities, and research bodies
- **Duplicate avoidance** — remembers previously used links so repeat searches surface fresh content instead of the same articles
- **Local AI summarisation** — runs entirely on-device via [Ollama](https://ollama.com) and the `qwen2.5:7b` model, no API costs, no data leaving the machine
- **Human review step** — every AI-generated summary can be approved, edited, or rejected before the final draft is built
- **Styled HTML output** — generates a clean, newsletter-style draft (not just plain text) that can be previewed, downloaded, and shared

## Tech Stack

| Layer | Tool |
|---|---|
| AI model | [Ollama](https://ollama.com) running `qwen2.5:7b` (fully local, free) |
| Article extraction | `newspaper3k` |
| Web search | `ddgs` (DuckDuckGo search, free, no API key) |
| UI | [Streamlit](https://streamlit.io) |
| Output | Styled HTML (custom template) |

## Architecture

```
 Topic / Links
      │
      ▼
 ┌─────────────┐
 │ Web Search  │  (ddgs, optional site: filter)
 │  + Filters  │  → blocklist, EU-priority list, duplicate memory
 └─────┬───────┘
       ▼
 ┌─────────────┐
 │  Article    │  (newspaper3k — download + extract readable text)
 │  Extraction │
 └─────┬───────┘
       ▼
 ┌─────────────┐
 │  Local AI   │  (Ollama + qwen2.5:7b — 2-3 sentence summary,
 │ Summarising │   copyright-safe prompt, own words only)
 └─────┬───────┘
       ▼
 ┌─────────────┐
 │ Human Review│  (Streamlit UI — approve / edit / reject each item)
 └─────┬───────┘
       ▼
 ┌─────────────┐
 │ Final Draft │  (styled HTML, downloadable)
 └─────────────┘
```

## Setup & Installation

**Prerequisites:** Python 3.10+, [Ollama](https://ollama.com) installed

```bash
# 1. Install Ollama and pull the model
ollama pull qwen2.5:7b

# 2. Install Python dependencies
pip install requests newspaper3k lxml_html_clean ddgs streamlit

# 3. Start Ollama (in one terminal)
ollama serve

# 4. Run the app (in another terminal)
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501`.

## Usage

1. Choose **Paste links** or **Search by topic** for each newsletter section
2. Click **Generate Draft** — the AI downloads, filters, and summarises each source
3. **Review** each item: uncheck anything irrelevant, edit any summary that needs correcting
4. Click **Build Final Newsletter** to produce the final styled HTML draft
5. Download and hand off for sending (e.g. via Mailchimp)

## Design Decisions Worth Noting

- **Local model over cloud API** — directly addresses the client's cost and data-sovereignty concerns; zero per-request cost
- **"Own words only" prompting** — the summarisation prompt explicitly instructs the model not to copy source sentences, and every entry links back to the original — reduces copyright risk while keeping the workflow legal and sustainable
- **Social media was deliberately excluded** — LinkedIn/Facebook block automated scraping in their terms of service; rather than build something that violates platform rules, this was documented as a known limitation
- **Human-in-the-loop by design** — matches the client's explicit requirement that AI assists but never sends anything unreviewed

## Known Limitations

- Local model (`qwen2.5:7b`) occasionally hallucinates on long or non-English source text (~25% failure rate observed in initial testing on a single long Finnish-language article) — mitigated by the mandatory human review step
- Social media sources (LinkedIn, Facebook) are not supported due to platform scraping restrictions
- Search relies on DuckDuckGo's free search index, which is less exhaustive than paid search APIs
- No direct integration with sending platforms (Mailchimp, etc.) yet — output is a downloadable HTML file

## Possible Future Improvements

- Direct OAI-PMH integration for specific trusted repositories (e.g. Theseus.fi) for more precise "what's new since last time" detection than search-engine indexing
- Optional cloud model comparison (e.g. free-tier Gemini) for teams wanting a quality/reliability trade-off
- Direct Mailchimp API integration to skip the manual copy-paste step
- Multi-language summarisation quality testing beyond Finnish/English

## Project Context

Built as part of a Service Design / Design Thinking university module, following the Empathize → Define → Ideate → Prototype process, using Jira for sprint/backlog management.

## License

MIT — feel free to reuse or adapt.
