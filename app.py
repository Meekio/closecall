"""
CloseCall — AI Personal Stylist
Entry point.  Run:  python app.py
"""

import sys
import socket
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gradio as gr

from src.config import config
from src.database.db import init_db
from src.ui.styles import APP_CSS

from src.ui.home_tab        import build_home_tab
from src.ui.add_clothes_tab import build_add_clothes_tab
from src.ui.item_detail_tab import build_item_detail_tab
from src.ui.wardrobe_tab    import build_wardrobe_tab
from src.ui.outfits_tab     import build_outfits_tab
from src.ui.profile_tab     import build_profile_tab


def _get_wifi_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "localhost"


def build_app() -> gr.Blocks:

    with gr.Blocks(title="CloseCall", css=APP_CSS) as app:

        # ── Shared state ──────────────────────────────────────────────────
        prefill_request_state = gr.State("")

        # ── Main tabs ─────────────────────────────────────────────────────
        with gr.Tabs(elem_id="main-tabs") as main_tabs:

            # ── Tab 1: Home ───────────────────────────────────────────────
            with gr.Tab("Home", id="tab-home"):
                # These buttons/inputs are built inside build_home_tab;
                # we capture nav callbacks after all Columns are defined.
                home_submit_input = gr.State("")   # holds request text

                # Build home — nav fns wired after wardrobe columns exist
                # We pass dummy lambdas first, then wire real ones below
                # by capturing the button references from inside the tab.
                # Simpler pattern: build everything, then wire cross-tab
                # events using the returned component references.
                (
                    home_request_box,
                    home_submit_btn,
                    home_add_btn,
                    home_ward_btn,
                ) = _build_home_inner()

            # ── Tab 2: Wardrobe ───────────────────────────────────────────
            with gr.Tab("Wardrobe", id="tab-wardrobe"):

                with gr.Column(visible=True) as wv_grid:
                    (
                        ward_add_btn,
                        ward_edit_picker,
                        ward_edit_btn,
                    ) = _build_wardrobe_inner()

                with gr.Column(visible=False) as wv_add:
                    add_last_item_id = _build_add_inner()
                    add_edit_btn_ref = gr.State("")   # placeholder

                with gr.Column(visible=False) as wv_detail:
                    build_item_detail_tab()

            # ── Tab 3: Outfits ────────────────────────────────────────────
            with gr.Tab("Outfits", id="tab-outfits"):
                build_outfits_tab(prefill_state=prefill_request_state)

            # ── Tab 4: Profile ────────────────────────────────────────────
            with gr.Tab("Profile", id="tab-profile"):
                build_profile_tab()

        # ── Cross-tab wiring ──────────────────────────────────────────────

        _WV_OUTS = [wv_grid, wv_add, wv_detail]

        def _wv(grid=False, add=False, detail=False):
            return (gr.update(visible=grid), gr.update(visible=add), gr.update(visible=detail))

        # Home submit → pre-fill Outfits + switch tab
        home_submit_btn.click(
            fn=lambda req: req,
            inputs=[home_request_box],
            outputs=[prefill_request_state],
        ).then(
            fn=lambda: gr.update(selected="tab-outfits"),
            outputs=[main_tabs],
        )

        home_request_box.submit(
            fn=lambda req: req,
            inputs=[home_request_box],
            outputs=[prefill_request_state],
        ).then(
            fn=lambda: gr.update(selected="tab-outfits"),
            outputs=[main_tabs],
        )

        # Home → Add clothes
        home_add_btn.click(
            fn=lambda: (gr.update(selected="tab-wardrobe"), *_wv(add=True)),
            outputs=[main_tabs, *_WV_OUTS],
        )

        # Home → Wardrobe grid
        home_ward_btn.click(
            fn=lambda: (gr.update(selected="tab-wardrobe"), *_wv(grid=True)),
            outputs=[main_tabs, *_WV_OUTS],
        )

        # Wardrobe → Add clothes sub-view
        ward_add_btn.click(
            fn=lambda: _wv(add=True),
            outputs=_WV_OUTS,
        )

        # Wardrobe → Item detail sub-view
        ward_edit_btn.click(
            fn=lambda choice: _wv(detail=True),
            inputs=[ward_edit_picker],
            outputs=_WV_OUTS,
        )

    return app


# ─── inner builders returning component refs ──────────────────────────────────
# These build the tab content and return the Gradio components that need
# cross-tab wiring, avoiding the "placeholder lambda" pattern.

def _build_home_inner():
    """Build home content, return (request_box, submit_btn, add_btn, ward_btn)."""
    from src.tools.weather import get_weather
    from src.database.profile import load_profile
    from src.database.db import get_all_items

    def _weather_html():
        profile = load_profile()
        w       = get_weather(profile.get("location", "Mumbai"))
        is_rain = w.get("is_raining", False)
        cond    = w.get("description", w.get("condition", "")).title()
        temp    = w.get("temperature_c", "–")
        city    = w.get("location", profile.get("location", ""))
        icon    = "🌧️" if is_rain else "☀️" if "clear" in cond.lower() else "⛅"
        return f"""
<div class="cc-weather-widget">
  <span style="font-size:28px;line-height:1">{icon}</span>
  <div>
    <div style="font-size:14px;font-weight:700;color:#1D3A8A">{city}</div>
    <div style="font-size:13px;color:#3B5FBF;margin-top:2px">{temp}°C · {cond}</div>
  </div>
</div>
"""

    def _wardrobe_stat_html():
        items = get_all_items()
        total = len(items)
        clean = sum(1 for i in items if i.get("status") == "clean")
        return f"""
<div style="background:#FFFFFF;border:1px solid #E8E5E0;border-radius:12px;
     padding:16px 20px;height:100%;min-height:72px;display:flex;flex-direction:column;justify-content:center">
  <div style="font-size:11px;font-weight:700;letter-spacing:1px;
       text-transform:uppercase;color:#6B7280;margin-bottom:8px">YOUR WARDROBE</div>
  <div style="font-size:24px;font-weight:800;color:#1A1A1A">{total} items</div>
  <div style="font-size:13px;color:#374151;margin-top:2px">{clean} clean · ready to wear</div>
</div>
"""

    with gr.Column(elem_classes=["cc-page"]):

        gr.HTML("""
<div style="padding:48px 0 32px">
  <div style="font-size:16px;font-weight:800;letter-spacing:1.5px;
       text-transform:uppercase;color:#4B5563;margin-bottom:16px">
    CloseCall — Your Personal Stylist
  </div>
  <h1 style="font-size:clamp(28px,4vw,52px);font-weight:800;color:#1A1A1A;
       letter-spacing:-1.5px;line-height:1.1;margin:0 0 14px">
    Your wardrobe.<br>Your plans.<br>
    <span style="color:#7C5CFC">One outfit that works.</span>
  </h1>
  <p style="font-size:clamp(14px,1.4vw,17px);color:#374151;
      line-height:1.6;max-width:540px;margin:0">
    Describe what you need and CloseCall reasons over your real wardrobe —
    checking weather, occasion, and formality — to recommend outfits that
    actually fit your day.
  </p>
</div>
""")

        gr.HTML("""
<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin-bottom:8px">
  What are you dressing for?
</div>
""")
        request_input = gr.Textbox(
            placeholder='"Casual office outfit for a rainy day…"',
            show_label=False,
            lines=1,
            max_lines=3,
            elem_classes=["cc-input"],
        )

        submit_btn = gr.Button(
            "Get outfit suggestions →",
            elem_classes=["cc-btn-primary"],
        )

        gr.HTML('<div style="font-size:12px;color:#6B7280;margin:20px 0 8px;font-weight:500">Try asking</div>')
        with gr.Row(elem_classes=["cc-chips"]):
            chip_work    = gr.Button("Work",    elem_classes=["cc-chip"], size="sm")
            chip_casual  = gr.Button("Casual",  elem_classes=["cc-chip"], size="sm")
            chip_date    = gr.Button("Date",    elem_classes=["cc-chip"], size="sm")
            chip_college = gr.Button("College", elem_classes=["cc-chip"], size="sm")
            chip_travel  = gr.Button("Travel",  elem_classes=["cc-chip"], size="sm")

        gr.HTML('<div style="height:28px"></div>')

        gr.HTML("""<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin-bottom:10px">TODAY</div>""")
        with gr.Row(equal_height=True):
            with gr.Column(scale=1, min_width=220):
                weather_widget = gr.HTML(_weather_html())
            with gr.Column(scale=1, min_width=220):
                gr.HTML(_wardrobe_stat_html())

        gr.Button("↻ Refresh weather", size="sm", elem_classes=["cc-btn-ghost"]).click(
            fn=_weather_html, outputs=[weather_widget]
        )

        gr.HTML('<div style="height:32px"></div>')
        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                add_btn  = gr.Button("+ Add clothes",    elem_classes=["cc-btn-secondary"])
            with gr.Column(scale=1):
                ward_btn = gr.Button("View wardrobe →",  elem_classes=["cc-btn-secondary"])

        gr.HTML('<div style="height:40px"></div>')

        for chip, text in [
            (chip_work,    "I need an outfit for work today."),
            (chip_casual,  "Something casual and comfortable for today."),
            (chip_date,    "A dinner date tonight — suggest something nice."),
            (chip_college, "Outfit for college today."),
            (chip_travel,  "Travelling today, need something comfortable."),
        ]:
            chip.click(fn=lambda t=text: t, outputs=[request_input])

    return request_input, submit_btn, add_btn, ward_btn


def _build_wardrobe_inner():
    """Build wardrobe grid content, return (add_btn, edit_picker, edit_btn)."""
    import base64
    from pathlib import Path as P
    from src.database.db import get_all_items, get_items_by_category

    _CAT_MAP = {
        "All": "", "Tops": "top", "Bottoms": "bottom",
        "One-pieces": "one_piece", "Footwear": "footwear", "Outerwear": "outerwear",
    }
    _FORM = {1:"Loungewear",2:"Casual",3:"Smart casual",4:"Business casual",5:"Formal"}

    def _img_src(item):
        p = item.get("image_path","")
        if p and P(p).exists():
            try:
                data = P(p).read_bytes()
                b64  = base64.b64encode(data).decode()
                ext  = P(p).suffix.lower().lstrip(".")
                mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png","webp":"webp"}.get(ext,"jpeg")
                return f"data:image/{mime};base64,{b64}"
            except Exception:
                pass
        return ""

    def _card(item):
        name   = (item.get("label") or
                  f"{item.get('color','').title()} {item.get('subtype','').replace('_',' ').title()}").strip()
        status = item.get("status","clean")
        form   = _FORM.get(item.get("formality",2),"")
        src    = _img_src(item)
        img    = (f'<img src="{src}" alt="{name}" style="width:100%;height:100%;object-fit:cover;display:block"/>'
                  if src else
                  '<div style="width:100%;height:100%;background:#F0EDE8;display:flex;'
                  'align-items:center;justify-content:center;font-size:28px;color:#C8C3BB">◻</div>')
        badge  = ('<span class="cc-badge-clean">● Clean</span>'
                  if status=="clean" else
                  '<span class="cc-badge-dirty">● Dirty</span>')
        return f"""
<div class="cc-item-card">
  <div style="aspect-ratio:1;overflow:hidden;background:#F8F6F3">{img}</div>
  <div style="padding:10px 12px 12px">
    <div style="font-size:13px;font-weight:600;color:#1A1A1A;white-space:nowrap;
         overflow:hidden;text-overflow:ellipsis;margin-bottom:3px">{name}</div>
    <div style="font-size:11px;color:#6B7280;margin-bottom:6px">{form}</div>
    {badge}
  </div>
</div>"""

    def _grid(items):
        if not items:
            return ('<div style="text-align:center;padding:64px 24px;color:#6B7280">'
                    '<div style="font-size:40px;margin-bottom:16px">◻</div>'
                    '<div style="font-size:17px;font-weight:600;color:#374151;margin-bottom:8px">'
                    'Your wardrobe is empty</div>'
                    '<div style="font-size:14px">Add a few clothes to get started.</div></div>')
        cat_display = {"top":"Tops","bottom":"Bottoms","one_piece":"One-pieces",
                       "footwear":"Footwear","outerwear":"Outerwear"}
        by_cat: dict = {}
        for i in items:
            by_cat.setdefault(i.get("category","other"), []).append(i)
        html = ""
        for cat, cat_items in by_cat.items():
            label = cat_display.get(cat, cat.title())
            html += (f'<div style="font-size:11px;font-weight:700;letter-spacing:1px;'
                     f'text-transform:uppercase;color:#6B7280;margin:28px 0 12px">'
                     f'{label.upper()} · {len(cat_items)}</div>')
            cards = "".join(f'<div>{_card(i)}</div>' for i in cat_items)
            html += f'<div class="cc-wardrobe-grid">{cards}</div>'
        return html

    def _choices():
        items = get_all_items()
        result = []
        for i in items:
            name = (i.get("label") or
                    f"{i.get('color','').title()} {i.get('subtype','').replace('_',' ').title()}").strip()
            status = "● Clean" if i.get("status") == "clean" else "● Dirty"
            result.append((f"{name}  {status}", i["item_id"]))
        return result

    def _filter(cat_label, search):
        cat   = _CAT_MAP.get(cat_label,"")
        items = get_items_by_category(category=cat)
        if search.strip():
            q = search.strip().lower()
            items = [i for i in items
                     if q in ((i.get("color","")+" "+i.get("subtype","")+" "+(i.get("label") or "")).lower())]
        return _grid(items)

    with gr.Column(elem_classes=["cc-page"]):

        with gr.Row():
            gr.HTML("""
<div style="padding:40px 0 20px;flex:1">
  <h2 style="font-size:clamp(22px,2.5vw,32px);font-weight:800;color:#1A1A1A;
      letter-spacing:-0.5px;margin:0">My Wardrobe</h2>
</div>
""")
            with gr.Column(scale=0, min_width=160):
                gr.HTML('<div style="padding-top:40px"></div>')
                add_btn = gr.Button("+ Add clothes", elem_classes=["cc-btn-accent"])

        search_input = gr.Textbox(
            placeholder="Search your wardrobe…",
            show_label=False, max_lines=1,
            elem_classes=["cc-input"],
        )

        active_filter = gr.State("All")
        gr.HTML('<div style="height:12px"></div>')
        with gr.Row(elem_classes=["cc-chips"]):
            filter_btns = [
                gr.Button(lbl, elem_classes=["cc-chip"], size="sm")
                for lbl in ["All","Tops","Bottoms","One-pieces","Footwear","Outerwear"]
            ]

        grid_html = gr.HTML(_grid(get_all_items()))

        gr.HTML('<hr style="border:none;border-top:1px solid #E8E5E0;margin:32px 0 20px">')
        gr.HTML("""
<div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:12px">
  Select an item to edit its tags
</div>
""")
        with gr.Row(equal_height=True):
            with gr.Column(scale=4):
                edit_picker = gr.Dropdown(
                    choices=_choices(), value=None, show_label=False,
                    allow_custom_value=False,
                    label="Choose item",
                    elem_classes=["cc-select"],
                )
            with gr.Column(scale=1, min_width=60):
                refresh_picker_btn = gr.Button("↻", elem_classes=["cc-btn-ghost"], size="sm")
            with gr.Column(scale=1, min_width=120):
                edit_btn = gr.Button("Edit →", elem_classes=["cc-btn-accent"])

        gr.HTML('<div style="height:40px"></div>')

        refresh_picker_btn.click(
            fn=lambda: gr.update(choices=_choices(), value=None),
            outputs=[edit_picker],
        )

        for btn, lbl in zip(filter_btns, ["All","Tops","Bottoms","One-pieces","Footwear","Outerwear"]):
            btn.click(
                fn=lambda s, l=lbl: (_filter(l, s), l),
                inputs=[search_input],
                outputs=[grid_html, active_filter],
            )
        search_input.change(
            fn=lambda s, f: _filter(f, s),
            inputs=[search_input, active_filter],
            outputs=[grid_html],
        )

    return add_btn, edit_picker, edit_btn


def _build_add_inner():
    """Build the Add Clothes content, return last_item_id State."""
    import io
    from PIL import Image
    from src.vision.uploader import upload_from_pil

    def _to_pil(image):
        if image is None: return None
        if isinstance(image, dict):
            path = image.get("path","")
            if not path: return None
            try: return Image.open(path).convert("RGB")
            except Exception:
                try: return Image.open(io.BytesIO(open(path,"rb").read())).convert("RGB")
                except Exception: return None
        if isinstance(image, Image.Image): return image.convert("RGB")
        return None

    _STEPS = ["Category detected","Type detected","Colour detected",
              "Formality estimated","Season assessed"]

    def _steps_html(phase):
        if phase == "idle": return ""
        colors = {"done":"#16A34A","spin":"#7C5CFC","wait":"#D1D5DB","error":"#DC2626"}
        icons  = {"done":"✓","spin":"…","wait":"○","error":"✕"}
        def _st(i):
            if phase=="error": return "error" if i==0 else "wait"
            if phase=="done":  return "done"
            return "spin" if i==0 else "wait"
        rows = "".join(
            f'<div style="display:flex;align-items:center;gap:10px;padding:6px 0;font-size:14px;color:#1A1A1A">'
            f'<span style="color:{colors[_st(i)]};font-weight:700;width:16px;text-align:center">{icons[_st(i)]}</span>'
            f'<span style="color:#1A1A1A;font-weight:500">{s}</span></div>'
            for i,s in enumerate(_STEPS)
        )
        hd = {"running":'<div style="font-size:13px;font-weight:700;letter-spacing:1px;'
                         'text-transform:uppercase;color:#7C5CFC;margin-bottom:12px">Analyzing…</div>',
              "done":   '<div style="font-size:13px;font-weight:700;letter-spacing:1px;'
                        'text-transform:uppercase;color:#16A34A;margin-bottom:12px">Item tagged ✓</div>',
              "error":  '<div style="font-size:13px;font-weight:700;letter-spacing:1px;'
                        'text-transform:uppercase;color:#DC2626;margin-bottom:12px">Tagging failed</div>',
              }.get(phase,"")
        return f'<div class="cc-agent-steps">{hd}{rows}</div>'

    def _result_html(item):
        name     = f"{item.get('color','').title()} {item.get('subtype','').replace('_',' ').title()}".strip()
        seasons  = ", ".join(item.get("season") or [])
        rain     = "Yes" if item.get("rain_suitable") else "No"
        conf_pct = int((item.get("confidence") or 0)*100)
        fmap     = {1:"Loungewear",2:"Casual",3:"Smart casual",4:"Business casual",5:"Formal"}
        fs       = fmap.get(item.get("formality",2),"")
        rows = [("Category",item.get("category","").title()),
                ("Type",item.get("subtype","").replace("_"," ").title()),
                ("Colour",item.get("color","").title()),
                ("Formality",fs),("Season",seasons),("Rain",rain),
                ("Status",item.get("status","clean").title())]
        rhtml = "".join(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:10px 0;border-bottom:1px solid #F0EDE8;font-size:14px">'
            f'<span style="color:#374151;font-weight:500">{l}</span>'
            f'<span style="color:#1A1A1A;font-weight:600">{v}</span></div>'
            for l,v in rows
        )
        return (f'<div class="cc-card" style="margin-top:0">'
                f'<div style="font-size:17px;font-weight:700;color:#1A1A1A;margin-bottom:16px">{name}</div>'
                f'{rhtml}'
                f'<div style="margin-top:16px">'
                f'<div style="font-size:12px;color:#6B7280;margin-bottom:6px;font-weight:500">AI confidence</div>'
                f'<div class="cc-confidence-bar"><div class="cc-confidence-fill" style="width:{conf_pct}%"></div></div>'
                f'<div style="font-size:12px;color:#7C5CFC;margin-top:4px;font-weight:600">{conf_pct}%</div></div>'
                f'<div style="font-size:11px;color:#C8C3BB;margin-top:10px">ID: {item.get("item_id","")}</div>'
                f'</div>')

    def handle_tag(image, label):
        pil = _to_pil(image)
        if pil is None:
            return (_steps_html("error"),
                    '<div class="cc-error-box">Please upload a photo first.</div>',
                    "", gr.update(visible=False))
        try:
            item = upload_from_pil(pil, label=label.strip() or None)
            return _steps_html("done"), _result_html(item), item["item_id"], gr.update(visible=True)
        except Exception as exc:
            return (_steps_html("error"),
                    f'<div class="cc-error-box">{exc}</div>',
                    "", gr.update(visible=False))

    last_item_id = gr.State("")

    with gr.Column(elem_classes=["cc-page"]):
        gr.HTML("""
<div style="padding:40px 0 28px">
  <h2 style="font-size:clamp(22px,2.5vw,32px);font-weight:800;color:#1A1A1A;
      letter-spacing:-0.5px;margin:0 0 8px">Add to wardrobe</h2>
  <p style="font-size:14px;color:#374151;margin:0">
    Upload a photo of one clothing item. CloseCall tags it automatically.</p>
</div>
""")

        with gr.Row(equal_height=False):
            with gr.Column(scale=1, min_width=280):
                gr.HTML('<div style="font-size:11px;font-weight:700;letter-spacing:1px;'
                        'text-transform:uppercase;color:#6B7280;margin-bottom:10px">Upload a photo</div>')
                with gr.Group(elem_classes=["cc-upload-zone"]):
                    upload_image = gr.Image(
                        label="Clothing photo", type="pil",
                        sources=["upload","webcam"], show_label=False, height=280,
                    )
                label_input = gr.Textbox(
                    placeholder="Optional label — e.g. 'Favourite jacket'",
                    show_label=False, max_lines=1, elem_classes=["cc-input"],
                )
                analyze_btn = gr.Button("Analyze item", elem_classes=["cc-btn-primary"])
                steps_html  = gr.HTML("")

            with gr.Column(scale=1, min_width=280):
                gr.HTML('<div style="font-size:11px;font-weight:700;letter-spacing:1px;'
                        'text-transform:uppercase;color:#6B7280;margin-bottom:10px">Detected tags</div>')
                result_html = gr.HTML(
                    '<div style="background:#FDFCFA;border:1.5px dashed #D1CCC4;border-radius:14px;'
                    'padding:40px 24px;text-align:center;color:#C8C3BB">'
                    '<div style="font-size:28px;margin-bottom:10px">◻</div>'
                    '<div style="font-size:14px">Upload a photo and click<br>Analyze item</div></div>'
                )
                with gr.Row(visible=False) as post_row:
                    with gr.Column(scale=1):
                        add_another_btn = gr.Button("Add another", elem_classes=["cc-btn-secondary"])
                    with gr.Column(scale=1):
                        edit_tags_btn = gr.Button("Edit tags →", elem_classes=["cc-btn-accent"])

        gr.HTML('<div style="height:40px"></div>')

        analyze_btn.click(
            fn=lambda img, lbl: (
                _steps_html("running"),
                '<div style="background:#FDFCFA;border:1.5px dashed #D1CCC4;border-radius:14px;'
                'padding:40px 24px;text-align:center;color:#7C5CFC">'
                '<div style="font-size:14px">Analyzing…</div></div>',
                "", gr.update(visible=False)
            ),
            inputs=[upload_image, label_input],
            outputs=[steps_html, result_html, last_item_id, post_row],
        ).then(
            fn=handle_tag,
            inputs=[upload_image, label_input],
            outputs=[steps_html, result_html, last_item_id, post_row],
        )

        add_another_btn.click(
            fn=lambda: (None, "", _steps_html("idle"), "", "", gr.update(visible=False)),
            outputs=[upload_image, label_input, steps_html, result_html, last_item_id, post_row],
        )

    return last_item_id


# ─── entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    try:
        config.validate()
    except EnvironmentError as exc:
        print(f"\n⚠  Configuration error:\n{exc}\n")
        sys.exit(1)

    init_db()
    print("✅ Database initialised.")

    ip = _get_wifi_ip()
    print(f"\n💻 Open in browser:        http://localhost:7860")
    print(f"📱 On your phone (Wi-Fi):  http://{ip}:7860\n")

    app = build_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()
