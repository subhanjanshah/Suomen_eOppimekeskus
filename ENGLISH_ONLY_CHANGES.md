# English-only newsletter workflow

The Streamlit app no longer translates titles or summaries into Finnish.

- Select and edit articles, then build the final newsletter directly.
- The final HTML is English-only and no longer includes a language switch.
- The Ollama Finnish translation function and its prompt have been removed.
- The editorial review, images, article selection, duplicate-link memory, and date filtering remain.
- Old generated HTML/Markdown and standalone design preview were excluded because they contained stale bilingual output. A new `newsletter_draft.html` is created when you build a newsletter.
- Updated tests cover the no-translation export flow.

Run `python -m unittest discover -s tests -v` after installing `requirements.txt`.
