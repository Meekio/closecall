"""
Gradio UI — Stylist Chat Tab.

Provides a conversational chat interface backed by the CloseCall reasoning agent.
"""

from __future__ import annotations

import gradio as gr

from src.agent.stylist_agent import get_agent, reset_agent
from src.database.db import get_all_items


# ─── Event handlers ───────────────────────────────────────────────────────────

def _check_wardrobe_empty(user_id: str = "default_user") -> bool:
    return len(get_all_items(user_id)) == 0


def handle_message(
    user_message: str,
    history: list[list[str]],
) -> tuple[list[list[str]], str]:
    """
    Process a user message through the stylist agent.

    Returns:
        Updated chat history and cleared input box.
    """
    if not user_message.strip():
        return history, ""

    if _check_wardrobe_empty():
        history = history + [
            [user_message, "⚠️ Your wardrobe is empty. Please go to the **My Wardrobe** tab "
             "and upload some clothing items before asking for outfit recommendations."]
        ]
        return history, ""

    agent = get_agent()

    try:
        response = agent.chat(user_message)
    except Exception as exc:
        response = (
            f"Sorry, I ran into an error: `{exc}`\n\n"
            "Please check that your GEMINI_API_KEY is set correctly in `.env`."
        )

    history = history + [[user_message, response]]
    return history, ""


def handle_reset(history: list[list[str]]) -> list[list[str]]:
    """Reset the agent session and clear chat history."""
    reset_agent()
    return []


# ─── Tab builder ──────────────────────────────────────────────────────────────

def build_stylist_tab() -> None:
    """Construct the Stylist Chat tab UI inside an active gr.Blocks context."""

    gr.Markdown("## 🪞 Your Personal Stylist")
    gr.Markdown(
        "Describe what you need and CloseCall will recommend outfits from your wardrobe. "
        "Try something like:\n"
        "> *\"I need a casual outfit for office today and it's raining.\"*\n\n"
        "> *\"Give me a formal office look for tomorrow.\"*\n\n"
        "> *\"Something comfortable for a weekend brunch.\"*"
    )

    chatbot = gr.Chatbot(
        label="CloseCall Stylist",
        height=500,
        render_markdown=True,
    )

    with gr.Row():
        msg_input = gr.Textbox(
            label="",
            placeholder="Describe what you need to wear...",
            scale=8,
            show_label=False,
            autofocus=True,
            max_lines=3,
        )
        send_btn = gr.Button("Send", variant="primary", scale=1, min_width=80)

    with gr.Row():
        reset_btn = gr.Button("🔄 Start new session", variant="secondary", size="sm")
        gr.Markdown(
            "<small>Starting a new session clears the conversation history and "
            "any session-specific constraints (e.g. 'no jeans').</small>"
        )

    # Sample request buttons
    with gr.Accordion("💡 Try a sample request", open=False):
        gr.Markdown("Click any example to use it:")
        with gr.Row():
            ex1 = gr.Button("Casual rainy office day", size="sm")
            ex2 = gr.Button("Formal office tomorrow", size="sm")
            ex3 = gr.Button("Weekend brunch", size="sm")
            ex4 = gr.Button("Evening dinner date", size="sm")

    # ── Wire events ───────────────────────────────────────────────────────────

    def _submit(message, history):
        return handle_message(message, history)

    send_btn.click(
        _submit,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input],
    )
    msg_input.submit(
        _submit,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input],
    )
    reset_btn.click(
        handle_reset,
        inputs=[chatbot],
        outputs=[chatbot],
    )

    # Sample requests
    ex1.click(
        lambda h: handle_message("I need a casual outfit for office today and it's raining.", h),
        inputs=[chatbot], outputs=[chatbot, msg_input],
    )
    ex2.click(
        lambda h: handle_message("Give me a formal office outfit for tomorrow.", h),
        inputs=[chatbot], outputs=[chatbot, msg_input],
    )
    ex3.click(
        lambda h: handle_message("Something comfortable and stylish for a weekend brunch.", h),
        inputs=[chatbot], outputs=[chatbot, msg_input],
    )
    ex4.click(
        lambda h: handle_message("I have a dinner date tonight, suggest something nice.", h),
        inputs=[chatbot], outputs=[chatbot, msg_input],
    )
