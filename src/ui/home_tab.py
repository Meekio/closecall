"""
Home Tab — CloseCall
─────────────────────
Desktop: wide hero heading, full-width request box, chip row,
         two-column context cards (weather + wardrobe count), quick actions.
Mobile:  everything stacks vertically, request box stays the visual focus.
"""

from __future__ import annotations
import gradio as gr
from src.tools.weather import get_weather
from src.database.profile import load_profile
from src.database.db import get_all_items


# ─── helpers ──────────────────────────────────────────────────────────────────

def _weather_html() -> str:
    profile = load_profile()
    w = get_weather(profile.get("location", "Mumbai"))
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


def _wardrobe_stat_html() -> str:
    items = get_all_items()
    total = len(items)
    clean = sum(1 for i in items if i.get("status") == "clean")
    return f"""
<div style="background:#FFFFFF;border:1px solid #E8E5E0;border-radius:12px;
     padding:16px 20px;height:100%">
  <div style="font-size:11px;font-weight:700;letter-spacing:1px;
       text-transform:uppercase;color:#6B7280;margin-bottom:8px">YOUR WARDROBE</div>
  <div style="font-size:24px;font-weight:800;color:#1A1A1A">{total} items</div>
  <div style="font-size:13px;color:#374151;margin-top:2px">{clean} clean · ready to wear</div>
</div>
"""


# ─── tab builder ──────────────────────────────────────────────────────────────

def build_home_tab(go_add_clothes_fn, go_wardrobe_fn, on_request_fn) -> None:
    """
    Build the Home tab inside the active gr.Blocks context.

    Parameters
    ----------
    go_add_clothes_fn : callable
        Switches to Wardrobe tab → Add Clothes sub-view.
    go_wardrobe_fn : callable
        Switches to Wardrobe tab → grid sub-view.
    on_request_fn : callable(request_text)
        Pre-fills Outfits tab and switches to it.
    """

    with gr.Column(elem_classes=["cc-page"]):

        # ── Hero heading ──────────────────────────────────────────────────────
        gr.HTML("""
<div style="padding: 48px 0 32px">
  <div style="font-size:11px;font-weight:700;letter-spacing:1.5px;
       text-transform:uppercase;color:#6B7280;margin-bottom:16px">
    CloseCall — Your Personal Stylist
  </div>
  <h1 style="font-size:clamp(28px,4vw,52px);font-weight:800;color:#1A1A1A;
       letter-spacing:-1.5px;line-height:1.1;margin:0 0 14px">
    Your wardrobe.<br>Your plans.<br>
    <span style="color:#7C5CFC">One outfit that works.</span>
  </h1>
  <p style="font-size:clamp(14px,1.4vw,17px);color:#374151;
      line-height:1.6;max-width:540px;margin:0">
    Describe what you need and CloseCall reasons over your
    real wardrobe — checking weather, occasion, and formality —
    to recommend outfits that actually fit your day.
  </p>
</div>
""")

        # ── Request input ─────────────────────────────────────────────────────
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

        get_outfits_btn = gr.Button(
            "Get outfit suggestions →",
            elem_classes=["cc-btn-primary"],
        )

        # ── Quick-pick chips ──────────────────────────────────────────────────
        gr.HTML("""
<div style="font-size:12px;color:#6B7280;margin:20px 0 8px;font-weight:500">
  Try asking
</div>
""")
        with gr.Row(elem_classes=["cc-chips"],
                    elem_id="home-chips"):
            chip_work    = gr.Button("Work",    elem_classes=["cc-chip"], size="sm")
            chip_casual  = gr.Button("Casual",  elem_classes=["cc-chip"], size="sm")
            chip_date    = gr.Button("Date",    elem_classes=["cc-chip"], size="sm")
            chip_college = gr.Button("College", elem_classes=["cc-chip"], size="sm")
            chip_travel  = gr.Button("Travel",  elem_classes=["cc-chip"], size="sm")

        # Add a small gap
        gr.HTML('<div style="height:28px"></div>')

        # ── Context cards — weather + wardrobe (two columns on desktop) ───────
        gr.HTML("""
<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin-bottom:10px">TODAY</div>
""")
        with gr.Row(equal_height=True):
            with gr.Column(scale=1, min_width=220):
                weather_widget = gr.HTML(_weather_html())
            with gr.Column(scale=1, min_width=220):
                wardrobe_stat  = gr.HTML(_wardrobe_stat_html())

        # Refresh weather button
        gr.Button(
            "↻  Refresh weather",
            size="sm",
            elem_classes=["cc-btn-ghost"],
        ).click(fn=_weather_html, outputs=[weather_widget])

        gr.HTML('<div style="height:32px"></div>')

        # ── Quick action buttons ──────────────────────────────────────────────
        gr.HTML("""
<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin-bottom:10px"></div>
""")
        with gr.Row():
            with gr.Column(scale=1):
                btn_add = gr.Button(
                    "+ Add clothes",
                    elem_classes=["cc-btn-secondary"],
                )
            with gr.Column(scale=1):
                btn_wardrobe = gr.Button(
                    "View wardrobe →",
                    elem_classes=["cc-btn-ghost"],
                )

        gr.HTML('<div style="height:40px"></div>')

        # ── Wire chips → fill input ───────────────────────────────────────────
        _chip_prompts = [
            (chip_work,    "I need an outfit for work today."),
            (chip_casual,  "Something casual and comfortable for today."),
            (chip_date,    "A dinner date tonight — suggest something nice."),
            (chip_college, "Outfit for college today."),
            (chip_travel,  "Travelling today, need something comfortable."),
        ]
        for chip, text in _chip_prompts:
            chip.click(fn=lambda t=text: t, outputs=[request_input])

        # ── Submit ────────────────────────────────────────────────────────────
        get_outfits_btn.click(
            fn=on_request_fn,
            inputs=[request_input],
            outputs=[],
        )
        request_input.submit(
            fn=on_request_fn,
            inputs=[request_input],
            outputs=[],
        )

        # ── Quick nav ─────────────────────────────────────────────────────────
        btn_add.click(fn=go_add_clothes_fn, outputs=[])
        btn_wardrobe.click(fn=go_wardrobe_fn, outputs=[])
