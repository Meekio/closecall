"""
Screen 1 (Splash/Welcome) + Screen 2 (Home)
─────────────────────────────────────────────
Splash is shown only on first load via a gr.State flag.
Home shows:
  • Greeting + sparkle
  • Natural-language request input
  • Quick-pick occasion chips
  • Live weather widget
  • Quick-action buttons (Add Clothes / My Wardrobe)
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
    icon = "🌧️" if w.get("is_raining") else "🌤️"
    cond = w.get("description", w.get("condition", ""))
    temp = w.get("temperature_c", "–")
    city = w.get("location", profile.get("location", ""))
    return (
        f'<div class="cc-weather">'
        f'  <span style="font-size:24px">{icon}</span>'
        f'  <div>'
        f'    <div class="cc-weather-city">{city}</div>'
        f'    <div class="cc-weather-desc">{temp}°C · {cond.title()}</div>'
        f'  </div>'
        f'</div>'
    )


def _wardrobe_count() -> int:
    return len(get_all_items())


# ─── splash HTML ──────────────────────────────────────────────────────────────

_SPLASH_HTML = """
<div class="cc-splash-bg" style="min-height:100vh;display:flex;flex-direction:column;
     align-items:center;justify-content:center;padding:40px 24px;text-align:center;
     background:linear-gradient(160deg,#FDF6F0 0%,#F3E8FF 100%)">
  <div style="font-size:72px;margin-bottom:20px">👗</div>
  <div class="cc-splash-logo" style="font-size:40px;font-weight:800;
       letter-spacing:-1px;color:#1C1C1E">CloseCall</div>
  <div style="font-size:16px;color:#6B7280;margin:10px 0 48px;line-height:1.6;max-width:280px">
    Your Personal Stylist<br>
    <span style="font-size:14px">Outfits from your wardrobe,<br>for every mood and moment.</span>
  </div>
</div>
"""


# ─── tab builder ──────────────────────────────────────────────────────────────

def build_home_tab(go_add_clothes_fn, go_wardrobe_fn, on_request_fn) -> None:
    """
    Build the Home tab.

    Parameters
    ----------
    go_add_clothes_fn : callable
        Called (with no args) when "Add Clothes" quick-action is clicked.
        Should switch the outer Tabs to the Wardrobe/Add tab.
    go_wardrobe_fn : callable
        Called when "My Wardrobe" quick-action is clicked.
    on_request_fn : callable(request_text) -> None
        Called when the user submits a request; should switch to Outfits tab
        and pre-fill the request there.
    """

    with gr.Column(elem_classes=["cc-screen"]):

        # ── Greeting ──────────────────────────────────────────────────────────
        with gr.Row():
            gr.HTML(
                '<div style="padding:8px 0 4px">'
                '  <div style="font-size:22px;font-weight:700;color:#1C1C1E">'
                '    Hi! ✨'
                '  </div>'
                '  <div style="font-size:15px;color:#6B7280;margin-top:2px">'
                '    What are you dressing for today?'
                '  </div>'
                '</div>'
            )

        # ── NL request input ─────────────────────────────────────────────────
        request_input = gr.Textbox(
            placeholder="e.g. office outfit for rainy day",
            show_label=False,
            lines=1,
            max_lines=2,
            elem_classes=["cc-input"],
        )

        # ── Quick-pick occasion chips ─────────────────────────────────────────
        gr.HTML('<div style="font-size:12px;color:#9CA3AF;margin:4px 0 2px">Quick picks</div>')
        with gr.Row(elem_classes=["cc-chips"]):
            chip_work    = gr.Button("Work",    elem_classes=["cc-chip"], size="sm")
            chip_casual  = gr.Button("Casual",  elem_classes=["cc-chip"], size="sm")
            chip_college = gr.Button("College", elem_classes=["cc-chip"], size="sm")
        with gr.Row(elem_classes=["cc-chips"]):
            chip_party   = gr.Button("Party",   elem_classes=["cc-chip"], size="sm")
            chip_date    = gr.Button("Date",    elem_classes=["cc-chip"], size="sm")
            chip_travel  = gr.Button("Travel",  elem_classes=["cc-chip"], size="sm")

        # ── Weather widget ────────────────────────────────────────────────────
        weather_html = gr.HTML(_weather_html())

        gr.Button(
            "🔄 Refresh weather",
            size="sm",
            elem_classes=["cc-chip"],
        ).click(
            fn=lambda: _weather_html(),
            outputs=[weather_html],
        )

        # ── Submit request button ─────────────────────────────────────────────
        submit_btn = gr.Button(
            "→  Get outfit suggestions",
            elem_classes=["cc-btn-primary"],
        )

        # ── Quick actions ─────────────────────────────────────────────────────
        gr.HTML('<div class="cc-label" style="margin-top:20px">Quick Actions</div>')
        with gr.Row():
            btn_add  = gr.Button("📷\nAdd Clothes",    elem_classes=["cc-action-card"])
            btn_ward = gr.Button("👗\nMy Wardrobe",    elem_classes=["cc-action-card"])

        # ── Wire chips → fill input ───────────────────────────────────────────
        for chip, text in [
            (chip_work,    "I need an outfit for work today."),
            (chip_casual,  "Something casual and comfortable."),
            (chip_college, "Outfit for college today."),
            (chip_party,   "I have a party tonight."),
            (chip_date,    "A dinner date tonight."),
            (chip_travel,  "Travelling today, need something comfortable."),
        ]:
            chip.click(fn=lambda t=text: t, outputs=[request_input])

        # ── Submit → delegate to parent ───────────────────────────────────────
        submit_btn.click(fn=on_request_fn, inputs=[request_input], outputs=[])

        # ── Quick action nav ──────────────────────────────────────────────────
        btn_add.click(fn=go_add_clothes_fn, outputs=[])
        btn_ward.click(fn=go_wardrobe_fn,   outputs=[])
