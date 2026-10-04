"""
Screen 5 — Item Details / Edit Tags
─────────────────────────────────────
Displays the item image (if available), auto-filled dropdowns,
a 1-5 formality slider, season chips, clean/dirty toggle, and Save.
Can be pre-loaded with an item_id from the Add Clothes or Wardrobe screens.
"""

from __future__ import annotations
import gradio as gr

from src.database.db import get_item_dict, update_item, delete_item, get_all_items

_CATEGORIES = ["top", "bottom", "one_piece", "footwear", "outerwear"]
_SUBTYPES = [
    "t-shirt", "shirt", "kurti", "jeans", "trousers", "leggings",
    "palazzo", "sneakers", "formal_shoes", "flats", "sandals",
    "chappal", "jacket", "dress", "skirt", "shorts", "blazer",
    "coat", "saree", "unknown",
]
_SEASONS_ALL = ["Summer", "Winter", "Monsoon", "Spring", "All-season"]
_FORMALITY_LABELS = {1:"Loungewear",2:"Casual",3:"Smart Casual",4:"Business Casual",5:"Formal"}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _formality_label(f: int) -> str:
    return f"{f} · {_FORMALITY_LABELS.get(f, '')}"


def _seasons_from_item(item: dict) -> list[str]:
    raw = item.get("season") or []
    return [s.title() for s in raw]


def _load_item(item_id: str):
    """Return component updates pre-filled from the DB item."""
    if not item_id:
        return _empty_state()
    item = get_item_dict(item_id.strip())
    if item is None:
        return _empty_state()

    img_path = item.get("image_path") or None
    return (
        item_id,
        img_path,
        item.get("category", "top"),
        item.get("subtype", "t-shirt"),
        item.get("color", ""),
        item.get("formality", 2),
        _seasons_from_item(item),
        item.get("status", "clean") == "clean",   # True = clean
        gr.update(value="", visible=False),         # save_msg
        gr.update(visible=True),                    # save_btn
        gr.update(visible=True),                    # delete_btn
    )


def _empty_state():
    return (
        "",       # item_id_state
        None,     # image
        "top",    # category
        "t-shirt",# subtype
        "",       # color
        2,        # formality
        [],       # seasons
        True,     # is_clean
        gr.update(value="", visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def handle_load_by_id(item_id: str):
    return _load_item(item_id)


def handle_save(item_id, category, subtype, color, formality, seasons, is_clean):
    if not item_id:
        return gr.update(value="⚠️ No item selected.", visible=True)
    season_list = [s.lower() for s in (seasons or [])]
    updates = {
        "category":     category,
        "subtype":      subtype,
        "color":        color.strip(),
        "formality":    int(formality),
        "season":       season_list,
        "status":       "clean" if is_clean else "dirty",
    }
    result = update_item(item_id, updates)
    if result is None:
        return gr.update(value=f"❌ Item `{item_id}` not found.", visible=True)
    return gr.update(value="✅ Tags saved!", visible=True)


def handle_delete(item_id):
    if not item_id:
        return gr.update(value="⚠️ No item selected.", visible=True)
    success = delete_item(item_id)
    if success:
        return gr.update(value="🗑️ Item deleted.", visible=True)
    return gr.update(value=f"❌ Item `{item_id}` not found.", visible=True)


# ─── wardrobe item picker helper (shown above form) ──────────────────────────

def _item_choices() -> list[str]:
    items = get_all_items()
    return [
        f"{i['item_id']} — {i['color']} {i['subtype']}"
        for i in items
    ]


# ─── tab builder ──────────────────────────────────────────────────────────────

def build_item_detail_tab() -> gr.State:
    """
    Build the Item Detail / Edit Tags tab.
    Returns a gr.State holding the currently-loaded item_id,
    so external tabs can write into it to pre-load an item.
    """

    item_id_state = gr.State("")

    with gr.Column(elem_classes=["cc-screen"]):

        gr.HTML(
            '<div style="font-size:20px;font-weight:700;color:#1C1C1E;'
            'padding:8px 0 12px">✏️ Item Details</div>'
        )

        # ── Item picker (select from wardrobe) ────────────────────────────────
        with gr.Group():
            item_picker = gr.Dropdown(
                label="Select item to edit",
                choices=_item_choices(),
                value=None,
                allow_custom_value=False,
                elem_classes=["cc-select"],
            )
            refresh_picker_btn = gr.Button("🔄 Refresh list", size="sm", elem_classes=["cc-chip"])

        # ── Item image ────────────────────────────────────────────────────────
        item_image = gr.Image(
            label="",
            show_label=False,
            interactive=False,
            height=200,
            visible=True,
        )

        # ── Tag fields ────────────────────────────────────────────────────────
        with gr.Group(elem_classes=["cc-card"]):

            gr.HTML('<div class="cc-section-title">Tags</div>')

            category_dd = gr.Dropdown(
                choices=_CATEGORIES,
                label="Category",
                value="top",
                elem_classes=["cc-select"],
            )
            subtype_dd = gr.Dropdown(
                choices=_SUBTYPES,
                label="Subtype",
                value="t-shirt",
                elem_classes=["cc-select"],
            )
            color_box = gr.Textbox(
                label="Color",
                placeholder="e.g. White",
                elem_classes=["cc-input"],
                max_lines=1,
            )

            gr.HTML('<div class="cc-label" style="margin-top:8px">Formality</div>')
            formality_slider = gr.Slider(
                minimum=1, maximum=5, step=1,
                value=2,
                label="Formality",
                show_label=False,
                elem_classes=["cc-formality-slider"],
            )
            # Live formality label
            formality_label_html = gr.HTML(
                f'<div style="text-align:center;font-size:13px;color:#6B7280;margin-bottom:8px">'
                f'2 · Casual</div>'
            )
            formality_slider.change(
                fn=lambda v: f'<div style="text-align:center;font-size:13px;color:#6D28D9;'
                             f'font-weight:600;margin-bottom:8px">{_formality_label(int(v))}</div>',
                inputs=[formality_slider],
                outputs=[formality_label_html],
            )

            gr.HTML('<div class="cc-label" style="margin-top:8px">Season</div>')
            season_cb = gr.CheckboxGroup(
                choices=_SEASONS_ALL,
                label="Season",
                show_label=False,
                value=[],
            )

            gr.HTML('<div class="cc-label" style="margin-top:8px">Status</div>')
            status_radio = gr.Radio(
                choices=["Clean", "Dirty"],
                label="Status",
                show_label=False,
                value="Clean",
            )

        # ── Action buttons ────────────────────────────────────────────────────
        save_btn   = gr.Button("💾  Save Item", elem_classes=["cc-btn-primary"],  visible=False)
        delete_btn = gr.Button("🗑️  Delete",   elem_classes=["cc-btn-secondary"], visible=False)
        save_msg   = gr.HTML("", visible=False)

        # ─────────────────────────────────────────────────────────────────────
        # Outputs order for _load_item / handle_load_by_id:
        # item_id_state, item_image, category_dd, subtype_dd, color_box,
        # formality_slider, season_cb, is_clean→status_radio,
        # save_msg, save_btn, delete_btn
        # ─────────────────────────────────────────────────────────────────────

        _LOAD_OUTPUTS = [
            item_id_state, item_image, category_dd, subtype_dd, color_box,
            formality_slider, season_cb, status_radio,
            save_msg, save_btn, delete_btn,
        ]

        def _status_bool_to_radio(item_id, img, cat, sub, col, form, seas, is_clean, sm, sb, db_):
            status_val = "Clean" if is_clean else "Dirty"
            return item_id, img, cat, sub, col, form, seas, status_val, sm, sb, db_

        def _load_and_convert(iid):
            raw = _load_item(iid)
            return _status_bool_to_radio(*raw)

        # Picker → load
        item_picker.change(
            fn=lambda choice: _load_and_convert(choice.split(" — ")[0] if choice else ""),
            inputs=[item_picker],
            outputs=_LOAD_OUTPUTS,
        )

        # Refresh picker list
        refresh_picker_btn.click(
            fn=lambda: gr.update(choices=_item_choices()),
            outputs=[item_picker],
        )

        # Save
        save_btn.click(
            fn=lambda iid, cat, sub, col, form, seas, stat: handle_save(
                iid, cat, sub, col, form, seas, stat == "Clean"
            ),
            inputs=[item_id_state, category_dd, subtype_dd, color_box,
                    formality_slider, season_cb, status_radio],
            outputs=[save_msg],
        )

        # Delete
        delete_btn.click(
            fn=lambda iid: handle_delete(iid),
            inputs=[item_id_state],
            outputs=[save_msg],
        )

    return item_id_state
