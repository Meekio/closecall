"""
Profile Tab — CloseCall
────────────────────────
Compact layout per the spec:
  • Avatar + name + email
  • Wardrobe stats (items, clean count)
  • Saved preferences count
  • Editable: name, location, style notes
  • Coming-soon rows
"""

from __future__ import annotations
import gradio as gr

from src.database.db import get_all_items
from src.database.profile import load_profile, save_profile


def _stats_html() -> str:
    items = get_all_items()
    total = len(items)
    clean = sum(1 for i in items if i.get("status") == "clean")

    try:
        from src.database.preferences import get_preference_notes
        prefs = get_preference_notes("default_user")
        pref_count = len(prefs)
    except Exception:
        pref_count = 0

    return f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0">
  <div class="cc-stat-card">
    <div style="font-size:26px;font-weight:800;color:#1A1A1A">{total}</div>
    <div style="font-size:12px;color:#6B7280;margin-top:4px;font-weight:500">Wardrobe items</div>
  </div>
  <div class="cc-stat-card">
    <div style="font-size:26px;font-weight:800;color:#16A34A">{clean}</div>
    <div style="font-size:12px;color:#6B7280;margin-top:4px;font-weight:500">Clean</div>
  </div>
  <div class="cc-stat-card">
    <div style="font-size:26px;font-weight:800;color:#7C5CFC">{pref_count}</div>
    <div style="font-size:12px;color:#6B7280;margin-top:4px;font-weight:500">Saved preferences</div>
  </div>
</div>
"""


def build_profile_tab() -> None:

    with gr.Column(elem_classes=["cc-page"]):

        # Page header
        gr.HTML("""
<div style="padding: 40px 0 24px">
  <h2 style="font-size:clamp(22px,2.5vw,32px);font-weight:800;color:#1A1A1A;
      letter-spacing:-0.5px;margin:0">Profile</h2>
</div>
""")

        # ── Avatar + identity ─────────────────────────────────────────────
        profile = load_profile()
        gr.HTML(f"""
<div style="display:flex;align-items:center;gap:18px;margin-bottom:8px">
  <div style="width:60px;height:60px;border-radius:50%;background:#EDE9FE;
       display:flex;align-items:center;justify-content:center;
       font-size:24px;flex-shrink:0">👤</div>
  <div>
    <div style="font-size:18px;font-weight:700;color:#1A1A1A">
      {profile.get('name', 'Your Name')}</div>
    <div style="font-size:14px;color:#6B7280;margin-top:2px">
      {profile.get('email', 'user@example.com')}</div>
  </div>
</div>
""")

        # ── Stats ─────────────────────────────────────────────────────────
        gr.HTML("""
<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin:24px 0 0">
  Wardrobe
</div>
""")
        stats_html = gr.HTML(_stats_html())

        # ── Edit profile ──────────────────────────────────────────────────
        with gr.Accordion("Edit profile", open=False):
            name_input = gr.Textbox(
                label="Your name",
                value=profile.get("name", ""),
                max_lines=1,
                elem_classes=["cc-input"],
            )
            email_input = gr.Textbox(
                label="Email",
                value=profile.get("email", ""),
                max_lines=1,
                elem_classes=["cc-input"],
            )
            location_input = gr.Textbox(
                label="Location (for weather)",
                value=profile.get("location", "Mumbai"),
                max_lines=1,
                elem_classes=["cc-input"],
                placeholder="City name, e.g. Chennai",
            )
            style_input = gr.Textbox(
                label="Style notes (optional)",
                value=profile.get("style_notes", ""),
                lines=2,
                max_lines=4,
                elem_classes=["cc-input"],
                placeholder="e.g. I prefer neutral colours, no prints",
            )
            save_btn = gr.Button("Save profile", elem_classes=["cc-btn-primary"])
            save_msg = gr.HTML("")

            def handle_save(name, email, location, style_notes):
                save_profile({
                    "name": name, "email": email,
                    "location": location, "style_notes": style_notes,
                })
                return '<div style="color:#16A34A;font-size:13px;padding:6px 0;font-weight:600">✓ Profile saved</div>'

            save_btn.click(
                fn=handle_save,
                inputs=[name_input, email_input, location_input, style_input],
                outputs=[save_msg],
            )

        # ── Saved preferences ─────────────────────────────────────────────
        gr.HTML("""
<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin:28px 0 12px">
  Saved preferences
</div>
""")
        prefs_html = gr.HTML("")

        def _prefs_html():
            try:
                from src.database.preferences import get_preference_notes
                notes = get_preference_notes("default_user")
            except Exception:
                notes = []
            if not notes:
                return (
                    '<div style="font-size:14px;color:#C8C3BB;padding:16px 0">'
                    'No preferences saved yet. Refine an outfit suggestion to save preferences.</div>'
                )
            rows = "".join(
                f'<div style="padding:10px 0;border-bottom:1px solid #F0EDE8;'
                f'font-size:14px;color:#374151">{n.get("preference_text","")}</div>'
                for n in notes[-5:]
            )
            return f'<div class="cc-card-sm">{rows}</div>'

        prefs_html.value = _prefs_html()

        # ── Menu rows ─────────────────────────────────────────────────────
        gr.HTML("""
<div class="cc-card-sm" style="margin-top:28px">
  <div class="cc-profile-row">
    <span style="font-size:15px;color:#1A1A1A">Wardrobe</span>
    <span style="font-size:13px;color:#6B7280">View and manage your clothes</span>
  </div>
  <div class="cc-profile-row">
    <span style="font-size:15px;color:#1A1A1A">Calendar integration</span>
    <span style="background:#FEF9C3;color:#854D0E;border-radius:100px;
          padding:2px 10px;font-size:11px;font-weight:600">Coming soon</span>
  </div>
  <div class="cc-profile-row">
    <span style="font-size:15px;color:#1A1A1A">About CloseCall</span>
    <span style="color:#6B7280;font-size:16px">›</span>
  </div>
</div>
""")

        gr.HTML('<div style="height:8px"></div>')
        gr.Button(
            "↻ Refresh stats",
            size="sm",
            elem_classes=["cc-btn-ghost"],
        ).click(fn=_stats_html, outputs=[stats_html])

        gr.HTML('<div style="height:40px"></div>')
