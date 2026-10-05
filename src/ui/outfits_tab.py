"""
Outfits Tab — CloseCall
────────────────────────
Two views:

  View A — Request input + agent processing checklist
  View B — Results (stays visible after "Looks good"; inline refinement)

"Try another" fires agent inline and updates cards without leaving results.
"Looks good" shows a confirmation banner and stays on results.
"Change something" opens a refinement row inline below the cards.
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
            f'padding:8px 0;border-bottom:1px solid #F0EDE8;font-size:14px;color:#1A1A1A">'
            f'  <span style="color:#1A1A1A;font-weight:500">{label}</span>'
            f'  <span style="color:{color};font-weight:700;font-size:16px">{icon}</span>'
            f'</div>'
        )
    return f'<div class="cc-agent-steps">{rows}</div>'


# ─── response parser ───────────────────────────────────────────────────────────

def _parse_outfits(text: str) -> list[dict]:
    heading_re = re.compile(r"#{1,3}\s*Outfit\s+(\d+)\s*[:\-–]?\s*([^\n]*)", re.IGNORECASE)
    headings = list(heading_re.finditer(text))
    if not headings:
        return [{"title": "Recommendation", "items": [], "why": "", "guidance": "", "raw": text.strip()}]
    outfits = []
    for i, match in enumerate(headings):
        title = match.group(2).strip().strip("*").strip()
        start = match.end()
        end   = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        block = text[start:end]
        item_re = re.compile(r"-\s+\*{0,2}(.+?)\*{0,2}\s*[—–\-]+\s*(item_\S+)", re.MULTILINE)
        items = [{"name": m.group(1).strip(), "item_id": m.group(2).strip().rstrip(".,)")}
                 for m in item_re.finditer(block)]
        why_re = re.compile(r"\*?Why(?:\s+this\s+works)?\*?[:\s]+(.+?)(?:\n\n|\*?Styling|\Z)",
                             re.IGNORECASE | re.DOTALL)
        why_m  = why_re.search(block)
        why    = why_m.group(1).strip().strip("*") if why_m else ""
        guide_re = re.compile(r"\*?Styling\s+guidance\*?[:\s]+(.+?)(?:\n\n|\Z)",
                               re.IGNORECASE | re.DOTALL)
        guide_m  = guide_re.search(block)
        guidance = guide_m.group(1).strip().strip("*") if guide_m else ""
        outfits.append({"title": title, "items": items, "why": why,
                        "guidance": guidance, "raw": block.strip()})
    return outfits[:3]


def _is_failure_response(text: str) -> bool:
    lower = text.lower()
    signals = ["couldn't find", "could not find", "no valid outfit",
               "no suitable outfit", "no outfit", "couldn't complete",
               "nothing suitable", "wardrobe doesn't have"]
    return any(s in lower for s in signals) and "outfit 1" not in lower


# ─── HTML builders ────────────────────────────────────────────────────────────

def _outfit_card_html(outfit: dict, idx: int, is_best: bool = False,
                      is_raining: bool = False) -> str:
    best_badge = ('<span class="cc-badge-violet" style="margin-bottom:10px;display:inline-block">'
                  'BEST MATCH</span>' if is_best else "")
    rain_badge = ('<span class="cc-badge-rain" style="margin-left:6px">🌧 Rain suitable</span>'
                  if is_raining else "")
    items_html = ""
    for item in outfit.get("items", []):
        items_html += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:9px 0;border-bottom:1px solid #F8F7F5;font-size:14px">'
            f'  <span style="color:#1A1A1A;font-weight:500">{item["name"]}</span>'
            f'  <span style="color:#9CA3AF;font-size:11px;font-family:monospace">{item["item_id"]}</span>'
            f'</div>'
        )
    why = (outfit.get("why") or "").strip()
    why_html = ""
    if why:
        why_c = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", why).replace("\n", " ")
        why_c = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", why_c)
        why_html = (
            f'<div class="cc-why-box">'
            f'  <div style="font-size:11px;font-weight:700;letter-spacing:1px;'
            f'text-transform:uppercase;color:#15803D;margin-bottom:6px">Why this works</div>'
            f'  <div style="font-size:13px;color:#1A5C2E;line-height:1.6">{why_c}</div>'
            f'</div>'
        )
    guidance = (outfit.get("guidance") or "").strip()
    guide_html = ""
    if guidance:
        guide_c = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", guidance).replace("\n", " ")
        guide_html = (
            f'<div style="margin-top:10px;padding:12px 14px;background:#F5F3FF;border-radius:10px">'
            f'  <div style="font-size:11px;font-weight:700;letter-spacing:1px;'
            f'text-transform:uppercase;color:#5B3FD4;margin-bottom:5px">▸ Styling guidance</div>'
            f'  <div style="font-size:13px;color:#4C3BA0;line-height:1.5">{guide_c}</div>'
            f'</div>'
        )
    raw_html = ""
    if not outfit.get("items") and not why:
        raw = outfit.get("raw", "")
        raw_c = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", raw)
        raw_c = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", raw_c)
        raw_c = raw_c.replace("\n", "<br>")
        raw_html = f'<div style="font-size:14px;color:#1A1A1A;line-height:1.7">{raw_c}</div>'
    border = "border-color:#7C5CFC;box-shadow:0 4px 20px rgba(124,92,252,0.15)" if is_best else ""
    return f"""
<div class="cc-outfit-card" style="{border}">
  <div style="padding:20px">
    {best_badge}
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap">
      <span style="font-size:16px;font-weight:700;color:#1A1A1A">
        Outfit {idx + 1}: {outfit['title']}</span>{rain_badge}
    </div>
    {items_html}{raw_html}{why_html}{guide_html}
  </div>
</div>"""


def _failure_html(agent_response: str) -> str:
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
    <div style="font-size:14px;color:#1A1A1A;line-height:1.7"><p>{clean}</p></div>
  </div>
</div>"""


def _cards_html(outfits, is_raining):
    return (
        '<div class="cc-outfit-grid">'
        + "".join(_outfit_card_html(o, i, is_best=(i == 0), is_raining=is_raining)
                  for i, o in enumerate(outfits))
        + '</div>'
    )


# ─── tab builder ──────────────────────────────────────────────────────────────

def build_outfits_tab(prefill_state: gr.State) -> None:

    outfits_state = gr.State([])
    is_raining_st = gr.State(False)
    history_state = gr.State([])

    with gr.Column(elem_classes=["cc-page"]):

        # ══════════════════════════════════════════════════════════════════
        # VIEW A — Request
        # ══════════════════════════════════════════════════════════════════
        with gr.Column(visible=True) as view_request:

            gr.HTML("""
<div style="padding:40px 0 16px">
  <h2 style="font-size:clamp(22px,2.5vw,32px);font-weight:800;color:#1A1A1A;
      letter-spacing:-0.5px;margin:0 0 8px">New outfit</h2>
  <p style="font-size:14px;color:#374151;margin:0">
    Describe what you need and CloseCall will check your wardrobe.</p>
</div>
""")
            with gr.Row(elem_classes=["cc-label-row"]):
                gr.HTML('<div style="font-size:11px;font-weight:700;letter-spacing:1px;'
                        'text-transform:uppercase;color:#6B7280;padding:4px 0">What do you need?</div>')
                reset_btn = gr.Button("↺ Start over", elem_classes=["cc-btn-ghost"], size="sm")

            request_input = gr.Textbox(
                placeholder="I need a semi-formal office outfit for today…",
                show_label=False, lines=3, max_lines=6,
                elem_classes=["cc-input"],
            )
            send_btn      = gr.Button("Get outfits →", elem_classes=["cc-btn-primary"])
            thinking_html = gr.HTML("")
            error_html    = gr.HTML("")

        # ══════════════════════════════════════════════════════════════════
        # VIEW B — Results  (stays visible; refinement happens inline)
        # ══════════════════════════════════════════════════════════════════
        with gr.Column(visible=False) as view_results:

            # Header row
            with gr.Row():
                back_btn = gr.Button("← New request", elem_classes=["cc-btn-ghost"])
                gr.HTML('<div style="flex:1;padding:40px 0 24px 16px">'
                        '<h2 style="font-size:clamp(20px,2.5vw,28px);font-weight:800;'
                        'color:#1A1A1A;letter-spacing:-0.5px;margin:0">Your outfits</h2></div>')

            context_html    = gr.HTML("")
            outfit_cards_html = gr.HTML("")

            # Confirmation banner (shown after "Looks good")
            confirm_banner = gr.HTML("")

            # Action row
            gr.HTML('<div style="height:20px"></div>')
            with gr.Row():
                with gr.Column(scale=1):
                    try_another_btn = gr.Button("Try another →", elem_classes=["cc-btn-secondary"])
                with gr.Column(scale=1):
                    change_btn  = gr.Button("Change something", elem_classes=["cc-btn-secondary"])
                with gr.Column(scale=1):
                    looks_good_btn = gr.Button("Looks good ✓", elem_classes=["cc-btn-accent"])

            # ── Inline refinement row (hidden until "Change something") ───
            with gr.Column(visible=False) as refine_row:
                gr.HTML('<div style="height:16px"></div>')
                gr.HTML('<hr style="border:none;border-top:1px solid #E8E5E0;margin:0 0 20px">')
                gr.HTML('<div style="font-size:13px;font-weight:600;color:#1A1A1A;margin-bottom:14px">'
                        'What should I change?</div>')

                # Quick chips
                chip_labels = ["More formal","More casual","Different colour",
                               "No blazer","Different footwear","Show more options"]
                chip_prompts = ["Make the outfit more formal.",
                                "Make it more casual and relaxed.",
                                "Suggest a different colour combination.",
                                "I don't want to wear a blazer.",
                                "Suggest different footwear.",
                                "Show me more outfit options."]

                with gr.Row():
                    refine_chips = [
                        gr.Button(lbl,
                                  elem_classes=["cc-chip"],
                                  size="sm")
                        for lbl in chip_labels
                    ]

                gr.HTML('<div style="margin:16px 0 8px;font-size:13px;color:#6B7280">'
                        '— or type your own —</div>')
                refine_input = gr.Textbox(
                    placeholder="e.g. No jeans, or something more colourful…",
                    show_label=False, lines=2, max_lines=4,
                    elem_classes=["cc-input"],
                )
                refine_submit = gr.Button("Update outfit →", elem_classes=["cc-btn-primary"])
                refine_thinking = gr.HTML("")

        # ══════════════════════════════════════════════════════════════════
        # HELPERS
        # ══════════════════════════════════════════════════════════════════

        def _weather_context():
            profile = load_profile()
            w = get_weather(profile.get("location", "Chennai"))
            return w.get("is_raining", False), w

        def _ctx_html(w, is_raining):
            temp = w.get("temperature_c", "")
            cond = w.get("condition", "").title()
            rain_txt = " · 🌧 Rainy" if is_raining else ""
            return (f'<div style="font-size:12px;color:#6B7280;margin-bottom:20px">'
                    f'{cond} · {temp}°C{rain_txt}</div>')

        # ── shared outputs for send flow ──────────────────────────────────
        _SEND_OUTS = [
            view_request, view_results,
            history_state, thinking_html, error_html,
            outfits_state, is_raining_st,
            context_html, outfit_cards_html, confirm_banner,
        ]

        def on_send_start(request, history):
            if not request.strip():
                return (gr.update(visible=True), gr.update(visible=False),
                        history, "", gr.update(value=""), [], False, "", "", "")
            return (gr.update(visible=True), gr.update(visible=False),
                    history, _thinking_html(0), gr.update(value=""), [], False, "", "", "")

        def on_send_execute(request, history):
            if not request.strip():
                return (gr.update(), gr.update(), history, "", gr.update(value=""),
                        [], False, "", "", "")
            if not get_all_items():
                err = ('<div class="cc-error-box"><strong>Wardrobe is empty.</strong> '
                       'Add clothes first.</div>')
                return (gr.update(visible=True), gr.update(visible=False),
                        history, "", gr.update(value=err), [], False, "", "", "")

            is_raining, w = _weather_context()
            agent = get_agent()
            try:
                response = agent.chat(request)
            except Exception as exc:
                err = f'<div class="cc-error-box"><strong>Error:</strong> {exc}</div>'
                return (gr.update(visible=True), gr.update(visible=False),
                        history, "", gr.update(value=err), [], False, "", "", "")

            new_hist = history + [[request, response]]
            ctx      = _ctx_html(w, is_raining)

            if _is_failure_response(response):
                return (gr.update(visible=False), gr.update(visible=True),
                        new_hist, _thinking_html(99), gr.update(value=""),
                        [], is_raining, ctx, _failure_html(response), "")

            outfits    = _parse_outfits(response)
            cards      = _cards_html(outfits, is_raining)
            return (gr.update(visible=False), gr.update(visible=True),
                    new_hist, _thinking_html(99), gr.update(value=""),
                    outfits, is_raining, ctx, cards, "")

        send_btn.click(fn=on_send_start, inputs=[request_input, history_state],
                       outputs=_SEND_OUTS).then(
            fn=on_send_execute, inputs=[request_input, history_state], outputs=_SEND_OUTS)
        request_input.submit(fn=on_send_start, inputs=[request_input, history_state],
                             outputs=_SEND_OUTS).then(
            fn=on_send_execute, inputs=[request_input, history_state], outputs=_SEND_OUTS)

        # ── Looks good — show confirmation, stay on results ───────────────
        def on_looks_good():
            banner = ('<div style="background:#F0FDF4;border:1px solid #BBF7D0;'
                      'border-radius:10px;padding:14px 18px;margin-top:16px;'
                      'font-size:14px;color:#15803D;font-weight:500">'
                      '✓ Great choice! Your outfit is saved for today.</div>')
            return banner

        looks_good_btn.click(fn=on_looks_good, outputs=[confirm_banner])

        # ── Try another — ask agent inline, update cards ──────────────────
        _REFRESH_OUTS = [outfit_cards_html, history_state, outfits_state, confirm_banner,
                         refine_thinking]

        def on_try_another(history, outfits, is_raining):
            agent = get_agent()
            try:
                response = agent.chat("Show me different outfit options.")
            except Exception as exc:
                return (_failure_html(str(exc)), history, outfits, "", "")
            new_hist = history + [["Show me different outfit options.", response]]
            if _is_failure_response(response):
                return (_failure_html(response), new_hist, [], "", "")
            new_outfits = _parse_outfits(response)
            return (_cards_html(new_outfits, is_raining), new_hist, new_outfits, "", "")

        try_another_btn.click(
            fn=on_try_another,
            inputs=[history_state, outfits_state, is_raining_st],
            outputs=_REFRESH_OUTS,
        )

        # ── Change something — toggle refinement row ──────────────────────
        change_btn.click(
            fn=lambda: gr.update(visible=True),
            outputs=[refine_row],
        )

        # ── Refinement submit ─────────────────────────────────────────────
        def do_refine(text, history, outfits, is_raining):
            if not text.strip():
                return (_cards_html(outfits, is_raining) if outfits else "",
                        history, outfits, "", "")
            try:
                from src.database.preferences import add_preference_note
                add_preference_note("default_user", text)
            except Exception:
                pass
            agent = get_agent()
            try:
                response = agent.chat(text)
            except Exception as exc:
                return (_failure_html(str(exc)), history, outfits, "", "")
            new_hist = history + [[text, response]]
            if _is_failure_response(response):
                return (_failure_html(response), new_hist, [], "", "")
            new_outfits = _parse_outfits(response)
            return (_cards_html(new_outfits, is_raining), new_hist, new_outfits, "", "")

        _REFINE_OUTS = [outfit_cards_html, history_state, outfits_state,
                        confirm_banner, refine_thinking]

        refine_submit.click(
            fn=do_refine,
            inputs=[refine_input, history_state, outfits_state, is_raining_st],
            outputs=_REFINE_OUTS,
        )
        refine_input.submit(
            fn=do_refine,
            inputs=[refine_input, history_state, outfits_state, is_raining_st],
            outputs=_REFINE_OUTS,
        )

        for chip, prompt in zip(refine_chips, chip_prompts):
            chip.click(
                fn=lambda h, o, r, pt=prompt: do_refine(pt, h, o, r),
                inputs=[history_state, outfits_state, is_raining_st],
                outputs=_REFINE_OUTS,
            )

        # ── Back — go to new request, reset session ───────────────────────
        def on_back():
            reset_agent()
            return gr.update(visible=True), gr.update(visible=False)

        back_btn.click(fn=on_back, outputs=[view_request, view_results])

        # ── Reset ─────────────────────────────────────────────────────────
        def on_reset():
            reset_agent()
            return (gr.update(visible=True), gr.update(visible=False),
                    [], _thinking_html(-1), gr.update(value=""),
                    [], False, "", "", "")

        reset_btn.click(fn=on_reset, outputs=_SEND_OUTS)
