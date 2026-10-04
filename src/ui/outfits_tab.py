"""
Screens 7–10 — Outfits Tab
────────────────────────────
Screen 7  — Outfit Request   : conversational input + agent thinking steps
Screen 8  — Recommendations  : tabbed outfit cards (Outfit 1 / 2 / 3)
Screen 9  — Outfit Detail    : expanded item breakdown per outfit
Screen 10 — Feedback         : quick-pick chips + free-text refinement

The whole flow lives inside a single tab managed by a gr.State("view")
that switches between sub-views via gr.update(visible=...) on each Column.
"""

from __future__ import annotations
import re
import gradio as gr

from src.agent.stylist_agent import get_agent, reset_agent
from src.database.db import get_all_items
from src.tools.weather import get_weather
from src.database.profile import load_profile


# ─── agent thinking HTML ──────────────────────────────────────────────────────

_AGENT_STEPS = [
    ("Fetching weather for your location…",    "🌤️"),
    ("Filtering your wardrobe…",               "👗"),
    ("Generating outfit combinations…",        "✨"),
    ("Validating for occasion and weather…",   "✅"),
]

def _thinking_html(active: int = -1) -> str:
    """active = index of currently running step (-1 = none yet, 99 = done)."""
    rows = ""
    for i, (label, icon) in enumerate(_AGENT_STEPS):
        if i < active:
            color, check = "#22C55E", "✅"
        elif i == active:
            color, check = "#8B5CF6", "⏳"
        else:
            color, check = "#D1D5DB", "○"
        rows += (
            f'<div class="cc-agent-step-item" style="color:{color}">'
            f'  <span>{check}</span>'
            f'  <span style="color:#374151;font-size:13px">{label}</span>'
            f'</div>'
        )
    return f'<div class="cc-agent-steps">{rows}</div>'


# ─── outfit card HTML helpers ─────────────────────────────────────────────────

def _parse_outfits(agent_response: str) -> list[dict]:
    """
    Parse the agent response into outfit dicts.
    Handles the format:
        ### Outfit 1: Title
        - **Item name** — item_id
        *Why this works:* explanation
    """
    outfits: list[dict] = []

    # Find every "### Outfit N: Title" heading and its position
    heading_pattern = re.compile(
        r"#{1,3}\s*Outfit\s+(\d+)\s*[:\-–]?\s*([^\n]*)",
        re.IGNORECASE
    )
    headings = list(heading_pattern.finditer(agent_response))

    if not headings:
        # No structured headings — return raw
        return [{"title": "Recommendation", "items": [], "why": "", "raw": agent_response.strip()}]

    for i, match in enumerate(headings):
        title = match.group(2).strip().strip("*").strip()
        # Block is from end of this heading to start of next (or end of string)
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(agent_response)
        block = agent_response[start:end]

        # Extract items: - **Name** — item_id
        item_pattern = re.compile(r"-\s+\*{0,2}(.+?)\*{0,2}\s*[—–-]+\s*(item_\S+)", re.MULTILINE)
        items = [
            {"name": m.group(1).strip(), "item_id": m.group(2).strip().rstrip(".,)")}
            for m in item_pattern.finditer(block)
        ]

        # Extract why: *Why this works:* text
        why_pattern = re.compile(r"\*?Why(?:\s+this\s+works)?\*?[:\s]+(.+?)(?:\n\n|\Z)", re.IGNORECASE | re.DOTALL)
        why_match = why_pattern.search(block)
        why = why_match.group(1).strip().strip("*") if why_match else ""

        outfits.append({"title": title, "items": items, "why": why, "raw": block.strip()})

    return outfits[:3]


def _outfit_card_html(outfit: dict, idx: int, is_raining: bool = False) -> str:
    badge = '<span class="cc-badge">🌧️ Rain Ready</span>' if is_raining else ""

    # Items list
    items_html = ""
    for item in outfit.get("items", []):
        items_html += (
            f'<div class="cc-outfit-item-row">'
            f'  <span style="color:#1C1C1E;font-size:14px;font-weight:500">{item["name"]}</span>'
            f'  <span style="color:#9CA3AF;font-size:11px;font-family:monospace">{item["item_id"]}</span>'
            f'</div>'
        )

    # Why section — only render if there is actual text
    why = (outfit.get("why") or "").strip()
    if why:
        lines = why.split("\n")
        bullet_items = [l.lstrip("-•* ").strip() for l in lines if re.match(r"^\s*[-•*]", l)]
        prose_lines  = [l.strip() for l in lines if l.strip() and not re.match(r"^\s*[-•*]", l)]
        bullets_html = ""
        if bullet_items:
            bullets_html = "<ul style='margin:6px 0 0 0;padding-left:18px'>" + \
                           "".join(f"<li style='margin-bottom:3px'>{b}</li>" for b in bullet_items) + \
                           "</ul>"
        prose_html = "".join(f"<p style='margin:0 0 4px'>{p}</p>" for p in prose_lines)
        why_html = (
            f'<div class="cc-outfit-why">'
            f'  <div style="font-weight:600;margin-bottom:6px">✅ Why this outfit?</div>'
            f'  {prose_html}{bullets_html}'
            f'</div>'
        )
    else:
        why_html = ""

    # Raw fallback — only when no structured items AND no why
    raw_html = ""
    if not outfit.get("items") and not why:
        raw = outfit.get("raw", "")
        # Render raw markdown-ish text cleanly
        raw_clean = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", raw)
        raw_clean = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", raw_clean)
        raw_clean = raw_clean.replace("\n", "<br>")
        raw_html = f'<div style="font-size:14px;color:#374151;line-height:1.7">{raw_clean}</div>'

    return f"""
<div style="background:#FFFFFF;border-radius:16px;padding:16px;
     box-shadow:0 2px 10px rgba(0,0,0,0.07);border:1px solid #F3F4F6;margin-bottom:8px">
  {badge}
  <div style="font-size:16px;font-weight:700;color:#1C1C1E;margin-bottom:12px">
    Outfit {idx+1}: {outfit['title']}
  </div>
  {items_html}
  {raw_html}
  {why_html}
</div>
"""


def _all_outfits_html(outfits: list[dict], is_raining: bool = False) -> str:
    if not outfits:
        return '<div style="padding:20px;text-align:center;color:#6B7280">No outfits generated yet.</div>'
    return "".join(_outfit_card_html(o, i, is_raining) for i, o in enumerate(outfits))


# ─── feedback chip definitions ────────────────────────────────────────────────

_FEEDBACK_CHIPS = [
    ("More formal",      "Make the outfit more formal."),
    ("More casual",      "Make the outfit more casual."),
    ("Different color",  "Suggest a different color combination."),
    ("No blazer",        "I don't want to wear a blazer."),
    ("Different footwear","Suggest different footwear."),
    ("Show more options","Show me more outfit options."),
]


# ─── main tab builder ─────────────────────────────────────────────────────────

def build_outfits_tab(prefill_state: gr.State) -> None:
    """
    Build the full Outfits tab (screens 7–10).

    Parameters
    ----------
    prefill_state : gr.State
        Shared state written by the Home tab when the user submits a request there.
        When this tab becomes active it reads from that state to pre-fill the input.
    """

    # ── Shared state ──────────────────────────────────────────────────────────
    outfits_state  = gr.State([])      # list of parsed outfit dicts
    is_raining_st  = gr.State(False)
    history_state  = gr.State([])      # chatbot history list[list[str]]

    with gr.Column(elem_classes=["cc-screen"]):

        # ═══════════════════════════════════════════════════════════════════
        # VIEW A — Request input (Screen 7)
        # ═══════════════════════════════════════════════════════════════════
        with gr.Column(visible=True) as view_request:

            gr.HTML(
                '<div style="font-size:20px;font-weight:700;color:#1C1C1E;'
                'padding:8px 0 4px">New Outfit ✨</div>'
            )

            # Chat history (shows user bubble + "Got it!" agent ack)
            chatbot = gr.Chatbot(
                label="",
                show_label=False,
                height=180,
                render_markdown=True,
                visible=False,
            )

            thinking_html = gr.HTML("")

            request_input = gr.Textbox(
                placeholder="I need a semi-formal office outfit for today. It's raining and around 24°C.",
                show_label=False,
                lines=2,
                max_lines=4,
                elem_classes=["cc-input"],
            )

            with gr.Row():
                reset_btn = gr.Button("↺", size="sm", elem_classes=["cc-chip"])
                send_btn  = gr.Button("→  Get Outfits", elem_classes=["cc-btn-primary"])

            error_html = gr.HTML("")

        # ═══════════════════════════════════════════════════════════════════
        # VIEW B — Recommendations (Screen 8)
        # ═══════════════════════════════════════════════════════════════════
        with gr.Column(visible=False) as view_results:

            with gr.Row():
                back_btn_results = gr.Button("← Back", size="sm", elem_classes=["cc-chip"])
                gr.HTML(
                    '<div style="font-size:18px;font-weight:700;color:#1C1C1E;'
                    'padding:8px 0;flex:1;text-align:center">'
                    'Here are 3 outfits for you ✨</div>'
                )

            results_context_html = gr.HTML("")   # e.g. "Semi-formal · Office · Rainy · 24°C"

            # Tab selector for Outfit 1 / 2 / 3
            outfit_selector = gr.Radio(
                choices=["Outfit 1", "Outfit 2", "Outfit 3"],
                value="Outfit 1",
                show_label=False,
            )
            outfit_display_html = gr.HTML("")

            with gr.Row():
                try_another_btn = gr.Button("Try Another", elem_classes=["cc-btn-secondary"])
                looks_good_btn  = gr.Button("Looks Good! 👍", elem_classes=["cc-btn-violet"])

        # ═══════════════════════════════════════════════════════════════════
        # VIEW C — Feedback / Refinement (Screen 10)
        # ═══════════════════════════════════════════════════════════════════
        with gr.Column(visible=False) as view_feedback:

            with gr.Row():
                back_btn_feedback = gr.Button("← Back", size="sm", elem_classes=["cc-chip"])
                gr.HTML(
                    '<div style="font-size:18px;font-weight:700;color:#1C1C1E;'
                    'padding:8px 0;flex:1">Not quite right? 🤔</div>'
                )

            gr.HTML(
                '<div style="font-size:14px;color:#6B7280;margin-bottom:12px">'
                'Tell me what you\'d like to change</div>'
            )

            # Quick feedback chips
            with gr.Column():
                feedback_chip_btns = [
                    gr.Button(label, elem_classes=["cc-feedback-chip"])
                    for label, _ in _FEEDBACK_CHIPS
                ]

            gr.HTML(
                '<div style="text-align:center;color:#D1D5DB;font-size:13px;'
                'margin:12px 0">— or —</div>'
            )

            refinement_input = gr.Textbox(
                placeholder="Describe what you want...",
                show_label=False,
                lines=2,
                max_lines=4,
                elem_classes=["cc-input"],
            )
            refine_btn = gr.Button("→  Refine", elem_classes=["cc-btn-primary"])

        # ═══════════════════════════════════════════════════════════════════
        # EVENT HANDLERS
        # ═══════════════════════════════════════════════════════════════════

        # ── helpers ───────────────────────────────────────────────────────────

        def _is_wardrobe_empty():
            return len(get_all_items()) == 0

        def _get_weather_flag():
            profile = load_profile()
            w = get_weather(profile.get("location","Mumbai"))
            return w.get("is_raining", False), w

        # ── send request (screen 7 → 8) ────────────────────────────────────

        _SEND_OUTPUTS = [
            view_request, view_results, view_feedback,
            history_state, thinking_html, chatbot, error_html,
            outfits_state, is_raining_st, results_context_html,
            outfit_display_html,
        ]

        def on_send_start(request, history):
            """Immediately show thinking state."""
            if not request.strip():
                return (
                    gr.update(visible=True),   # view_request
                    gr.update(visible=False),  # view_results
                    gr.update(visible=False),  # view_feedback
                    history,
                    _thinking_html(0),
                    gr.update(visible=True),   # chatbot
                    gr.update(value=""),       # error_html
                    [],                        # outfits_state
                    False,                     # is_raining
                    "",                        # results_context_html
                    "",                        # outfit_display_html
                )
            user_bubble = [[request, "Got it! I'll check the weather, look at your wardrobe and put together some options…"]]
            new_hist = history + user_bubble
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                new_hist,
                _thinking_html(1),
                gr.update(visible=True),
                gr.update(value=""),
                [],
                False,
                "",
                "",   # outfit_display_html
            )

        def on_send_execute(request, history):
            """Run the agent and parse results."""
            if not request.strip():
                return (
                    gr.update(), gr.update(), gr.update(),
                    history, "", gr.update(), gr.update(value=""),
                    [], False, "", "",
                )

            if _is_wardrobe_empty():
                err = (
                    '<div style="color:#EF4444;padding:8px;font-size:14px">'
                    '⚠️ Your wardrobe is empty. Please add clothes first.</div>'
                )
                return (
                    gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                    history, "", gr.update(), gr.update(value=err),
                    [], False, "", "",
                )

            is_raining, w = _get_weather_flag()
            agent = get_agent()

            try:
                response = agent.chat(request)
            except Exception as exc:
                err = f'<div style="color:#EF4444;font-size:13px;padding:8px">Error: {exc}</div>'
                return (
                    gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                    history, "", gr.update(), gr.update(value=err),
                    [], False, "", "",
                )

            outfits = _parse_outfits(response)
            new_hist = history + [[request, response]]

            temp = w.get("temperature_c", "")
            cond = w.get("condition", "")
            ctx_html = (
                f'<div style="font-size:12px;color:#6B7280;text-align:center;'
                f'margin-bottom:12px">{cond} · {temp}°C</div>'
            )

            first_html = _outfit_card_html(outfits[0], 0, is_raining) if outfits else ""

            return (
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
                new_hist,
                _thinking_html(99),
                gr.update(visible=True),
                gr.update(value=""),
                outfits,
                is_raining,
                ctx_html,
                first_html,   # outfit_display_html — populated here
            )

        send_btn.click(
            fn=on_send_start,
            inputs=[request_input, history_state],
            outputs=_SEND_OUTPUTS,
        ).then(
            fn=on_send_execute,
            inputs=[request_input, history_state],
            outputs=_SEND_OUTPUTS,
        )

        # Enter key also submits
        request_input.submit(
            fn=on_send_start,
            inputs=[request_input, history_state],
            outputs=_SEND_OUTPUTS,
        ).then(
            fn=on_send_execute,
            inputs=[request_input, history_state],
            outputs=_SEND_OUTPUTS,
        )

        # ── outfit tab selector ───────────────────────────────────────────────

        def on_outfit_select(choice, outfits, is_raining):
            idx = int(choice.split()[-1]) - 1
            if idx < len(outfits):
                return _outfit_card_html(outfits[idx], idx, is_raining)
            return ""

        outfit_selector.change(
            fn=on_outfit_select,
            inputs=[outfit_selector, outfits_state, is_raining_st],
            outputs=[outfit_display_html],
        )

        # Populate display when results arrive
        def _show_first_outfit(outfits, is_raining):
            if outfits:
                return _outfit_card_html(outfits[0], 0, is_raining)
            return ""

        # Trigger display update when outfits_state changes (via .then chain above)
        # We hook into looks_good_btn / try_another for now; results_context triggers
        # the HTML directly inside on_send_execute above.

        # ── back navigation ───────────────────────────────────────────────────

        back_btn_results.click(
            fn=lambda: (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)),
            outputs=[view_request, view_results, view_feedback],
        )
        back_btn_feedback.click(
            fn=lambda: (gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)),
            outputs=[view_request, view_results, view_feedback],
        )

        # ── "Try Another" → feedback ──────────────────────────────────────────

        try_another_btn.click(
            fn=lambda: (gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)),
            outputs=[view_request, view_results, view_feedback],
        )

        # ── "Looks Good!" → back to request (reset) ───────────────────────────

        looks_good_btn.click(
            fn=lambda: (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)),
            outputs=[view_request, view_results, view_feedback],
        )

        # ── feedback chip → refine ─────────────────────────────────────────────

        def _do_refinement(refinement_text, history, outfits, is_raining):
            if not refinement_text.strip():
                return (
                    gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
                    history, outfits, is_raining, "",
                )
            agent = get_agent()
            try:
                response = agent.chat(refinement_text)
            except Exception as exc:
                response = f"Error: {exc}"

            new_outfits = _parse_outfits(response)
            new_hist    = history + [[refinement_text, response]]
            first_html  = _outfit_card_html(new_outfits[0], 0, is_raining) if new_outfits else ""

            return (
                gr.update(visible=False),   # hide request
                gr.update(visible=True),    # show results
                gr.update(visible=False),   # hide feedback
                new_hist,
                new_outfits,
                is_raining,
                first_html,
            )

        _REFINE_OUTPUTS = [
            view_request, view_results, view_feedback,
            history_state, outfits_state, is_raining_st, outfit_display_html,
        ]

        refine_btn.click(
            fn=_do_refinement,
            inputs=[refinement_input, history_state, outfits_state, is_raining_st],
            outputs=_REFINE_OUTPUTS,
        )
        refinement_input.submit(
            fn=_do_refinement,
            inputs=[refinement_input, history_state, outfits_state, is_raining_st],
            outputs=_REFINE_OUTPUTS,
        )

        # Wire quick feedback chips
        for btn, (label, prompt_text) in zip(feedback_chip_btns, _FEEDBACK_CHIPS):
            btn.click(
                fn=lambda h, o, r, pt=prompt_text: _do_refinement(pt, h, o, r),
                inputs=[history_state, outfits_state, is_raining_st],
                outputs=_REFINE_OUTPUTS,
            )

        # ── reset session ─────────────────────────────────────────────────────

        def on_reset():
            reset_agent()
            return (
                gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                [], _thinking_html(-1), gr.update(value=[], visible=False),
                gr.update(value=""), [], False, "", "",
            )

        reset_btn.click(
            fn=on_reset,
            outputs=_SEND_OUTPUTS,
        )

        # ── pre-fill from Home tab ─────────────────────────────────────────────
        # Called externally via prefill_state change trigger set up in app.py
