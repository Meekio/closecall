"""
Screen 6 — My Wardrobe
───────────────────────
• Search bar
• Filter chips: All / Tops / Bottoms / One-pieces / Footwear / Outerwear
• 3-column image grid with item cards (image + name + status badge)
• Tap a card → pre-load Item Detail tab
"""

from __future__ import annotations
import os
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
_FORMALITY_LABELS = {1:"Loungewear",2:"Casual",3:"Smart Casual",4:"Business Casual",5:"Formal"}


# ─── HTML grid builder ────────────────────────────────────────────────────────

def _item_card_html(item: dict) -> str:
    name = item.get("label") or f"{item.get('color','').title()} {item.get('subtype','').replace('_',' ').title()}"
    status = item.get("status","clean")
    badge_color = "#22C55E" if status == "clean" else "#EF4444"
    badge_bg    = "#DCFCE7" if status == "clean" else "#FEE2E2"
    formality   = _FORMALITY_LABELS.get(item.get("formality",2),"")

    img_path = item.get("image_path","")
    if img_path and Path(img_path).exists():
        # Use a data URI so Gradio HTML component can render it
        import base64
        try:
            data = Path(img_path).read_bytes()
            b64  = base64.b64encode(data).decode()
            ext  = Path(img_path).suffix.lower().lstrip(".")
            mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png","webp":"webp"}.get(ext,"jpeg")
            img_src = f"data:image/{mime};base64,{b64}"
        except Exception:
            img_src = ""
    else:
        img_src = ""

    img_html = (
        f'<img src="{img_src}" style="width:100%;height:100%;object-fit:cover;'
        f'border-radius:10px" />'
        if img_src else
        '<div style="width:100%;height:100%;background:#F3F4F6;border-radius:10px;'
        'display:flex;align-items:center;justify-content:center;font-size:14px;color:#9CA3AF;font-weight:600">•</div>'
    )

    return f"""
<div style="border-radius:12px;background:#fff;overflow:hidden;
     box-shadow:0 1px 4px rgba(0,0,0,0.08);border:1px solid #F3F4F6">
  <div style="aspect-ratio:1;overflow:hidden;background:#F9FAFB">
    {img_html}
  </div>
  <div style="padding:8px">
    <div style="font-size:12px;font-weight:600;color:#1C1C1E;
         white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{name}</div>
    <div style="font-size:10px;color:#6B7280;margin:2px 0">{formality}</div>
    <span style="display:inline-block;background:{badge_bg};color:{badge_color};
          border-radius:20px;padding:2px 8px;font-size:10px;font-weight:600">
      {status.title()}
    </span>
  </div>
</div>
"""


def _grid_html(items: list[dict]) -> str:
    if not items:
        return (
            '<div style="text-align:center;padding:48px 24px;color:#9CA3AF">'
            '  <div style="font-size:16px;margin-bottom:12px;color:#9CA3AF;font-weight:600">WARDROBE</div>'
            '  <div style="font-size:15px;font-weight:600;color:#6B7280">No items yet</div>'
            '  <div style="font-size:13px;margin-top:4px">Go to Add Clothes to upload your wardrobe.</div>'
            '</div>'
        )
    cards = "".join(f'<div>{_item_card_html(i)}</div>' for i in items)
    return (
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);'
        f'gap:8px;padding:4px 0">{cards}</div>'
    )


# ─── event handlers ───────────────────────────────────────────────────────────

def handle_filter(category_label: str, search: str) -> str:
    cat = _CATEGORY_MAP.get(category_label, "")
    items = get_items_by_category(category=cat)
    if search.strip():
        q = search.strip().lower()
        items = [
            i for i in items
            if q in (i.get("color","") + i.get("subtype","") + (i.get("label") or "")).lower()
        ]
    return _grid_html(items)


def handle_refresh_grid() -> tuple[str, list[str]]:
    items = get_all_items()
    return _grid_html(items), [
        f"{i['item_id']} — {i.get('color','')} {i.get('subtype','')}"
        for i in items
    ]


# ─── tab builder ──────────────────────────────────────────────────────────────

def build_wardrobe_tab(go_edit_fn) -> None:
    """
    Build the Wardrobe tab.

    Parameters
    ----------
    go_edit_fn : callable(item_id: str)
        Called when user selects an item to edit from the dropdown.
    """

    with gr.Column(elem_classes=["cc-screen"]):

        # ── Header ────────────────────────────────────────────────────────────
        with gr.Row():
            gr.HTML(
                '<div style="font-size:20px;font-weight:700;color:#1C1C1E;'
                'padding:8px 0 12px;flex:1">My Wardrobe</div>'
            )
            refresh_btn = gr.Button("🔄", size="sm", elem_classes=["cc-chip"])

        # ── Search ────────────────────────────────────────────────────────────
        search_input = gr.Textbox(
            placeholder="Search items...",
            show_label=False,
            max_lines=1,
            elem_classes=["cc-input"],
        )

        # ── Filter chips ──────────────────────────────────────────────────────
        active_filter = gr.State("All")

        with gr.Row(elem_classes=["cc-chips"]):
            filter_btns = [
                gr.Button(label, elem_classes=["cc-chip"], size="sm")
                for label in _CATEGORY_FILTERS
            ]

        # ── Wardrobe grid ─────────────────────────────────────────────────────
        grid_html = gr.HTML(_grid_html(get_all_items()))

        # ── Item selector (for edit) ──────────────────────────────────────────
        gr.HTML('<div class="cc-label" style="margin-top:16px">Tap to edit an item</div>')
        edit_picker = gr.Dropdown(
            label="Select item",
            choices=[
                f"{i['item_id']} — {i.get('color','')} {i.get('subtype','')}"
                for i in get_all_items()
            ],
            value=None,
            allow_custom_value=False,
            show_label=False,
            elem_classes=["cc-select"],
        )
        edit_btn = gr.Button("✏️  Edit Selected Item", elem_classes=["cc-btn-secondary"])

        # ── Wire filter chips ─────────────────────────────────────────────────
        for btn, label in zip(filter_btns, _CATEGORY_FILTERS):
            btn.click(
                fn=lambda s, lbl=label: handle_filter(lbl, s),
                inputs=[search_input],
                outputs=[grid_html],
            )

        # Live search
        search_input.change(
            fn=lambda s, f: handle_filter(f, s),
            inputs=[search_input, active_filter],
            outputs=[grid_html],
        )

        # Refresh
        refresh_btn.click(
            fn=lambda: handle_refresh_grid()[0],
            outputs=[grid_html],
        ).then(
            fn=lambda: gr.update(choices=handle_refresh_grid()[1]),
            outputs=[edit_picker],
        )

        # Edit selected item
        edit_btn.click(
            fn=lambda choice: go_edit_fn(choice.split(" — ")[0] if choice else ""),
            inputs=[edit_picker],
            outputs=[],
        )
