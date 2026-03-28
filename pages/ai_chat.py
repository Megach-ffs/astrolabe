import streamlit as sl
from utils import ai_assistant





sl.title(":material/chat: AI Chat & Code Snippets")
# no AI view
if not sl.session_state.get("ai_enabled"):
    sl.warning(":material/warning: AI Assistant is not enabled.")
    sl.info("To use this feature, toggle the AI Assistant in the sidebar.")
    sl.stop()

if not ai_assistant.is_available():
    sl.warning(":material/warning: AI Assistant Unavailable")
    sl.info("The Gemini API is not configured or is currently unresponsive. Please check your API key in `.streamlit/secrets.toml` or verify your quota.")
    sl.stop()

df = sl.session_state.get("df_working")

sl.markdown(
    "Ask questions about your data, request pandas code snippets to use locally, "
    "or get help interpreting your visualization and cleaning results."
)

if df is not None:
    sl.caption(f":material/robot: **Context attached:** Dashboard dataset ({len(df)} rows × {len(df.columns)} columns)")
else:
    sl.caption(":material/robot: **Context:** No dataset loaded.")

sl.markdown("---")

# saving chat history
if "ai_chat_messages" not in sl.session_state:
    sl.session_state.ai_chat_messages = []

# displaying chat messages from history on app rerun
for message in sl.session_state.ai_chat_messages:
    with sl.chat_message(message["role"]):
        sl.markdown(message["content"])

# user prompt input
initial_prompt = None
if "ai_chat_initial_prompt" in sl.session_state:
    initial_prompt = sl.session_state.pop("ai_chat_initial_prompt")

if prompt := sl.chat_input("Ask a question or request a pandas snippet...") or initial_prompt:
    # if typed use prompt, otherwise use initial
    active_prompt = prompt if isinstance(prompt, str) and prompt else initial_prompt
    
    # displaying user prompt
    with sl.chat_message("user"):
        sl.markdown(active_prompt)
    sl.session_state.ai_chat_messages.append({"role": "user", "content": active_prompt})

    # output
    with sl.chat_message("assistant"):
        stream = ai_assistant.chat_stream(df, sl.session_state.ai_chat_messages)
        response = sl.write_stream(stream)
    
    sl.session_state.ai_chat_messages.append({"role": "assistant", "content": response})

    # clear button
    c1, c2 = sl.columns([1, 10])
    with c1:
        if sl.button(":material/delete: Clear Chat", key="clear_chat"):
            sl.session_state.ai_chat_messages = []
            sl.rerun()
