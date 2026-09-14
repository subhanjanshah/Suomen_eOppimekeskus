"""
Gradio UI for the Newsletter Draft Generator
----------------------------------------------
A simple browser-based interface on top of newsletter_generator.py, so the
client (non-technical) can paste links and click a button, instead of
editing Python code.

Run locally (requires Ollama running: `ollama serve` in a separate terminal):
    python3 gradio_app.py

This will open a local web page (usually http://127.0.0.1:7860) with:
  - A text box for Event links (one per line)
  - A text box for Field Highlight links (one per line)
  - A "Generate Newsletter Draft" button
  - A live preview of the styled newsletter
  - A download button for the final HTML file
"""

import gradio as gr

from newsletter_generator import (
    build_newsletter_section,
    format_newsletter_html,
)


def parse_links(raw_text):
    """Turn a textbox's multi-line input into a clean list of URLs."""
    if not raw_text:
        return []
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def generate_newsletter(events_text, highlights_text, newsletter_title):
    """Called when the button is clicked. Runs the existing pipeline and
    returns (html_for_preview, path_to_downloadable_file)."""

    events_links = parse_links(events_text)
    highlight_links = parse_links(highlights_text)

    if not events_links and not highlight_links:
        error_html = "<p style='color:#b42318;'>Please paste at least one link before generating.</p>"
        return error_html, None

    sections = [
        build_newsletter_section("Events", events_links),
        build_newsletter_section("Field Highlights", highlight_links),
    ]

    html = format_newsletter_html(sections, newsletter_title=newsletter_title or "Newsletter")

    output_path = "newsletter_draft.html"
    with open(output_path, "w") as f:
        f.write(html)

    return html, output_path


with gr.Blocks(title="Newsletter Draft Generator") as demo:
    gr.Markdown(
        "# Newsletter Draft Generator\n"
        "Paste links below (one per line). The AI will summarise each one "
        "and build a draft newsletter. **Always review before sending.**"
    )

    newsletter_title = gr.Textbox(
        label="Newsletter title",
        value="Suomen eOppimiskeskus Newsletter",
    )

    with gr.Row():
        events_input = gr.Textbox(
            label="Event links (one per line)",
            lines=6,
            placeholder="https://example.com/upcoming-event",
        )
        highlights_input = gr.Textbox(
            label="Field highlight links (one per line)",
            lines=6,
            placeholder="https://example.com/interesting-article",
        )

    generate_button = gr.Button("Generate Newsletter Draft", variant="primary")

    gr.Markdown("### Preview")
    preview = gr.HTML()

    download_file = gr.File(label="Download draft (HTML)")

    generate_button.click(
        fn=generate_newsletter,
        inputs=[events_input, highlights_input, newsletter_title],
        outputs=[preview, download_file],
    )


if __name__ == "__main__":
    demo.launch()