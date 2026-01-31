"""
AI Tutor - Gradio UI (v0.3)

Changes from v0.2:
- Multi-user support with user_id input
- Shows current action (skill vs conversation)
- Displays complete state (not just debug fields)
- Compatible with refactored TutorAgent
"""

import gradio as gr
import json
from engine.agent_coordinator import AgentCoordinator

# Initialize coordinator (entry point)
coordinator = AgentCoordinator()


def interact(message, history, user_id_input):
    """
    Main interaction function.

    Args:
        message: User's message
        history: Chat history (Gradio format)
        user_id_input: User ID from textbox

    Returns:
        Tuple: (formatted_answer, state_json)
    """
    if not message:
        return "", None

    # Use provided user_id or default
    user_id = user_id_input.strip() if user_id_input.strip() else "default_user"

    # Process message through coordinator
    result = coordinator.process_message(user_id, message)

    # Extract response components
    answer = result["ai_response"]
    state = result["state"]
    action = result["action"]

    # Format answer with action indicator
    action_emoji = "🎯" if action.startswith("skill:") else "💬"
    action_text = action.replace("skill:", "Skill: ").title()

    # Extract state fields for cleaner formatting
    workflow = state['workflow']['onboarding_progress']
    profile = state['semantic']['profile']

    point_a_done = workflow['point_a_done']
    point_a_fields = workflow.get('collected_fields', [])
    point_b_done = workflow.get('point_b_done', False)
    point_b_fields = workflow.get('collected_fields_point_b', [])

    name = profile.get('name') or '—'
    native = profile.get('native_lang') or '—'
    target = profile.get('target_lang') or '—'
    level = profile.get('level') or '—'

    formatted_answer = (
        f"{answer}\n\n"
        f"<details>\n"
        f"<summary>`🔍 Debug Info | {action_emoji} {action_text} | Click to expand ▼`</summary>\n\n"
        f"> **Session Info:**\n"
        f"> - User: `{user_id}`\n"
        f"> - Action: `{action}`\n\n"
        f"> **Onboarding Progress:**\n"
        f"> - Point A: {'✅ Done' if point_a_done else '⏳ In Progress'} ({len(point_a_fields)}/7 fields)\n"
        f"> - Point B: {'✅ Done' if point_b_done else '⏳ In Progress'} ({len(point_b_fields)}/5 fields)\n"
        f"> - Fields A: `{point_a_fields}`\n"
        f"> - Fields B: `{point_b_fields}`\n\n"
        f"> **Student Profile:**\n"
        f"> - Name: **{name}**\n"
        f"> - Languages: {native} → {target}\n"
        f"> - Level: **{level}**\n\n"
        f"</details>"
    )

    return formatted_answer, state


def export_session(user_id_input):
    """
    Export conversation as JSON file.

    Args:
        user_id_input: User ID to export

    Returns:
        File path to downloaded JSON, or None with error
    """
    user_id = user_id_input.strip() if user_id_input.strip() else "default_user"

    # Get export data
    export_data = coordinator.export_conversation(user_id)

    # Check for error
    if "error" in export_data:
        # Return error info as JSON file anyway
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='_error.json', delete=False) as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
            filepath = f.name
        return filepath

    # Save to temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
        filepath = f.name

    return filepath


# --- LAYOUT ---
with gr.Blocks(title="AI Tutor - Tech UI v0.3 (Multi-User + Skills)", theme=gr.themes.Default()) as demo:
    gr.Markdown("# AI Tutor - Tech UI (v0.3)")
    gr.Markdown("**Features:** Multi-user support • Point A + B Skills • Enhanced Tutoring • State persistence")

    with gr.Row():
        # Left => Chat (main area)
        with gr.Column(scale=7):
            chatbot = gr.Chatbot(type="messages", height=600)
            user_msg = gr.Textbox(
                label="Your message",
                placeholder="Type your message here...",
                show_label=False
            )
            submit_btn = gr.Button("Send", variant="primary")

        # Right => Sidebar (debug & controls)
        with gr.Column(scale=3, variant="panel"):
            gr.Markdown("### 🛠️ Controls & Debug")

            # User ID input
            user_id_input = gr.Textbox(
                label="👤 User ID",
                placeholder="Enter user ID",
                value="test_user",
                info="Each user has independent state"
            )

            # State viewer
            with gr.Accordion("🧠 Complete State", open=False):
                state_json = gr.JSON(label="Internal State", height=400)

            # Advanced section with export
            with gr.Accordion("⚙️ Advanced", open=False):
                gr.Markdown("**Export Session**")
                gr.Markdown("Download full conversation as JSON.")
                export_btn = gr.Button("📥 Download JSON", variant="secondary", size="sm")
                export_file = gr.File(label="Downloaded File")

                export_btn.click(
                    fn=export_session,
                    inputs=[user_id_input],
                    outputs=[export_file]
                )

    # Wire up the chat interaction
    def chat_wrapper(message, history, user_id):
        """Wrapper to handle chat interaction with proper history format."""
        formatted_response, state = interact(message, history, user_id)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": formatted_response})
        return history, "", state

    submit_btn.click(
        fn=chat_wrapper,
        inputs=[user_msg, chatbot, user_id_input],
        outputs=[chatbot, user_msg, state_json]
    )

    user_msg.submit(
        fn=chat_wrapper,
        inputs=[user_msg, chatbot, user_id_input],
        outputs=[chatbot, user_msg, state_json]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8080)
