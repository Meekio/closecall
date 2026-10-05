"""
Screen 3 (Add Clothes) + Screen 4 (AI Tagging / Processing)
─────────────────────────────────────────────────────────────
Flow:
  1. User uploads a photo (camera or gallery).
  2. "Tag & Add" button calls Gemini vision.
  3. A step-by-step progress display appears during tagging.
  4. On success, a result card shows the detected tags.
  5. "Add Another" resets. "Edit Tags" switches to item-detail view.
"""

from __future__ import annotations
import io
import gradio as gr
from PIL import Image

from src.vision.uploader import upload_from_pil


# ─── Gradio 6 image coercion ──────────────────────────────────────────────────

def _to_pil(image) -> Image.Image | None:
    """
    Gradio 6 passes gr.Image(type='pil') as either:
      - A PIL Image  (older behaviour, still happens sometimes)
      - A dict       {'path': '/tmp/...', 'url': 'http://...'}  (Gradio 6 FileData)
      - None
    Handles both, plus AVIF / HEIC by reading raw bytes.
    """
    if image is None:
        return None

    # Gradio 6 FileData dict
    if isinstance(image, dict):
        path = image.get("path", "")
        if not path:
            return None
        try:
            return Image.open(path).convert("RGB")
        except Exception:
            try:
                data = open(path, "rb").read()
                return Image.open(io.BytesIO(data)).convert("RGB")
            except Exception:
                return None

    # Already PIL
    if isinstance(image, Image.Image):
        return image.convert("RGB")

    return None


# ─── progress HTML helpers ────────────────────────────────────────────────────

def _steps_html(phase: str) -> str:
    """
    phase: "idle" | "running" | "done" | "error"
    Returns the step checklist HTML shown during/after tagging.
    """
    steps = [
        ("Identifying item type",      "done"    if phase in ("done","error") else ("spin" if phase=="running" else "wait")),
        ("Detecting color and style",   "done"    if phase in ("done","error") else ("spin" if phase=="running" else "wait")),
        ("Estimating formality",        "done"    if phase == "done"           else ("spin" if phase=="running" else "wait")),
        ("Checking season suitability", "done"    if phase == "done"           else "wait"),
        ("Saving to your wardrobe",     "done"    if phase == "done"           else "wait"),
    ]
    icons = {"done": "✅", "spin": "⏳", "wait": "○", "error": "❌"}
    colors = {"done": "#22C55E", "spin": "#8B5CF6", "wait": "#D1D5DB", "error": "#EF4444"}

    rows = ""
    for label, state in steps:
        rows += (
            f'<div class="cc-agent-step-item" style="color:{colors[state]}">'
            f'  <span>{icons[state]}</span>'
            f'  <span style="font-size:14px;color:#374151">{label}</span>'
            f'</div>'
        )

    title = {
        "idle":    "",
        "running": '<div style="font-size:16px;font-weight:600;margin-bottom:10px;color:#1C1C1E">Analyzing your clothes...</div>',
        "done":    '<div style="font-size:16px;font-weight:600;margin-bottom:10px;color:#22C55E">Item added!</div>',
        "error":   '<div style="font-size:16px;font-weight:600;margin-bottom:10px;color:#EF4444">Tagging failed</div>',
    }[phase]

    if phase == "idle":
        return ""

    return f'<div class="cc-agent-steps">{title}{rows}</div>'


def _result_card_html(item: dict) -> str:
    seasons = ", ".join(item.get("season") or [])
    rain = "✅ Yes" if item.get("rain_suitable") else "No"
    conf = f"{(item.get('confidence') or 0)*100:.0f}%"
    formality_labels = {1:"Loungewear",2:"Casual",3:"Smart Casual",4:"Business Casual",5:"Formal"}
    formality_str = formality_labels.get(item.get("formality",2), str(item.get("formality","")))
    return f"""
<div class="cc-card" style="margin-top:12px">
  <div style="font-size:15px;font-weight:600;color:#1C1C1E;margin-bottom:12px">
    {item.get('color','').title()} {item.get('subtype','').replace('_',' ').title()}
    <span style="font-size:12px;color:#6B7280;font-weight:400;margin-left:6px">(confidence: {conf})</span>
  </div>
  <div class="cc-tag-row">
    <span class="cc-tag-label">Category</span>
    <span style="font-size:14px;color:#1C1C1E;font-weight:500">{item.get('category','').title()}</span>
  </div>
  <div class="cc-tag-row">
    <span class="cc-tag-label">Subtype</span>
    <span style="font-size:14px;color:#1C1C1E;font-weight:500">{item.get('subtype','').replace('_',' ').title()}</span>
  </div>
  <div class="cc-tag-row">
    <span class="cc-tag-label">Color</span>
    <span style="font-size:14px;color:#1C1C1E;font-weight:500">{item.get('color','').title()}</span>
  </div>
  <div class="cc-tag-row">
    <span class="cc-tag-label">Formality</span>
    <span style="font-size:14px;color:#1C1C1E;font-weight:500">{formality_str}</span>
  </div>
  <div class="cc-tag-row">
    <span class="cc-tag-label">Season(s)</span>
    <span style="font-size:14px;color:#1C1C1E;font-weight:500">{seasons}</span>
  </div>
  <div class="cc-tag-row" style="border-bottom:none">
    <span class="cc-tag-label">Rain suitable</span>
    <span style="font-size:14px;color:#1C1C1E;font-weight:500">{rain}</span>
  </div>
  <div style="margin-top:8px;font-size:12px;color:#9CA3AF">ID: {item.get('item_id','')}</div>
</div>
"""


# ─── event handlers ───────────────────────────────────────────────────────────

def handle_tag(image, label: str):
    """Run vision tagging. Accepts PIL Image or Gradio 6 FileData dict."""
    pil = _to_pil(image)

    if pil is None:
        return (
            '<div style="color:#EF4444;padding:8px">Please upload a photo first.</div>',
            "",
            "",
            gr.update(visible=False),
        )

    try:
        item = upload_from_pil(pil, label=label.strip() or None)
        steps  = _steps_html("done")
        result = _result_card_html(item)
        return steps, result, item["item_id"], gr.update(visible=True)
    except Exception as exc:
        steps = _steps_html("error") + f'<div style="color:#EF4444;font-size:13px;padding:4px 0">{exc}</div>'
        return steps, "", "", gr.update(visible=False)


def handle_reset():
    return None, "", _steps_html("idle"), "", "", gr.update(visible=False)


# ─── tab builder ──────────────────────────────────────────────────────────────

def build_add_clothes_tab(go_edit_item_fn) -> gr.State:
    """
    Build the Add Clothes tab.

    Parameters
    ----------
    go_edit_item_fn : callable(item_id: str)
        Called when the user clicks "Edit Tags" after a successful upload.
        Should pre-load that item into the Item Detail tab and switch to it.

    Returns
    -------
    gr.State
        The state component holding the last uploaded item_id.
    """

    last_item_id = gr.State("")

    with gr.Column(elem_classes=["cc-screen"]):

        gr.HTML(
            '<div style="font-size:20px;font-weight:700;color:#1C1C1E;'
            'padding:8px 0 16px">📷 Add Clothes</div>'
        )

        # ── Upload area ───────────────────────────────────────────────────────
        with gr.Group(elem_classes=["cc-upload-zone"]):
            gr.HTML(
                '<div class="cc-upload-area">'
                '  <span class="cc-upload-icon">📷</span>'
                '  <div style="font-size:15px;font-weight:600;color:#1C1C1E;margin-bottom:4px">'
                '    Upload Photos</div>'
                '  <div style="font-size:13px;color:#6B7280">'
                '    Take or select photos of your clothes</div>'
                '</div>'
            )
            upload_image = gr.Image(
                label="Clothing photo",
                type="pil",
                sources=["upload", "webcam"],
                show_label=False,
                height=220,
            )

        label_input = gr.Textbox(
            placeholder="Optional label (e.g. 'Favourite jacket')",
            show_label=False,
            max_lines=1,
            elem_classes=["cc-input"],
        )

        tag_btn = gr.Button(
            "Tag & Add to Wardrobe",
            elem_classes=["cc-btn-primary"],
        )

        # ── Progress steps ────────────────────────────────────────────────────
        steps_html  = gr.HTML("")
        result_html = gr.HTML("")

        # ── Post-upload actions ───────────────────────────────────────────────
        with gr.Row(visible=False) as post_row:
            add_another_btn = gr.Button(
                "Add Another",
                elem_classes=["cc-btn-secondary"],
            )
            edit_tags_btn = gr.Button(
                "Edit Tags →",
                elem_classes=["cc-btn-violet"],
            )

        # ── Wire ──────────────────────────────────────────────────────────────
        tag_btn.click(
            fn=lambda img, lbl: (
                _steps_html("running"), "", "", gr.update(visible=False)
            ),
            inputs=[upload_image, label_input],
            outputs=[steps_html, result_html, last_item_id, post_row],
        ).then(
            fn=handle_tag,
            inputs=[upload_image, label_input],
            outputs=[steps_html, result_html, last_item_id, post_row],
        )

        add_another_btn.click(
            fn=handle_reset,
            outputs=[upload_image, label_input, steps_html, result_html,
                     last_item_id, post_row],
        )

        edit_tags_btn.click(
            fn=go_edit_item_fn,
            inputs=[last_item_id],
            outputs=[],
        )

    return last_item_id
