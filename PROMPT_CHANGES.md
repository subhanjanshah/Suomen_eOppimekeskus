# Newsletter prompt improvements

Updated `newsletter_generator.py` prompts to produce fuller, more useful newsletter summaries.

- Article analysis now targets **4–6 sentences / approximately 90–140 words**, when the article provides enough reliable content.
- Summaries lead with the development, include meaningful concrete details, and explain relevance only where supported.
- Translation retains the full detail and length in idiomatic Finnish.
- Relevance scores focus on editorial value rather than keywords alone.
- Existing JSON keys (`relevance`, `reason`, `summary`, `topics`) and date-filter logic are unchanged.

## Suggested test

1. Run `streamlit run streamlit_app.py` with Ollama available.
2. Generate a draft using a substantive news article and a very short article.
3. Check that the substantive article gets a detailed but accurate summary; the short article should not be padded.
4. Prepare Finnish translations and verify that names, dates, numbers, and important details survive.
5. Review before publishing; AI-generated content still requires human checking.

Note: A longer output may take more time to generate on local Ollama models.
