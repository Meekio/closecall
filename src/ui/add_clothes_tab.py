"""
Add Clothes Tab — CloseCall
────────────────────────────
Desktop: upload panel and tag-result metadata shown side-by-side.
Mobile:  stacked vertically.

Flow:
  1. Upload photo.
  2. Click "Analyze item" → vision tagging with step checklist.
  3. Review detected tags.
  4. Save or Edit tags.
"""

from __future__ import annotations
import io
import gradio as gr
from PIL import Image

from src.vision.uploader import upload_from_pil


# ─── image coercion (Gradio 6 FileData compat) ────────────────────────────────

def _to_pil(image) -> Image.Image | None:
    if image is None:
        return None
    if isinstance(image, dict):
        path = image.get("path", "")
        if not path:
            return None
        try:
            return Image.open(path).convert("RGB")
        except Exception:
            try:
                return Image.open(io.BytesIO(open(path, "rb").read())).convert("RGB")
            except Exception:
                return None
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    return None


# ─── step checklist HTML ──────────────────────────────────────────────────────

_STEPS = [
    "Category detected",
    "Type detected",
    "Colour detected",
    "Formality estimated",
    "Season assessed",
]

def _steps_html(phase: str) -> str:
    """phase: idle | running | done | error"""
    if phase == "idle":
        return ""

    colors  = {"done": "#16A34A", "spin": "#7C5CFC", "wait": "#D1D5DB", "error": "#DC2626"}
    icons   = {"done": "✓", "spin": "…", "wait": "○", "error": "✕"}

    def _state(i):
        if phase == "error":
            return "error" if i == 0 else "wait"
        if phase == "done":
            return "done"
        return "spin" if i == 0 else "wait"

    rows = "".join(
        f'<div style="display:flex;align-items:center;gap:10px;padding:6px 0;'
        f'font-size:14px;color:#374151">'
        f'  <span style="color:{colors[_state(i)]};font-weight:700;width:16px;'
        f'text-align:center">{icons[_state(i)]}</span>'
        f'  <span>{step}</span>'
        f'</div>'
        for i, step in enumerate(_STEPS)
    )

    heading = {
        "running": '<div style="font-size:13px;font-weight:700;letter-spacing:1px;'
                   'text-transform:uppercase;color:#7C5CFC;margin-bottom:12px">'
                   'Analyzing your item…</div>',
        "done":    '<div style="font-size:13px;font-weight:700;letter-spacing:1px;'
                   'text-transform:uppercase;color:#16A34A;margin-bottom:12px">'
                   'Item tagged ✓</div>',
        "error":   '<div style="font-size:13px;font-weight:700;letter-spacing:1px;'
                   'text-transform:uppercase;color:#DC2626;margin-bottom:12px">'
                   'Tagging failed</div>',
    }.get(phase, "")

    return f'<div class="cc-agent-steps">{heading}{rows}</div>'


# ─── result card HTML ─────────────────────────────────────────────────────────

def _result_html(item: dict) -> str:
    name     = f"{item.get('color','').title()} {item.get('subtype','').replace('_',' ').title()}".strip()
    seasons  = ", ".join(item.get("season") or [])
    rain     = "Yes" if item.get("rain_suitable") else "No"
    conf_pct = int((item.get("confidence") or 0) * 100)
    fmap     = {1:"Loungewear",2:"Casual",3:"Smart casual",4:"Business casual",5:"Formal"}
    formality_str = fmap.get(item.get("formality", 2), "")

    rows = [
        ("Category",  item.get("category","").title()),
        ("Type",      item.get("subtype","").replace("_"," ").title()),
        ("Colour",    item.get("color","").title()),
        ("Formality", formality_str),
        ("Season",    seasons),
        ("Rain",      rain),
        ("Status",    item.get("status","clean").title()),
    ]
    rows_html = "".join(
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:10px 0;border-bottom:1px solid #F0EDE8;font-size:14px">'
        f'  <span style="color:#374151;font-weight:500">{label}</span>'
        f'  <span style="color:#1A1A1A;font-weight:600">{value}</span>'
        f'</div>'
        for label, value in rows
    )

    bar_width = f"{conf_pct}%"

    return f"""
<div class="cc-card" style="margin-top:0">
  <div style="font-size:17px;font-weight:700;color:#1A1A1A;margin-bottom:16px">{name}</div>
  {rows_html}
  <div style="margin-top:16px">
    <div style="font-size:12px;color:#6B7280;margin-bottom:6px;font-weight:500">
      AI confidence</div>
    <div class="cc-confidence-bar">
      <div class="cc-confidence-fill" style="width:{bar_width}"></div>
    </div>
    <div style="font-size:12px;color:#7C5CFC;margin-top:4px;font-weight:600">
      {conf_pct}%</div>
  </div>
  <div style="font-size:11px;color:#C8C3BB;margin-top:10px">ID: {item.get('item_id','')}</div>
</div>
"""


# ─── event handlers ───────────────────────────────────────────────────────────

def handle_tag(image, label: str):
    pil = _to_pil(image)
    if pil is None:
        err = '<div class="cc-error-box" style="margin-top:0"><strong>No image.</strong> Please upload a photo first.</div>'
        return _steps_html("error"), err, "", gr.update(visible=False)
    try:
        item   = upload_from_pil(pil, label=label.strip() or None)
        steps  = _steps_html("done")
        result = _result_html(item)
        return steps, result, item["item_id"], gr.update(visible=True)
    except Exception as exc:
        steps = _steps_html("error")
        err   = f'<div class="cc-error-box" style="margin-top:8px">{exc}</div>'
        return steps, err, "", gr.update(visible=False)


def handle_reset():
    return None, "", _steps_html("idle"), "", "", gr.update(visible=False)


# ─── tab builder ──────────────────────────────────────────────────────────────

def build_add_clothes_tab(go_edit_item_fn) -> gr.State:
    """
    Build the Add Clothes tab.

    Returns
    -------
    gr.State  — holds the last uploaded item_id (used by edit button).
    """

    last_item_id = gr.State("")

    with gr.Column(elem_classes=["cc-page"]):

        # Page header
        gr.HTML("""
<div style="padding: 40px 0 28px">
  <h2 style="font-size:clamp(22px,2.5vw,32px);font-weight:800;color:#1A1A1A;
      letter-spacing:-0.5px;margin:0 0 8px">Add to wardrobe</h2>
  <p style="font-size:14px;color:#374151;margin:0">
    Upload a photo of one clothing item. CloseCall will tag it automatically.</p>
</div>
""")

        # ── Two-column layout on desktop, stacked on mobile ───────────────────
        # We use a CSS grid trick via an HTML wrapper + inner Gradio columns.
        # Left: upload. Right: result metadata.

        with gr.Row(equal_height=False):

            # ── LEFT: upload panel ────────────────────────────────────────────
            with gr.Column(scale=1, min_width=280):

                gr.HTML("""
<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin-bottom:10px">
  Upload a photo
</div>
""")
                with gr.Group(elem_classes=["cc-upload-zone"]):
                    upload_image = gr.Image(
                        label="Clothing photo",
                        type="pil",
                        sources=["upload", "webcam"],
                        show_label=False,
                        height=280,
                    )

                label_input = gr.Textbox(
                    placeholder="Optional label — e.g. 'Favourite jacket'",
                    show_label=False,
                    max_lines=1,
                    elem_classes=["cc-input"],
                )

                analyze_btn = gr.Button(
                    "Analyze item",
                    elem_classes=["cc-btn-primary"],
                )

                steps_html = gr.HTML("")

            # ── RIGHT: result panel ───────────────────────────────────────────
            with gr.Column(scale=1, min_width=280):

                gr.HTML("""
<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin-bottom:10px">
  Detected tags
</div>
""")

                result_html = gr.HTML("""
<div style="background:#FDFCFA;border:1.5px dashed #D1CCC4;border-radius:14px;
     padding:40px 24px;text-align:center;color:#C8C3BB">
  <div style="font-size:28px;margin-bottom:10px">◻</div>
  <div style="font-size:14px">Upload a photo and click<br>Analyze item</div>
</div>
""")

                with gr.Row(visible=False) as post_row:
                    with gr.Column(scale=1):
                        add_another_btn = gr.Button(
                            "Add another",
                            elem_classes=["cc-btn-secondary"],
                        )
                    with gr.Column(scale=1):
                        edit_tags_btn = gr.Button(
                            "Edit tags →",
                            elem_classes=["cc-btn-accent"],
                        )

        gr.HTML('<div style="height:40px"></div>')

        # ── Wire ──────────────────────────────────────────────────────────────
        analyze_btn.click(
            fn=lambda img, lbl: (_steps_html("running"), """
<div style="background:#FDFCFA;border:1.5px dashed #D1CCC4;border-radius:14px;
     padding:40px 24px;text-align:center;color:#C8C3BB">
  <div style="font-size:14px;color:#7C5CFC">Analyzing…</div>
</div>
""", "", gr.update(visible=False)),
            inputs=[upload_image, label_input],
            outputs=[steps_html, result_html, last_item_id, post_row],
        ).then(
            fn=handle_tag,
            inputs=[upload_image, label_input],
            outputs=[steps_html, result_html, last_item_id, post_row],
        )

        add_another_btn.click(
            fn=handle_reset,
            outputs=[upload_image, label_input, steps_html, result_html, last_item_id, post_row],
        )

        edit_tags_btn.click(
            fn=go_edit_item_fn,
            inputs=[last_item_id],
            outputs=[],
        )

    return last_item_id
