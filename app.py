"""
CloseCall — AI Personal Stylist
Entry point.  Run:  python app.py
Then open the URL printed in the terminal on your phone.
"""

import sys
import socket
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gradio as gr

from src.config import config
from src.database.db import init_db
from src.ui.styles import MOBILE_CSS

# Tab builders
from src.ui.home_tab        import build_home_tab
from src.ui.add_clothes_tab import build_add_clothes_tab
from src.ui.item_detail_tab import build_item_detail_tab
from src.ui.wardrobe_tab    import build_wardrobe_tab
from src.ui.outfits_tab     import build_outfits_tab
from src.ui.profile_tab     import build_profile_tab


# ─── navigation helpers ───────────────────────────────────────────────────────

# We use a single gr.Tabs with 4 tabs whose labels act as the bottom nav:
#   Home | Wardrobe | Outfits | Profile
#
# "Add Clothes" and "Item Detail" live inside the Wardrobe tab as sub-views
# toggled by gr.Column(visible=...) — matching the wireframe's nav flow.

def _get_wifi_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "localhost"


# ─── app builder ──────────────────────────────────────────────────────────────

def build_app() -> gr.Blocks:

    with gr.Blocks(title="CloseCall") as app:

        # ── Shared cross-tab state ────────────────────────────────────────────
        prefill_request_state = gr.State("")
        edit_item_id_state    = gr.State("")

        # ── Outer Tab bar (becomes the bottom nav via CSS) ────────────────────
        with gr.Tabs(elem_id="main-tabs") as main_tabs:

            # ════════════════════════════════════════════════════════════════
            # TAB 1 — Home  (screens 1 + 2)
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("Home", id="tab-home") as tab_home:

                with gr.Column(visible=True) as splash_col:
                    gr.HTML("""
<div style="min-height:100vh;display:flex;flex-direction:column;
     align-items:center;justify-content:center;padding:40px 24px;
     text-align:center;background:linear-gradient(160deg,#FDF6F0 0%,#F3E8FF 100%)">
  <div style="font-size:48px;margin-bottom:20px;font-weight:300;letter-spacing:2px">CC</div>
  <div style="font-size:40px;font-weight:800;letter-spacing:-1px;color:#1C1C1E">
    CloseCall</div>
  <div style="font-size:14px;color:#6B7280;margin:10px 0 40px;
       line-height:1.7;max-width:280px">
    Your Personal Stylist<br>
    Outfits from your wardrobe,<br>for every mood and moment.
  </div>
</div>
""")
                    get_started_btn = gr.Button(
                        "Get Started →",
                        elem_classes=["cc-btn-primary"],
                    )

                with gr.Column(visible=False) as home_col:
                    # NL input + chips + weather + quick actions
                    from src.tools.weather import get_weather
                    from src.database.profile import load_profile

                    def _weather_html():
                        from src.ui.home_tab import _weather_html as _wh
                        return _wh()

                    gr.HTML(
                        '<div style="padding:8px 0 4px">'
                        '  <div style="font-size:22px;font-weight:700;color:#1C1C1E">Hi!</div>'
                        '  <div style="font-size:15px;color:#6B7280;margin-top:2px">'
                        '    What are you dressing for today?</div>'
                        '</div>'
                    )

                    home_request_input = gr.Textbox(
                        placeholder="e.g. office outfit for rainy day",
                        show_label=False,
                        lines=1,
                        max_lines=2,
                        elem_classes=["cc-input"],
                    )

                    gr.HTML('<div style="font-size:12px;color:#9CA3AF;margin:4px 0 2px">Quick picks</div>')
                    with gr.Row(elem_classes=["cc-chips"]):
                        hc_work    = gr.Button("Work",    elem_classes=["cc-chip"], size="sm")
                        hc_casual  = gr.Button("Casual",  elem_classes=["cc-chip"], size="sm")
                        hc_college = gr.Button("College", elem_classes=["cc-chip"], size="sm")
                    with gr.Row(elem_classes=["cc-chips"]):
                        hc_party   = gr.Button("Party",   elem_classes=["cc-chip"], size="sm")
                        hc_date    = gr.Button("Date",    elem_classes=["cc-chip"], size="sm")
                        hc_travel  = gr.Button("Travel",  elem_classes=["cc-chip"], size="sm")

                    weather_widget = gr.HTML(_weather_html())
                    gr.Button("🔄 Refresh weather", size="sm", elem_classes=["cc-chip"]).click(
                        fn=_weather_html, outputs=[weather_widget]
                    )

                    home_submit_btn = gr.Button(
                        "→  Get outfit suggestions",
                        elem_classes=["cc-btn-primary"],
                    )

                    gr.HTML('<div class="cc-label" style="margin-top:20px">Quick Actions</div>')
                    with gr.Row():
                        home_btn_add  = gr.Button("Add Clothes",  elem_classes=["cc-action-card"])
                        home_btn_ward = gr.Button("My Wardrobe",  elem_classes=["cc-action-card"])

                    # Chips fill input
                    for chip, text in [
                        (hc_work,    "I need an outfit for work today."),
                        (hc_casual,  "Something casual and comfortable."),
                        (hc_college, "Outfit for college today."),
                        (hc_party,   "I have a party tonight."),
                        (hc_date,    "A dinner date tonight."),
                        (hc_travel,  "Travelling today, need something comfortable."),
                    ]:
                        chip.click(fn=lambda t=text: t, outputs=[home_request_input])

                # Splash → Home
                get_started_btn.click(
                    fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
                    outputs=[splash_col, home_col],
                )

            # ════════════════════════════════════════════════════════════════
            # TAB 2 — Wardrobe  (screens 3, 4, 5, 6)
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("Wardrobe", id="tab-wardrobe") as tab_wardrobe:

                with gr.Column(visible=True) as wv_grid:
                    build_wardrobe_tab(go_edit_fn=lambda iid: None)  # wired below

                with gr.Column(visible=False) as wv_add:
                    build_add_clothes_tab(go_edit_item_fn=lambda iid: None)  # wired below

                with gr.Column(visible=False) as wv_detail:
                    item_id_detail_st = build_item_detail_tab()

                # Sub-view helper
                def _wv(grid=False, add=False, detail=False):
                    return (
                        gr.update(visible=grid),
                        gr.update(visible=add),
                        gr.update(visible=detail),
                    )
                _WV_OUTS = [wv_grid, wv_add, wv_detail]

                # "Add Clothes" button on the wardrobe grid top
                # We add it here as a proper button since build_wardrobe_tab's
                # go_edit_fn lambda can't switch sub-views without the Column refs.
                add_clothes_btn_ward = gr.Button(
                    "Add Clothes",
                    elem_classes=["cc-btn-violet"],
                )
                add_clothes_btn_ward.click(
                    fn=lambda: _wv(add=True),
                    outputs=_WV_OUTS,
                )

            # ════════════════════════════════════════════════════════════════
            # TAB 3 — Outfits  (screens 7–10)
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("Outfits", id="tab-outfits") as tab_outfits:
                build_outfits_tab(prefill_state=prefill_request_state)

            # ════════════════════════════════════════════════════════════════
            # TAB 4 — Profile  (screen 11)
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("Profile", id="tab-profile"):
                build_profile_tab()

        # ── Cross-tab wiring: Home → Outfits ─────────────────────────────────
        # Submitting a request from Home pre-fills Outfits input and switches tab
        home_submit_btn.click(
            fn=lambda req: req,
            inputs=[home_request_input],
            outputs=[prefill_request_state],
        )
        # Quick-action: Add Clothes → Wardrobe tab (add sub-view)
        home_btn_add.click(
            fn=lambda: (gr.update(selected="tab-wardrobe"), _wv(add=True)[0], _wv(add=True)[1], _wv(add=True)[2]),
            outputs=[main_tabs, wv_grid, wv_add, wv_detail],
        )
        # Quick-action: My Wardrobe → Wardrobe tab (grid sub-view)
        home_btn_ward.click(
            fn=lambda: (gr.update(selected="tab-wardrobe"),),
            outputs=[main_tabs],
        )

    return app


# ─── entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    try:
        config.validate()
    except EnvironmentError as exc:
        print(f"\n⚠️  Configuration error:\n{exc}\n")
        sys.exit(1)

    init_db()
    print("✅ Database initialised.")

    ip = _get_wifi_ip()
    print(f"\n📱 Open on your phone (same Wi-Fi): http://{ip}:7860\n")
    print(f"💻 Local:  http://localhost:7860\n")

    app = build_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(
            primary_hue="violet",
            secondary_hue="pink",
            neutral_hue="slate",
        ),
        css=MOBILE_CSS,
    )


if __name__ == "__main__":
    main()
