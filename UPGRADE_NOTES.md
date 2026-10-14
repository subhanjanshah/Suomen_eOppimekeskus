# Conservative cleanup — October 2026

This is an edited copy of the supplied GitHub ZIP, not a change to your repository.

## Changes

- `compose.yaml`, `start.sh`, `newsletter_generator.py`: select the Ollama model in **one place** (`OLLAMA_MODEL` in Compose, currently `qwen3:4b`). Both startup and Python read it. The request timeout is configurable as `OLLAMA_TIMEOUT` (600 seconds by default). Existing prompts and relevance scoring text are unchanged.
- `newsletter_generator.py`: removed an unused summary prompt and unused chat URL constants. Blocked domains now match exact hostnames or subdomains instead of arbitrary substrings; preferred-source matching uses hostname suffixes. AI response fields and 1–5 relevance range are validated before use. Malformed responses are skipped rather than passed to the editor. RSS feeds now report HTTP errors and empty feeds more clearly.
- `streamlit_app.py`: added a simple two-section progress status. No change to the Events or Field Highlights prompts, source selectors, editorial approval, or newsletter layout.
- `requirements.txt`: added the directly used `feedparser` dependency.
- `README.md`, `SETUP_GUIDE.md`: updated for the recommended Docker/Windows launcher workflow and Qwen3:4b.
- Removed obsolete experimental `gradio_app.py`, `compare_prompts.py` and three tracked example/generated newsletter HTML/Markdown files. They remain in the original GitHub commit if ever needed.
- Added `tests/test_cleanup_reliability.py` for domain filtering and AI response parsing.

## Intentionally unchanged

- Account storage and first-account administrator behavior, to avoid an untested data migration.
- Existing article-processing paths, to preserve tested date filtering, fallback behavior, used-link tracking and editorial review. A large refactor would increase risk and complexity.
- The exact AI instructions, prompts, relevance scale, newsletter design, Docker named volumes, and Windows launchers.

## Verification

- Python source compilation (`python -m compileall -q .`) **passed**.
- Full unit tests **not run in this environment**: required packages (Streamlit, newspaper3k, feedparser, ddgs) are not installed here.
- Docker image build, live Ollama generation, first-time model download, login persistence and Windows launcher tests **not run here**; please verify on your Windows machine before replacing the working project.

## Safe testing on Windows

1. Keep your working Git checkout untouched. Extract this ZIP to a separate folder.
2. Start Docker Desktop, then from the new folder run `docker compose up --build -d` (or double-click `Start-eOppimisRadar.bat`).
3. Open `http://localhost:8501`, create a **test account if prompted**, generate one or two articles, review and export a newsletter, and test stopping/starting.
4. Run tests in an environment with dependencies installed: `python -m unittest discover -s tests -v`.
5. **Do not run** `docker compose down -v` on your existing installation; it removes persistent volumes. Note: Compose project names depend on the folder name. A different extracted folder may create separate Docker volumes, so seeing a new login setup does not mean your old account was deleted.
6. Only after testing, selectively copy the upgraded files to your Git checkout, review `git diff`, commit and push.

## Remaining limitations

- `feedparser.parse(feed_url)` can wait on an unresponsive feed; robust request timeouts would require a separate behavior-tested change.
- Sequential CPU-based AI generation is still slow; progress is section-level, not per-article.
- The administrator is still the first account in the existing JSON file. Changing this safely requires an account migration plan.
- Source preference and blocklists are editorial heuristics, not factual verification.
