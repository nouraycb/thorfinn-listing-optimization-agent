import os
import tempfile
from datetime import datetime

import gradio as gr

from agent import audit_listing, rewrite_listing
from keepa_client import get_listing_from_keepa


# ------------ MANUAL MODE FUNCTION ------------
def optimize_manual_ui(
    title,
    bullets,
    description,
    reviews,
    target_keywords,
    category,
    audience,
):
    audit_text = audit_listing(
        title=title,
        bullets=bullets,
        description=description,
        reviews=reviews,
        target_keywords=target_keywords,
    )

    optimized_text = rewrite_listing(
        title=title,
        bullets=bullets,
        description=description,
        reviews=reviews,
        target_keywords=target_keywords,
        category=category,
        audience=audience,
        audit_summary=audit_text,
    )

    return audit_text, optimized_text


# ------------ ASIN / URL MODE FUNCTION ------------
def optimize_from_identifiers_ui(identifiers_text, target_keywords, category, audience):
    # Split and clean input lines
    lines = [line.strip() for line in identifiers_text.splitlines() if line.strip()]
    if not lines:
        return "⚠️ No ASINs or URLs provided. Please add one per line."

    results = []

    for identifier in lines:
        try:
            listing = get_listing_from_keepa(identifier)
        except Exception as e:
            results.append(
                f"## {identifier}\n\n❌ Error fetching from Keepa: `{str(e)}`\n\n---\n"
            )
            continue

        title = listing["title"]
        bullets_list = listing["bullets"]
        description = listing["description"]

        bullets_text = "\n".join(f"- {b}" for b in bullets_list)

        audit_text = audit_listing(
            title=title,
            bullets=bullets_text,
            description=description,
            reviews="",
            target_keywords=target_keywords,
        )

        optimized_text = rewrite_listing(
            title=title,
            bullets=bullets_text,
            description=description,
            reviews="",
            target_keywords=target_keywords,
            category=category,
            audience=audience,
            audit_summary=audit_text,
        )

        block = f"""
## {identifier}  _(ASIN: {listing['asin']})_

### 🧾 Original Title
{title or "_(no title found)_"}

### 📌 Original Bullets
{bullets_text or "_(no bullets found)_"}

### 📝 Original Description
{description or "_(no description found)_"}

---

### 🔍 AI Audit
{audit_text}

---

### ✏️ Optimized Listing
{optimized_text}

---

"""
        results.append(block.strip())

    return "\n\n".join(results)


# ------------ EXPORT HELPERS ------------
def export_manual_result(audit_text: str, optimized_text: str) -> str:
    if not (audit_text or optimized_text):
        raise gr.Error("No results to export. Run an optimization first.")

    content = (
        "=== AUDIT ===\n\n"
        + (audit_text or "")
        + "\n\n=== OPTIMIZED LISTING ===\n\n"
        + (optimized_text or "")
        + "\n"
    )

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"listing_manual_{timestamp}.txt"
    file_path = os.path.join(tempfile.gettempdir(), filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path


def export_batch_result(batch_markdown: str) -> str:
    if not batch_markdown:
        raise gr.Error("No batch results to export. Run a batch optimization first.")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"listing_batch_{timestamp}.txt"
    file_path = os.path.join(tempfile.gettempdir(), filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(batch_markdown)

    return file_path


# ------------ THEME + CSS (for Gradio 6.x) ------------
theme = gr.themes.Soft(
    primary_hue="orange",
    neutral_hue="slate",
)

css = """
#main-header {
    text-align: center;
    padding: 12px 0 4px 0;
}
#main-header h1 {
    font-size: 2.0rem;
    margin-bottom: 0.25rem;
}
#main-header p {
    font-size: 0.95rem;
    opacity: 0.85;
}
.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
}
.small-caption {
    font-size: 0.8rem;
    opacity: 0.8;
}
"""


# ------------ UI LAYOUT (Blocks) ------------
# CHANGE #1: attach theme and css to Blocks instead of launch
with gr.Blocks(
    title="THORFINN",
    theme=theme,      # ✅ moved here
    css=css,          # ✅ moved here
) as demo:
    # Top header
    with gr.Column(elem_id="main-header"):
        gr.Markdown(
            """
<h1> 🧠THORFINN </h1>
<p>I am a a 1,000-year-old Viking reborn as an Amazon listing optimization general. Pillaging weak listings using <b>OpenAI + Keepa</b>, forging war-ready Amazon pages from single ASINs or full raid batches</p>
"""
        )

    # ===== MANUAL INPUT TAB =====
    with gr.Tab("✨ Manual Input"):
        with gr.Row():
            # LEFT: inputs
            with gr.Column(scale=1):
                gr.Markdown("### ✍️ Listing Inputs")

                title_input = gr.Textbox(
                    label="Product Title",
                    lines=2,
                    placeholder="Paste your current Amazon title here",
                )
                bullets_input = gr.Textbox(
                    label="Bullet Points",
                    lines=6,
                    placeholder="One bullet per line or separated clearly",
                )
                description_input = gr.Textbox(
                    label="Description",
                    lines=6,
                    placeholder="Paste your current product description",
                )
                reviews_input = gr.Textbox(
                    label="Optional: Reviews / Voice of Customer",
                    lines=4,
                    placeholder="Paste a few real reviews or phrases customers use",
                )

                gr.Markdown("### 🎯 Targeting")

                keywords_input = gr.Textbox(
                    label="Target Keywords (comma-separated)",
                    placeholder="kataifi dough, shredded phyllo, premium kataifi...",
                )
                category_input = gr.Textbox(
                    label="Category",
                    placeholder="e.g. Grocery & Gourmet Food › Baking Supplies",
                )
                audience_input = gr.Textbox(
                    label="Target Audience",
                    placeholder="e.g. home bakers, Mediterranean dessert lovers, pastry chefs...",
                )

                manual_button = gr.Button("🚀 Optimize Listing", variant="primary")

            # RIGHT: outputs
            with gr.Column(scale=1):
                gr.Markdown("### 📊 Results")

                with gr.Tabs():
                    with gr.TabItem("🔍 Audit"):
                        manual_audit_output = gr.Markdown(
                            value="Run an optimization to see the AI audit here."
                        )
                    with gr.TabItem("✏️ Optimized Listing"):
                        manual_optimized_output = gr.Markdown(
                            value="Run an optimization to see the improved copy here."
                        )

                gr.Markdown("---")
                gr.Markdown("#### 📥 Export Manual Result")

                manual_export_button = gr.Button("Export Manual Result (.txt)")
                manual_export_file = gr.File(
                    label="Download Manual Export",
                    file_types=[".txt"],
                )

        manual_button.click(
            fn=optimize_manual_ui,
            inputs=[
                title_input,
                bullets_input,
                description_input,
                reviews_input,
                keywords_input,
                category_input,
                audience_input,
            ],
            outputs=[manual_audit_output, manual_optimized_output],
        )

        manual_export_button.click(
            fn=export_manual_result,
            inputs=[manual_audit_output, manual_optimized_output],
            outputs=[manual_export_file],
        )

    # ===== ASIN / URL MODE TAB =====
    with gr.Tab("📦 ASIN / URL Mode"):
        with gr.Row():
            # LEFT: inputs
            with gr.Column(scale=1):
                gr.Markdown("### 🔗 ASIN / URL Inputs")

                ids_input = gr.Textbox(
                    label="ASINs or Amazon URLs (one per line)",
                    lines=8,
                    placeholder="Example:\nB0DJ33ZFJH\nhttps://www.amazon.com/dp/B0DJ33ZFJH",
                )

                keywords_batch = gr.Textbox(
                    label="Target Keywords (for all ASINs in this run)",
                    placeholder="kataifi dough, shredded phyllo, premium kataifi...",
                )
                category_batch = gr.Textbox(
                    label="Category (for all ASINs in this run)",
                    placeholder="e.g. Grocery & Gourmet Food › Baking Supplies",
                )
                audience_batch = gr.Textbox(
                    label="Target Audience (for all ASINs in this run)",
                    placeholder="e.g. home bakers, Mediterranean dessert lovers, pastry chefs...",
                )

                batch_button = gr.Button("🚀 Fetch via Keepa & Optimize", variant="primary")

                gr.Markdown(
                    '<p class="small-caption">Each ASIN/URL uses Keepa tokens + OpenAI calls. Use in batches you’re comfortable with.</p>',
                    elem_classes=["small-caption"],
                )

            # RIGHT: outputs
            with gr.Column(scale=1):
                gr.Markdown("### 📊 Batch Results")

                batch_output = gr.Markdown(
                    value="Results for each ASIN will appear here as sections."
                )

                gr.Markdown("---")
                gr.Markdown("#### 📥 Export Batch Results")

                batch_export_button = gr.Button("Export Batch Results (.txt)")
                batch_export_file = gr.File(
                    label="Download Batch Export",
                    file_types=[".txt"],
                )

        batch_button.click(
            fn=optimize_from_identifiers_ui,
            inputs=[
                ids_input,
                keywords_batch,
                category_batch,
                audience_batch,
            ],
            outputs=[batch_output],
        )

        batch_export_button.click(
            fn=export_batch_result,
            inputs=[batch_output],
            outputs=[batch_export_file],
        )


if __name__ == "__main__":
    # Render sets a PORT environment variable; default to 7860 for local runs
    port = int(os.getenv("PORT", "7860"))

    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=True,       # needed on Render so Gradio doesn't complain about localhost
        show_api=False,   # disables the buggy API schema endpoint that was throwing errors
    )
