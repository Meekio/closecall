"""
Profile Tab — CloseCall
Compact layout: avatar, stats, inline edit form, preferences, menu rows.
No accordion — edit fields are always visible in a clean card.
"""

from __future__ import annotations
import gradio as gr

from src.database.db import get_all_items
from src.database.profile import load_profile, save_profile


def _stats_html() -> str:
    items  = get_all_items()
    total  = len(items)
    clean  = sum(1 for i in items if i.get("status") == "clean")
    try:
        from src.database.preferences import get_preference_notes
        pref_count = len(get_preference_notes("default_user"))
    except Exception:
        pref_count = 0

    return f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0 0">
  <div style="background:#FFFFFF;border:1px solid #E8E5E0;border-radius:12px;
       padding:20px;text-align:center">
    <div style="font-size:28px;font-weight:800;color:#1A1A1A">{total}</div>
    <div style="font-size:12px;color:#6B7280;margin-top:4px;font-weight:500">Wardrobe items</div>
  </div>
  <div style="background:#FFFFFF;border:1px solid #E8E5E0;border-radius:12px;
       padding:20px;text-align:center">
    <div style="font-size:28px;font-weight:800;color:#16A34A">{clean}</div>
    <div style="font-size:12px;color:#6B7280;margin-top:4px;font-weight:500">Clean</div>
  </div>
  <div style="background:#FFFFFF;border:1px solid #E8E5E0;border-radius:12px;
       padding:20px;text-align:center">
    <div style="font-size:28px;font-weight:800;color:#7C5CFC">{pref_count}</div>
    <div style="font-size:12px;color:#6B7280;margin-top:4px;font-weight:500">Saved preferences</div>
  </div>
</div>
"""


def _prefs_html() -> str:
    try:
        from src.database.preferences import get_preference_notes
        notes = get_preference_notes("default_user")
    except Exception:
        notes = []
    if not notes:
        return ('<div style="font-size:14px;color:#9CA3AF;padding:12px 0">'
                'No preferences saved yet. Refine an outfit to save preferences.</div>')
    rows = "".join(
        f'<div style="padding:10px 0;border-bottom:1px solid #F0EDE8;'
        f'font-size:14px;color:#374151">{n.get("preference_text","")}</div>'
        for n in notes[-5:]
    )
    return f'<div>{rows}</div>'


def build_profile_tab() -> None:

    profile = load_profile()

    with gr.Column(elem_classes=["cc-page"]):

        # ── Page title ────────────────────────────────────────────────────
        gr.HTML("""
<div style="padding:40px 0 20px">
  <h2 style="font-size:clamp(22px,2.5vw,32px);font-weight:800;color:#1A1A1A;
      letter-spacing:-0.5px;margin:0">Profile</h2>
</div>
""")

        # ── Avatar row ────────────────────────────────────────────────────
        gr.HTML(f"""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:4px">
  <div style="width:56px;height:56px;border-radius:50%;background:#EDE9FE;
       display:flex;align-items:center;justify-content:center;
       font-size:22px;flex-shrink:0">👤</div>
  <div>
    <div style="font-size:18px;font-weight:700;color:#1A1A1A">
      {profile.get('name', 'Your Name')}</div>
    <div style="font-size:14px;color:#6B7280;margin-top:2px">
      {profile.get('email', 'user@example.com')}</div>
  </div>
</div>
""")

        # ── Stats ─────────────────────────────────────────────────────────
        gr.HTML('<div style="font-size:11px;font-weight:700;letter-spacing:1px;'
                'text-transform:uppercase;color:#6B7280;margin:28px 0 0">Wardrobe</div>')
        stats_html = gr.HTML(_stats_html())

        # ── Edit profile — inline card, no accordion ──────────────────────
        gr.HTML("""
<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin:32px 0 12px">
  Edit profile
</div>
""")

        with gr.Column(elem_classes=["cc-card"]):
            with gr.Row():
                with gr.Column(scale=1):
                    name_input = gr.Textbox(
                        label="Your name",
                        value=profile.get("name", ""),
                        max_lines=1,
                        elem_classes=["cc-input"],
                    )
                with gr.Column(scale=1):
                    email_input = gr.Textbox(
                        label="Email",
                        value=profile.get("email", ""),
                        max_lines=1,
                        elem_classes=["cc-input"],
                    )

            with gr.Row():
                with gr.Column(scale=1):
                    location_input = gr.Textbox(
                        label="Location (for weather)",
                        value=profile.get("location", "Chennai"),
                        max_lines=1,
                        elem_classes=["cc-input"],
                        placeholder="City name, e.g. Chennai",
                    )
                with gr.Column(scale=1):
                    style_input = gr.Textbox(
                        label="Style notes (optional)",
                        value=profile.get("style_notes", ""),
                        lines=1,
                        max_lines=3,
                        elem_classes=["cc-input"],
                        placeholder="e.g. I prefer neutral colours, no prints",
                    )

            with gr.Row():
                with gr.Column(scale=2):
                    save_msg = gr.HTML("")
                with gr.Column(scale=1, min_width=140):
                    save_btn = gr.Button("Save profile", elem_classes=["cc-btn-primary"])

        # ── Saved preferences ─────────────────────────────────────────────
        gr.HTML("""
<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin:32px 0 12px">
  Saved preferences
</div>
""")
        gr.HTML(_prefs_html())

        # ── Menu rows ─────────────────────────────────────────────────────
        gr.HTML("""
<div style="background:#FFFFFF;border:1px solid #E8E5E0;border-radius:12px;
     padding:0 20px;margin-top:28px">
  <div style="display:flex;align-items:center;justify-content:space-between;
       padding:16px 0;border-bottom:1px solid #F0EDE8">
    <span style="font-size:15px;color:#1A1A1A;font-weight:500">Wardrobe</span>
    <span style="font-size:13px;color:#6B7280">View and manage your clothes</span>
  </div>
  <div style="display:flex;align-items:center;justify-content:space-between;
       padding:16px 0;border-bottom:1px solid #F0EDE8">
    <span style="font-size:15px;color:#1A1A1A;font-weight:500">Calendar integration</span>
    <span style="background:#FEF9C3;color:#854D0E;border-radius:100px;
          padding:3px 10px;font-size:11px;font-weight:600">Coming soon</span>
  </div>
  <div style="display:flex;align-items:center;justify-content:space-between;
       padding:16px 0">
    <span style="font-size:15px;color:#1A1A1A;font-weight:500">About CloseCall</span>
    <span style="color:#9CA3AF;font-size:16px">›</span>
  </div>
</div>
""")

        gr.HTML('<div style="height:40px"></div>')

        # ── Wire save ─────────────────────────────────────────────────────
        def handle_save(name, email, location, style_notes):
            save_profile({
                "name": name, "email": email,
                "location": location, "style_notes": style_notes,
            })
            return ('<div style="color:#16A34A;font-size:13px;font-weight:600;padding:4px 0">'
                    '✓ Saved</div>')

        save_btn.click(
            fn=handle_save,
            inputs=[name_input, email_input, location_input, style_input],
            outputs=[save_msg],
        )

        gr.Button("↻ Refresh stats", size="sm", elem_classes=["cc-btn-ghost"]).click(
            fn=_stats_html, outputs=[stats_html]
        )
