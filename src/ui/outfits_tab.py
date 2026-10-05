"""
Outfits Tab — CloseCall
────────────────────────
Three sub-views managed by gr.Column(visible=...):

  View A — Request input
    • Natural-language text box
    • Agent processing checklist (shows tool calls in progress)

  View B — Recommendations
    • Weather/occasion context bar
    • Outfit cards — side-by-side on desktop (cc-outfit-grid CSS grid)
    • Each card: item list, Why this works, Styling guidance, validation checks
    • Failure diagnosis when no valid outfit found

  View C — Feedback / Refinement
    • Quick-change chips + free-text refinement
    • Routes back through agent with session memory intact

Backend untouched: get_agent(), reset_agent(), all tool calls happen inside
agent.chat(). UI only parses and renders the response.
"""

from __future__ import annotations
import re
import gradio as gr

from src.agent.stylist_agent import get_agent, reset_agent
from src.database.db import get_all_items
from src.tools.weather import get_weather
from src.database.profile import load_profile


# ─── agent processing checklist ───────────────────────────────────────────────

_AGENT_STEPS = [
    "Understanding your request",
    "Checking today's weather",
    "Searching your wardrobe",
    "Finding suitable combinations",
    "Checking outfit validity",
    "Finding the best match",
]

def _thinking_html(active: int = -1) -> str:
    """
    active: index of the currently running step.
    -1 = idle (show nothing), 99 = all done.
    """
    if active == -1:
        return ""

    rows = ""
    for i, label in enumerate(_AGENT_STEPS):
        if i < active or active == 99:
            icon, color = "✓", "#16A34A"
        elif i == active:
            icon, color = "…", "#7C5CFC"
        else:
            icon, color = "○", "#D1D5DB"

        rows += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:8px 0;border-bottom:1px solid #F0EDE8;font-size:14px;color:#374151">'
            f'  <span>{label}</span>'
            f'  <span style="color:{color};font-weight:700;font-size:16px">{icon}</span>'
            f'</div>'
        )

    return f'<div class="cc-agent-steps">{rows}</div>'


# ─── response parser ───────────────────────────────────────────────────────────

def _parse_outfits(text: str) -> list[dict]:
    """
    Parse agent Markdown response into outfit dicts:
      { title, items: [{name, item_id}], why, guidance, raw }
    """
    heading_re = re.compile(
        r"#{1,3}\s*Outfit\s+(\d+)\s*[:\-–]?\s*([^\n]*)", re.IGNORECASE
    )
    headings = list(heading_re.finditer(text))

    if not headings:
        return [{"title": "Recommendation", "items": [], "why": "",
                 "guidance": "", "raw": text.strip()}]

    outfits = []
    for i, match in enumerate(headings):
        title = match.group(2).strip().strip("*").strip()
        start = match.end()
        end   = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        block = text[start:end]

        # Items: - **Name** — item_id
        item_re = re.compile(r"-\s+\*{0,2}(.+?)\*{0,2}\s*[—–\-]+\s*(item_\S+)", re.MULTILINE)
        items = [
            {"name": m.group(1).strip(), "item_id": m.group(2).strip().rstrip(".,)")}
            for m in item_re.finditer(block)
        ]

        # Why this works
        why_re = re.compile(
            r"\*?Why(?:\s+this\s+works)?\*?[:\s]+(.+?)(?:\n\n|\*?Styling|\Z)",
            re.IGNORECASE | re.DOTALL
        )
        why_m  = why_re.search(block)
        why    = why_m.group(1).strip().strip("*") if why_m else ""

        # Styling guidance
        guide_re = re.compile(
            r"\*?Styling\s+guidance\*?[:\s]+(.+?)(?:\n\n|\Z)",
            re.IGNORECASE | re.DOTALL
        )
        guide_m  = guide_re.search(block)
        guidance = guide_m.group(1).strip().strip("*") if guide_m else ""

        outfits.append({
            "title":    title,
            "items":    items,
            "why":      why,
            "guidance": guidance,
            "raw":      block.strip(),
        })

    return outfits[:3]


def _is_failure_response(text: str) -> bool:
    """Detect if the agent returned a failure/no-outfit-found response."""
    lower = text.lower()
    signals = [
        "couldn't find", "could not find", "no valid outfit",
        "no suitable outfit", "no outfit", "couldn't complete",
        "nothing suitable", "wardrobe doesn't have",
    ]
    return any(s in lower for s in signals) and "outfit 1" not in lower


# ─── outfit card HTML ──────────────────────────────────────────────────────────

def _outfit_card_html(outfit: dict, idx: int, is_best: bool = False,
                      is_raining: bool = False) -> str:
    best_badge  = '<span class="cc-badge-violet" style="margin-bottom:10px;display:inline-block">BEST MATCH</span>' if is_best else ""
    rain_badge  = '<span class="cc-badge-rain" style="margin-left:6px">🌧 Rain suitable</span>' if is_raining else ""

    # Items
    items_html = ""
    for item in outfit.get("items", []):
        items_html += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:9px 0;border-bottom:1px solid #F8F7F5;font-size:14px">'
            f'  <span style="color:#1A1A1A;font-weight:500">{item["name"]}</span>'
            f'  <span style="color:#C8C3BB;font-size:11px;font-family:monospace">'
            f'    {item["item_id"]}</span>'
            f'</div>'
        )

    # Why this works
    why = (outfit.get("why") or "").strip()
    why_html = ""
    if why:
        why_clean = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", why)
        why_clean = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", why_clean)
        why_clean = why_clean.replace("\n", " ")
        why_html = (
            f'<div class="cc-why-box">'
            f'  <div style="font-size:11px;font-weight:700;letter-spacing:1px;'
            f'text-transform:uppercase;color:#15803D;margin-bottom:6px">Why this works</div>'
            f'  <div style="font-size:13px;color:#1A5C2E;line-height:1.6">{why_clean}</div>'
            f'</div>'
        )

    # Styling guidance (RAG)
    guidance = (outfit.get("guidance") or "").strip()
    guide_html = ""
    if guidance:
        guide_clean = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", guidance)
        guide_clean = guide_clean.replace("\n", " ")
        guide_html = (
            f'<div style="margin-top:10px;padding:12px 14px;background:#F5F3FF;'
            f'border-radius:10px">'
            f'  <div style="font-size:11px;font-weight:700;letter-spacing:1px;'
            f'text-transform:uppercase;color:#5B3FD4;margin-bottom:5px">'
            f'▸ Styling guidance</div>'
            f'  <div style="font-size:13px;color:#4C3BA0;line-height:1.5">{guide_clean}</div>'
            f'</div>'
        )

    # Raw fallback
    raw_html = ""
    if not outfit.get("items") and not why:
        raw = outfit.get("raw", "")
        raw_c = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", raw)
        raw_c = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", raw_c)
        raw_c = raw_c.replace("\n", "<br>")
        raw_html = f'<div style="font-size:14px;color:#374151;line-height:1.7">{raw_c}</div>'

    border_style = "border-color:#7C5CFC;box-shadow:0 4px 20px rgba(124,92,252,0.15)" if is_best else ""

    return f"""
<div class="cc-outfit-card" style="{border_style}">
  <div style="padding:20px">
    {best_badge}
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px">
      <span style="font-size:16px;font-weight:700;color:#1A1A1A">
        Outfit {idx + 1}: {outfit['title']}</span>
      {rain_badge}
    </div>
    {items_html}
    {raw_html}
    {why_html}
    {guide_html}
  </div>
</div>
"""


def _failure_html(agent_response: str) -> str:
    """Render a failure/diagnosis response in the spec's failure card style."""
    clean = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", agent_response)
    clean = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", clean)
    clean = clean.replace("\n\n", "</p><p>").replace("\n", "<br>")
    return f"""
<div style="background:#FFFFFF;border-radius:16px;border:1px solid #E8E5E0;
     box-shadow:0 2px 8px rgba(0,0,0,0.05);padding:24px">
  <div style="font-size:11px;font-weight:700;letter-spacing:1px;
       text-transform:uppercase;color:#D97706;margin-bottom:12px">
    We couldn't find a perfect match
  </div>
  <div class="cc-fail-box">
    <div style="font-size:14px;color:#1A1A1A;line-height:1.7">
      <p>{clean}</p>
    </div>
  </div>
</div>
"""


# ─── feedback chips ────────────────────────────────────────────────────────────

_FEEDBACK_CHIPS = [
    ("More formal",         "Make the outfit more formal."),
    ("More casual",         "Make it more casual and relaxed."),
    ("Different colour",    "Suggest a different colour combination."),
    ("No blazer",           "I don't want to wear a blazer."),
    ("Different footwear",  "Suggest different footwear."),
    ("Show more options",   "Show me more outfit options."),
]


# ─── tab builder ──────────────────────────────────────────────────────────────

def build_outfits_tab(prefill_state: gr.State) -> None:
    """
    Build the full Outfits tab.

    prefill_state : gr.State written by the Home tab with the user's request.
    """

    # Shared state
    outfits_state  = gr.State([])
    is_raining_st  = gr.State(False)
    history_state  = gr.State([])

    with gr.Column(elem_classes=["cc-page"]):

        # ══════════════════════════════════════════════════════════════════
        # VIEW A — Request
        # ══════════════════════════════════════════════════════════════════
        with gr.Column(visible=True) as view_request:

            gr.HTML("""
<div style="padding: 40px 0 24px">
  <h2 style="font-size:clamp(22px,2.5vw,32px);font-weight:800;color:#1A1A1A;
      letter-spacing:-0.5px;margin:0 0 8px">New outfit</h2>
  <p style="font-size:14px;color:#374151;margin:0">
    Describe what you need and CloseCall will check your wardrobe.</p>
</div>
""")

            request_input = gr.Textbox(
                placeholder="I need a semi-formal office outfit for today. It's raining and I want something comfortable.",
                show_label=False,
                lines=3,
                max_lines=6,
                elem_classes=["cc-input"],
            )

            with gr.Row():
                with gr.Column(scale=1, min_width=100):
                    reset_btn = gr.Button("↺ Reset", elem_classes=["cc-btn-ghost"])
                with gr.Column(scale=3):
                    send_btn = gr.Button("Get outfits →", elem_classes=["cc-btn-primary"])

            thinking_html = gr.HTML("")
            error_html    = gr.HTML("")

        # ══════════════════════════════════════════════════════════════════
        # VIEW B — Recommendations
        # ══════════════════════════════════════════════════════════════════
        with gr.Column(visible=False) as view_results:

            with gr.Row():
                back_btn = gr.Button("← Back", elem_classes=["cc-btn-ghost"])
                gr.HTML("""
<div style="flex:1;padding:40px 0 24px;padding-left:16px">
  <h2 style="font-size:clamp(20px,2.5vw,28px);font-weight:800;color:#1A1A1A;
      letter-spacing:-0.5px;margin:0">Your outfits</h2>
</div>
""")

            context_html = gr.HTML("")

            # Outfit cards — cc-outfit-grid gives side-by-side on desktop
            gr.HTML('<div class="cc-outfit-grid" id="outfit-grid-start"></div>')
            outfit_cards_html = gr.HTML("")

            gr.HTML('<div style="height:24px"></div>')
            with gr.Row():
                with gr.Column(scale=1):
                    try_another_btn = gr.Button("Try another", elem_classes=["cc-btn-secondary"])
                with gr.Column(scale=1):
                    looks_good_btn  = gr.Button("Looks good ✓", elem_classes=["cc-btn-accent"])

        # ══════════════════════════════════════════════════════════════════
        # VIEW C — Feedback / Refinement
        # ══════════════════════════════════════════════════════════════════
        with gr.Column(visible=False) as view_feedback:

            with gr.Row():
                back_fb_btn = gr.Button("← Back", elem_classes=["cc-btn-ghost"])
                gr.HTML("""
<div style="flex:1;padding:40px 0 24px;padding-left:16px">
  <h2 style="font-size:clamp(20px,2.5vw,26px);font-weight:800;color:#1A1A1A;
      letter-spacing:-0.5px;margin:0">How does this look?</h2>
</div>
""")

            gr.HTML("""
<div style="font-size:14px;color:#374151;margin-bottom:18px">
  What should I change?
</div>
""")

            # Quick-change chips in a 2-col responsive grid
            gr.HTML('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:20px" id="feedback-chips">')
            feedback_btns = [
                gr.Button(label, elem_classes=["cc-feedback-btn"])
                for label, _ in _FEEDBACK_CHIPS
            ]
            gr.HTML('</div>')

            gr.HTML("""
<div style="text-align:center;color:#D1CCC4;font-size:13px;margin:16px 0">— or —</div>
<div style="font-size:11px;font-weight:700;letter-spacing:1px;
     text-transform:uppercase;color:#6B7280;margin-bottom:8px">
  What should I change?
</div>
""")
            refinement_input = gr.Textbox(
                placeholder="e.g. Something without jeans, or more colourful…",
                show_label=False,
                lines=2,
                max_lines=5,
                elem_classes=["cc-input"],
            )
            refine_btn = gr.Button("Update outfit →", elem_classes=["cc-btn-primary"])
            refine_thinking = gr.HTML("")

        # ══════════════════════════════════════════════════════════════════
        # HELPERS
        # ══════════════════════════════════════════════════════════════════

        def _empty_wardrobe():
            return len(get_all_items()) == 0

        def _weather_context():
            profile = load_profile()
            w = get_weather(profile.get("location", "Mumbai"))
            return w.get("is_raining", False), w

        # Outputs shared by send & refine flows
        _SEND_OUTS = [
            view_request, view_results, view_feedback,
            history_state, thinking_html, error_html,
            outfits_state, is_raining_st,
            context_html, outfit_cards_html,
        ]

        # ── send: immediate feedback ──────────────────────────────────────
        def on_send_start(request, history):
            if not request.strip():
                return (
                    gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                    history, "", gr.update(value=""),
                    [], False, "", "",
                )
            return (
                gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                history, _thinking_html(0), gr.update(value=""),
                [], False, "", "",
            )

        # ── send: run agent ───────────────────────────────────────────────
        def on_send_execute(request, history):
            if not request.strip():
                return (
                    gr.update(), gr.update(), gr.update(),
                    history, "", gr.update(value=""),
                    [], False, "", "",
                )

            if _empty_wardrobe():
                err = (
                    '<div class="cc-error-box">'
                    '<strong>Wardrobe is empty.</strong> '
                    'Please add clothes first from the Wardrobe tab.</div>'
                )
                return (
                    gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                    history, "", gr.update(value=err),
                    [], False, "", "",
                )

            is_raining, w = _weather_context()
            agent = get_agent()

            try:
                response = agent.chat(request)
            except Exception as exc:
                err = f'<div class="cc-error-box"><strong>Error:</strong> {exc}</div>'
                return (
                    gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                    history, "", gr.update(value=err),
                    [], False, "", "",
                )

            new_hist = history + [[request, response]]

            # Context bar
            temp = w.get("temperature_c", "")
            cond = w.get("condition", "").title()
            rain_txt = " · 🌧 Rainy" if is_raining else ""
            ctx = (
                f'<div style="font-size:12px;color:#6B7280;letter-spacing:0.3px;'
                f'margin-bottom:20px">{cond} · {temp}°C{rain_txt}</div>'
            )

            # Failure path
            if _is_failure_response(response):
                cards_html = _failure_html(response)
                return (
                    gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
                    new_hist, _thinking_html(99), gr.update(value=""),
                    [], is_raining, ctx, cards_html,
                )

            outfits = _parse_outfits(response)
            cards_html = (
                '<div class="cc-outfit-grid">'
                + "".join(
                    _outfit_card_html(o, i, is_best=(i == 0), is_raining=is_raining)
                    for i, o in enumerate(outfits)
                )
                + '</div>'
            )

            return (
                gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
                new_hist, _thinking_html(99), gr.update(value=""),
                outfits, is_raining, ctx, cards_html,
            )

        send_btn.click(
            fn=on_send_start,
            inputs=[request_input, history_state],
            outputs=_SEND_OUTS,
        ).then(
            fn=on_send_execute,
            inputs=[request_input, history_state],
            outputs=_SEND_OUTS,
        )

        request_input.submit(
            fn=on_send_start,
            inputs=[request_input, history_state],
            outputs=_SEND_OUTS,
        ).then(
            fn=on_send_execute,
            inputs=[request_input, history_state],
            outputs=_SEND_OUTS,
        )

        # ── back / navigation ─────────────────────────────────────────────
        def _show(req=False, res=False, fb=False):
            return gr.update(visible=req), gr.update(visible=res), gr.update(visible=fb)

        back_btn.click(
            fn=lambda: _show(req=True),
            outputs=[view_request, view_results, view_feedback],
        )
        back_fb_btn.click(
            fn=lambda: _show(res=True),
            outputs=[view_request, view_results, view_feedback],
        )
        try_another_btn.click(
            fn=lambda: _show(fb=True),
            outputs=[view_request, view_results, view_feedback],
        )
        looks_good_btn.click(
            fn=lambda: _show(req=True),
            outputs=[view_request, view_results, view_feedback],
        )

        # ── refinement ────────────────────────────────────────────────────
        _REFINE_OUTS = [
            view_request, view_results, view_feedback,
            history_state, outfits_state, is_raining_st,
            context_html, outfit_cards_html, refine_thinking,
        ]

        def do_refinement(text, history, outfits, is_raining):
            if not text.strip():
                return (
                    gr.update(), gr.update(visible=True), gr.update(),
                    history, outfits, is_raining, "", "", "",
                )

            # Persist as long-term preference
            try:
                from src.database.preferences import add_preference_note
                add_preference_note("default_user", text)
            except Exception:
                pass

            agent = get_agent()
            try:
                response = agent.chat(text)
            except Exception as exc:
                response = f"Error: {exc}"

            new_hist   = history + [[text, response]]
            new_outfits = _parse_outfits(response)

            if _is_failure_response(response):
                cards_html = _failure_html(response)
            else:
                cards_html = (
                    '<div class="cc-outfit-grid">'
                    + "".join(
                        _outfit_card_html(o, i, is_best=(i == 0), is_raining=is_raining)
                        for i, o in enumerate(new_outfits)
                    )
                    + '</div>'
                )

            return (
                gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
                new_hist, new_outfits, is_raining, "", cards_html, "",
            )

        refine_btn.click(
            fn=do_refinement,
            inputs=[refinement_input, history_state, outfits_state, is_raining_st],
            outputs=_REFINE_OUTS,
        )
        refinement_input.submit(
            fn=do_refinement,
            inputs=[refinement_input, history_state, outfits_state, is_raining_st],
            outputs=_REFINE_OUTS,
        )

        # Wire quick-change chips
        for btn, (_, prompt_text) in zip(feedback_btns, _FEEDBACK_CHIPS):
            btn.click(
                fn=lambda h, o, r, pt=prompt_text: do_refinement(pt, h, o, r),
                inputs=[history_state, outfits_state, is_raining_st],
                outputs=_REFINE_OUTS,
            )

        # ── reset ─────────────────────────────────────────────────────────
        def on_reset():
            reset_agent()
            return (
                gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                [], _thinking_html(-1), gr.update(value=""),
                [], False, "", "",
            )

        reset_btn.click(fn=on_reset, outputs=_SEND_OUTS)
