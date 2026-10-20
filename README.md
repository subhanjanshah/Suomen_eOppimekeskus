# AI-Assisted Newsletter Draft Generator

A local, free, privacy-respecting tool that helps a small team turn scattered web content into a reviewable newsletter draft.

## Recommended Windows setup (Docker Desktop)

1. Install **Docker Desktop** once. Start it at least once after installation to complete its setup and accept any prompts.
2. Download the project ZIP from GitHub and **extract it** to a normal folder. Keep the project files together; do not run launchers from inside the ZIP.
3. Double-click **`Start-eOppimisKeskus.bat`**. The launcher checks Docker, opens Docker Desktop if needed, waits for its engine, builds and starts the application, then opens **http://localhost:8501** in your browser.
4. On first launch, Docker downloads/builds the application and the local **Qwen3:4b** model (approximately 2.5 GB for the model). Internet access and several minutes may be required. The app may become available before the model has finished downloading; allow extra time for the first AI request.
5. In the app, **create the first administrator account** on the initial setup screen and sign in. The administrator can add colleagues from **Manage Accounts**.
6. When finished, double-click **`Stop-eOppimisKeskus.bat`**. It stops the project containers and closes its Command Prompt window automatically on success. Docker Desktop itself remains open.

**Requirements:** Windows with Docker Desktop installed and a working Docker engine, enough free disk space for the container image and AI model, and an internet connection for initial setup and web searches. The Windows launchers do **not** require Python, VS Code, a separate Ollama installation, or Git to run the downloaded project. Docker Desktop must be installed, but you do not have to open it manually each time.

**Data safety:** Accounts and model files are stored in Docker named volumes and survive normal starts/stops, including `docker compose down`. **Do not run `docker compose down -v`** unless you intend to delete those volumes. Do not distribute private accounts, generated newsletters, or other sensitive data with the project.

The application listens on the local computer at **http://localhost:8501** (bound to `127.0.0.1`). See [`SETUP_GUIDE.md`](SETUP_GUIDE.md) for step-by-step troubleshooting. Developers can run `docker compose up -d --build` and `docker compose down` from the project folder.

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
- **Local AI summarisation** — runs entirely on-device via [Ollama](https://ollama.com) and the `qwen3:4b` model, no API costs, no data leaving the machine
- **Human review step** — every AI-generated summary can be approved, edited, or rejected before the final draft is built
- **Styled HTML output** — generates a clean, newsletter-style draft (not just plain text) that can be previewed, downloaded, and shared

## Tech Stack

| Layer | Tool |
|---|---|
| AI model | [Ollama](https://ollama.com) running `qwen3:4b` (fully local, free) |
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
 │  Local AI   │  (Ollama + qwen3:4b — 4–6 sentence summary,
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

**Recommended:** Docker Desktop. No separate Python or Ollama installation is required. See `SETUP_GUIDE.md` for client instructions.

**Optional manual developer setup:** Python 3.12+ and [Ollama](https://ollama.com) installed

```bash
# 1. Install Ollama and pull the model
ollama pull qwen3:4b

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start Ollama (in one terminal)
ollama serve

# 4. Run the app (in another terminal)
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501`.

## Usage

1. Choose **Paste links** or **Search by topic** for each newsletter section
2. Click **Generate Draft** — the AI downloads, filters, and summarises each source
3. **Review** each item: edit its English summary and explicitly check **Include** for the articles you want
4. Click **Build Final Newsletter** to save the reviewed HTML and remember only the included source links
5. Download and hand off for sending (e.g. via Mailchimp)

The preview and download remain available across interactions. Changing the title, selection, or article text requires rebuilding the export. Edits to selected articles require rebuilding the export. A new batch clears previous edits, approvals, and AI answers.

Search memory records articles included in a final newsletter built through Streamlit. Collection, failed processing, and rejected articles do not add links. Existing history from older versions is preserved; it may include previously collected but unused links. Use **Clear search memory** if you want to reset that history. The command-line and Gradio interfaces produce drafts without marking links as used.

Run the isolated workflow checks with `python -m unittest discover -s tests -v`. They use mocked AI and article responses and temporary output folders.

## Design Decisions Worth Noting

- **Local model over cloud API** — directly addresses the client's cost and data-sovereignty concerns; zero per-request cost
- **"Own words only" prompting** — the summarisation prompt explicitly instructs the model not to copy source sentences, and every entry links back to the original — reduces copyright risk while keeping the workflow legal and sustainable
- **Social media was deliberately excluded** — LinkedIn/Facebook block automated scraping in their terms of service; rather than build something that violates platform rules, this was documented as a known limitation
- **Human-in-the-loop by design** — matches the client's explicit requirement that AI assists but never sends anything unreviewed

## Known Limitations

- Local model (`qwen3:4b`) occasionally hallucinates on long or non-English source text (accuracy varies by source and model; check all factual details) — mitigated by the mandatory human review step
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


### Editorial newsletter design

The HTML export now has a forest-green cover, editable issue label and topic themes, a featured story, alternating image/text article rows, and compact event cards. Empty sections are hidden. The layout stacks on narrow screens and includes print styles with a break after the cover. The export uses the reviewed English summaries without a translation step.

After selecting articles, use **Newsletter design** to choose the featured story. Its approved image appears on the cover. Article extraction suggests a lead image when available; you can replace its URL or upload a PNG, JPEG, or WebP image. Add a credit and description, then explicitly include the image after checking reuse permission. Uploaded images are resized and embedded in the HTML; URL images require an internet connection and may become unavailable. Articles without images use a text layout.

This is a browser-oriented HTML draft. Compatibility with email sending platforms has not yet been validated. Existing drafts do not acquire images retroactively: regenerate articles or add images through the design controls.


### Local login

For the recommended Docker setup, **no terminal or Python commands are needed to create accounts**. On the first visit to `http://localhost:8501`, use the initial setup form to create the first account. The first account becomes the **administrator**. After signing in, the administrator can open **Manage Accounts** to add colleagues.

For optional manual development outside Docker, accounts can also be created using `python local_auth.py add-user YOUR_USERNAME` in the configured Python environment. The password must be at least 12 characters. The Docker app stores its accounts in a persistent Docker volume (`/data/accounts.json`); the default manual setup uses `.local/accounts.json`, excluded from Git. There is no default password or public self-registration after initial setup.

Login lasts for the current Streamlit session, up to eight hours. Refreshing may require signing in again. Logging out clears the session's draft, answers, and edits; saved HTML files and shared used-link history remain on disk. Five failed attempts trigger a 30-second delay within that session. Separate accounts currently share saved output and history, but have separate in-memory drafts.

Deployment configuration can supply `NEWSLETTER_ACCOUNTS_FILE` (absolute path to the account JSON), `OLLAMA_BASE_URL` (default `http://localhost:11434`), and `OLLAMA_MODEL` (default `qwen3:4b`) without modifying code. This is local prototype authentication, not a completed public hosting setup: deployment still needs HTTPS, durable storage, cross-session rate limiting or managed identity, and a decision about concurrent shared exports. The optional command-line demonstration is a developer tool and does not use this login gate.

### Article publication calendars

Enable **Filter by publication date**, then select **Published from** and **Published through** before generating a draft. Both calendar dates are included and apply to Events and Field Highlights across pasted links, topic search, and RSS. Invalid ranges disable generation. Dates refer to article publication, not event dates, and retain the source's calendar day.

Articles outside the range are skipped before AI analysis. Unknown dates are excluded by default when filtering is enabled; optionally include them for manual review. Review shows publication dates, exclusion counts, and a warning if you change the calendars after generating. Click Generate Draft to apply new settings.

RSS uses its published date when available, otherwise the extracted article date. Update dates are not substituted for RSS publication dates. Article dates depend on newspaper3k extraction and can be missing or inaccurate. The filter checks discovered candidates; it does not guarantee an exhaustive historical search. Search result limits, RSS feed retention, and previously used links can reduce the number of matching results. Leave filtering disabled for the original any-date behaviour.

Publication-date extraction now checks explicit published-date metadata, article JSON-LD (including graph/mainEntity structures), and semantic publication-time elements before using newspaper3k's fallback date. It does not use generic visible dates or event JSON-LD dates. An extractor fallback matching an explicitly identified modification date is rejected. RSS publication dates remain preferred when available. Review shows the chosen date's source and warns when extracted publication dates disagree; filtering uses the preferred date, so it still requires editorial verification. This improves detection but cannot recover dates a website does not publish.
