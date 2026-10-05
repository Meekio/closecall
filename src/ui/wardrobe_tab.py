"""
Wardrobe Tab — CloseCall
─────────────────────────
Desktop: 4-column responsive grid, search bar, category filter chips.
Tablet : 3 columns.
Mobile : 2 columns.
Each card shows the clothing image, name, formality label, clean/dirty badge.
"""

from __future__ import annotations
import base64
from pathlib import Path
import gradio as gr

from src.database.db import get_all_items, get_items_by_category

_CATEGORY_FILTERS = ["All", "Tops", "Bottoms", "One-pieces", "Footwear", "Outerwear"]
_CATEGORY_MAP = {
    "All": "",
    "Tops": "top",
    "Bottoms": "bottom",
    "One-pieces": "one_piece",
    "Footwear": "footwear",
    "Outerwear": "outerwear",
}
_FORMALITY_LABELS = {
    1: "Loungewear",
    2: "Casual",
    3: "Smart casual",
    4: "Business casual",
    5: "Formal",
}


# ─── HTML helpers ──────────────────────────────────────────────────────────────

def _img_src(item: dict) -> str:
    img_path = item.get("image_path", "")
    if img_path and Path(img_path).exists():
        try:
            data = Path(img_path).read_bytes()
            b64  = base64.b64encode(data).decode()
            ext  = Path(img_path).suffix.lower().lstrip(".")
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
            return f"data:image/{mime};base64,{b64}"
        except Exception:
            pass
    return ""


def _item_card_html(item: dict) -> str:
    name = (
        item.get("label")
        or f"{item.get('color', '').title()} {item.get('subtype', '').replace('_', ' ').title()}"
    ).strip()
    status      = item.get("status", "clean")
    formality   = _FORMALITY_LABELS.get(item.get("formality", 2), "")
    src         = _img_src(item)

    img_html = (
        f'<img src="{src}" alt="{name}" '
        f'style="width:100%;height:100%;object-fit:cover;display:block" />'
        if src else
        f'<div style="width:100%;height:100%;background:#F0EDE8;'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:28px;color:#C8C3BB">◻</div>'
    )

    badge = (
        '<span class="cc-badge-clean">● Clean</span>'
        if status == "clean" else
        '<span class="cc-badge-dirty">● Dirty</span>'
    )

    return f"""
<div class="cc-item-card">
  <div style="aspect-ratio:1;overflow:hidden;background:#F8F6F3">
    {img_html}
  </div>
  <div style="padding:10px 12px 12px">
    <div style="font-size:13px;font-weight:600;color:#1A1A1A;
         white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
         margin-bottom:3px">{name}</div>
    <div style="font-size:11px;color:#6B7280;margin-bottom:6px">{formality}</div>
    {badge}
  </div>
</div>
"""


def _section_header_html(label: str, count: int) -> str:
    return (
        f'<div style="font-size:11px;font-weight:700;letter-spacing:1px;'
        f'text-transform:uppercase;color:#6B7280;margin:28px 0 12px">'
        f'{label.upper()} · {count}</div>'
    )


def _grid_html(items: list[dict]) -> str:
    if not items:
        return """
<div style="text-align:center;padding:64px 24px;color:#6B7280">
  <div style="font-size:40px;margin-bottom:16px">◻</div>
  <div style="font-size:17px;font-weight:600;color:#374151;margin-bottom:8px">
    Your wardrobe is empty</div>
  <div style="font-size:14px;color:#6B7280">
    Add a few clothes and CloseCall can start building outfits.</div>
</div>
"""

    # Group by category for section headers
    by_cat: dict[str, list] = {}
    for item in items:
        cat = item.get("category", "other")
        by_cat.setdefault(cat, []).append(item)

    cat_display = {
        "top": "Tops", "bottom": "Bottoms", "one_piece": "One-pieces",
        "footwear": "Footwear", "outerwear": "Outerwear", "other": "Other",
    }

    html = ""
    for cat, cat_items in by_cat.items():
        label = cat_display.get(cat, cat.title())
        html += _section_header_html(label, len(cat_items))
        cards = "".join(f'<div>{_item_card_html(i)}</div>' for i in cat_items)
        html += f'<div class="cc-wardrobe-grid">{cards}</div>'

    return html


# ─── event handlers ───────────────────────────────────────────────────────────

def handle_filter(category_label: str, search: str) -> str:
    cat   = _CATEGORY_MAP.get(category_label, "")
    items = get_items_by_category(category=cat)
    if search.strip():
        q     = search.strip().lower()
        items = [
            i for i in items
            if q in (
                (i.get("color") or "") + " " +
                (i.get("subtype") or "") + " " +
                (i.get("label") or "")
            ).lower()
        ]
    return _grid_html(items)


def _item_choices() -> list[str]:
    return [
        f"{i['item_id']} — {i.get('color', '')} {i.get('subtype', '')}"
        for i in get_all_items()
    ]


# ─── tab builder ──────────────────────────────────────────────────────────────

def build_wardrobe_tab(go_add_fn, go_edit_fn) -> None:
    """
    Build the Wardrobe tab.

    Parameters
    ----------
    go_add_fn : callable
        Switches to Add Clothes sub-view.
    go_edit_fn : callable(item_id: str)
        Switches to Item Detail sub-view with the given item pre-loaded.
    """

    with gr.Column(elem_classes=["cc-page"]):

        # ── Page header ───────────────────────────────────────────────────────
        with gr.Row(elem_id="wardrobe-header"):
            gr.HTML("""
<div style="padding: 40px 0 20px">
  <h2 style="font-size:clamp(22px,2.5vw,32px);font-weight:800;color:#1A1A1A;
      letter-spacing:-0.5px;margin:0">My Wardrobe</h2>
</div>
""")
            with gr.Column(scale=0, min_width=160):
                gr.HTML('<div style="padding-top:40px"></div>')
                add_btn = gr.Button("+ Add clothes", elem_classes=["cc-btn-accent"])

        # ── Search bar ────────────────────────────────────────────────────────
        search_input = gr.Textbox(
            placeholder="Search your wardrobe…",
            show_label=False,
            max_lines=1,
            elem_classes=["cc-input"],
        )

        # ── Filter chips ──────────────────────────────────────────────────────
        gr.HTML('<div style="height:12px"></div>')
        active_filter = gr.State("All")

        with gr.Row(elem_classes=["cc-chips"]):
            filter_btns = [
                gr.Button(label, elem_classes=["cc-chip"], size="sm")
                for label in _CATEGORY_FILTERS
            ]

        gr.HTML('<div style="height:8px"></div>')

        # ── Wardrobe grid ─────────────────────────────────────────────────────
        grid_html = gr.HTML(_grid_html(get_all_items()))

        # ── Item picker for edit ──────────────────────────────────────────────
        gr.HTML("""
<hr style="border:none;border-top:1px solid #E8E5E0;margin:32px 0 20px">
<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin-bottom:10px">
  Edit an item
</div>
""")
        with gr.Row():
            with gr.Column(scale=3):
                edit_picker = gr.Dropdown(
                    choices=_item_choices(),
                    value=None,
                    show_label=False,
                    allow_custom_value=False,
                    elem_classes=["cc-select"],
                    label="Select item to edit",
                )
            with gr.Column(scale=1, min_width=140):
                edit_btn = gr.Button("Edit tags →", elem_classes=["cc-btn-secondary"])

        gr.HTML('<div style="height:40px"></div>')

        # ── Wire filter chips ─────────────────────────────────────────────────
        for btn, label in zip(filter_btns, _CATEGORY_FILTERS):
            btn.click(
                fn=lambda s, lbl=label: (handle_filter(lbl, s), lbl),
                inputs=[search_input],
                outputs=[grid_html, active_filter],
            )

        # Live search
        search_input.change(
            fn=lambda s, f: handle_filter(f, s),
            inputs=[search_input, active_filter],
            outputs=[grid_html],
        )

        # Edit
        edit_btn.click(
            fn=lambda choice: go_edit_fn(choice.split(" — ")[0] if choice else ""),
            inputs=[edit_picker],
            outputs=[],
        )

        # Add clothes nav
        add_btn.click(fn=go_add_fn, outputs=[])
