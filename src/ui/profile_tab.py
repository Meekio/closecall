"""
Screen 11 — Profile / Settings
────────────────────────────────
• Avatar + name + email
• Wardrobe count stat
• Editable: name, location, style notes
• Coming-soon items: Calendar, Advanced Preferences
"""

from __future__ import annotations
import gradio as gr

from src.database.db import get_all_items
from src.database.profile import load_profile, save_profile


def _stats_html() -> str:
    n = len(get_all_items())
    return (
        f'<div style="background:#F3E8FF;border-radius:14px;padding:14px 18px;'
        f'display:flex;align-items:center;gap:16px;margin:12px 0">'
        f'  <div style="text-align:center">'
        f'    <div style="font-size:24px;font-weight:700;color:#6D28D9">{n}</div>'
        f'    <div style="font-size:11px;color:#7C3AED;font-weight:500">Items</div>'
        f'  </div>'
        f'  <div style="flex:1;font-size:13px;color:#6B7280">'
        f'    Upload more clothes to get better outfit suggestions.'
        f'  </div>'
        f'</div>'
    )


def _profile_rows_html() -> str:
    return """
<div class="cc-card" style="margin-top:0">
  <div class="cc-profile-row">
    <span><span class="cc-profile-row-icon">📅</span>Calendar</span>
    <span style="display:flex;align-items:center;gap:6px">
      <span style="background:#FEF9C3;color:#854D0E;border-radius:20px;
            padding:2px 8px;font-size:10px;font-weight:600">Coming Soon</span>
      <span class="cc-profile-chevron">›</span>
    </span>
  </div>
  <div class="cc-profile-row">
    <span><span class="cc-profile-row-icon">❓</span>Help &amp; Support</span>
    <span class="cc-profile-chevron">›</span>
  </div>
  <div class="cc-profile-row" style="border-bottom:none">
    <span><span class="cc-profile-row-icon">ℹ️</span>About CloseCall</span>
    <span class="cc-profile-chevron">›</span>
  </div>
</div>
"""


def build_profile_tab() -> None:

    with gr.Column(elem_classes=["cc-screen"]):

        gr.HTML(
            '<div style="font-size:20px;font-weight:700;color:#1C1C1E;'
            'padding:8px 0 16px;display:flex;justify-content:space-between">'
            '  <span>Profile</span>'
            '  <span style="font-size:18px">⚙️</span>'
            '</div>'
        )

        # ── Avatar + name ─────────────────────────────────────────────────────
        profile = load_profile()
        with gr.Row():
            gr.HTML(
                f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:4px">'
                f'  <div class="cc-profile-avatar">👤</div>'
                f'  <div>'
                f'    <div style="font-size:17px;font-weight:700;color:#1C1C1E">'
                f'      {profile.get("name","Your Name")}</div>'
                f'    <div style="font-size:13px;color:#6B7280">'
                f'      {profile.get("email","user@example.com")}</div>'
                f'  </div>'
                f'</div>'
            )

        # ── Stats ─────────────────────────────────────────────────────────────
        stats_html = gr.HTML(_stats_html())

        # ── Edit profile ──────────────────────────────────────────────────────
        with gr.Accordion("✏️  Edit Profile", open=False):
            with gr.Group(elem_classes=["cc-card"]):
                name_input = gr.Textbox(
                    label="Your Name",
                    value=profile.get("name",""),
                    max_lines=1,
                    elem_classes=["cc-input"],
                )
                email_input = gr.Textbox(
                    label="Email",
                    value=profile.get("email",""),
                    max_lines=1,
                    elem_classes=["cc-input"],
                )
                location_input = gr.Textbox(
                    label="Location (for weather)",
                    value=profile.get("location","Mumbai"),
                    max_lines=1,
                    elem_classes=["cc-input"],
                    placeholder="City name, e.g. Mumbai",
                )
                style_input = gr.Textbox(
                    label="Style notes (optional)",
                    value=profile.get("style_notes",""),
                    lines=2,
                    max_lines=4,
                    elem_classes=["cc-input"],
                    placeholder="e.g. I prefer neutral colors, no prints",
                )
                save_profile_btn = gr.Button("💾  Save Profile", elem_classes=["cc-btn-primary"])
                profile_save_msg = gr.HTML("")

            def handle_save_profile(name, email, location, style_notes):
                save_profile({
                    "name": name, "email": email,
                    "location": location, "style_notes": style_notes,
                })
                return '<div style="color:#22C55E;font-size:13px;padding:4px 0">✅ Profile saved!</div>'

            save_profile_btn.click(
                fn=handle_save_profile,
                inputs=[name_input, email_input, location_input, style_input],
                outputs=[profile_save_msg],
            )

        # ── Wardrobe link row ─────────────────────────────────────────────────
        with gr.Group(elem_classes=["cc-card"]):
            gr.HTML(
                '<div class="cc-profile-row" style="border-bottom:none">'
                '  <span><span class="cc-profile-row-icon">👗</span>My Wardrobe</span>'
                '  <span style="font-size:12px;color:#6B7280">View and manage your clothes</span>'
                '</div>'
            )

        # ── Coming-soon rows ──────────────────────────────────────────────────
        gr.HTML(_profile_rows_html())

        # ── Refresh stats ─────────────────────────────────────────────────────
        gr.Button("🔄 Refresh stats", size="sm", elem_classes=["cc-chip"]).click(
            fn=_stats_html,
            outputs=[stats_html],
        )
