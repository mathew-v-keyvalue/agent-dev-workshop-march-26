import uuid

import streamlit as st
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage

from src.agents.chat import ChatAgent
from src.db import execute_query

st.set_page_config(page_title="KVKart Chat", page_icon="💬", layout="centered")
st.title("💬 KVKart Chat")

DOMAIN_NODES = {"order_management", "product_discovery", "general_assistant"}


def get_agent():
    """Create a fresh agent each time so code changes in src/agents/chat.py are picked up
    after a full app restart (Streamlit rerun does not re-import Python modules)."""
    return ChatAgent()


def _user_id_from_email(email: str) -> int | None:
    if not (email or "").strip():
        return None
    rows = execute_query(
        "SELECT user_id FROM users WHERE LOWER(email) = LOWER(%s)",
        (email.strip(),),
    )
    return rows[0]["user_id"] if rows else None


def _emails_from_db() -> list[str]:
    try:
        rows = execute_query(
            "SELECT email FROM users WHERE account_status = 'active' "
            "AND email IS NOT NULL ORDER BY user_id"
        )
        return [r["email"] for r in rows if r.get("email")]
    except Exception:
        return []


def _extract_text(content) -> str:
    """Extract clean text from content that may be str or list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return str(content)


# ── Session state ────────────────────────────────────────────────────────

if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = None
if "current_user_email" not in st.session_state:
    st.session_state.current_user_email = None
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "active_thread" not in st.session_state:
    st.session_state.active_thread = None
if "thread_order" not in st.session_state:
    st.session_state.thread_order = []


def _new_conversation():
    tid = str(uuid.uuid4())
    st.session_state.conversations[tid] = []
    st.session_state.thread_order.append(tid)
    st.session_state.active_thread = tid


def _ensure_conversation():
    if not st.session_state.thread_order:
        _new_conversation()


def _get_messages() -> list[dict]:
    tid = st.session_state.active_thread
    if tid and tid in st.session_state.conversations:
        return st.session_state.conversations[tid]
    return []


# ── Sidebar ──────────────────────────────────────────────────────────────

def _on_email_change():
    choice = st.session_state.user_email_select
    uid = _user_id_from_email(choice) if choice else None
    if uid is not None:
        st.session_state.current_user_id = uid
        st.session_state.current_user_email = (choice or "").strip()
    else:
        st.session_state.current_user_id = None
        st.session_state.current_user_email = None
    st.session_state.conversations = {}
    st.session_state.thread_order = []
    st.session_state.active_thread = None


with st.sidebar:
    st.header("User")
    emails = _emails_from_db()
    if emails:
        if st.session_state.current_user_id is None:
            uid = _user_id_from_email(emails[0])
            if uid is not None:
                st.session_state.current_user_email = emails[0].strip()
                st.session_state.current_user_id = uid
    st.selectbox(
        "Email",
        options=emails,
        index=(
            emails.index(st.session_state.current_user_email)
            if st.session_state.current_user_email in emails
            else 0
        ),
        key="user_email_select",
        on_change=_on_email_change,
        help="Select a user. Orders, cart, etc. are looked up for this user.",
    )

    st.divider()
    st.header("Conversations")
    if st.button("➕ New Chat"):
        _new_conversation()
        st.rerun()

    _ensure_conversation()

    for i, tid in enumerate(st.session_state.thread_order):
        label = f"Chat {i + 1}"
        if tid == st.session_state.active_thread:
            st.button(label, key=f"conv_{tid}", disabled=True)
        else:
            if st.button(label, key=f"conv_{tid}"):
                st.session_state.active_thread = tid
                st.rerun()

    with st.expander("Debug", expanded=False):
        st.text(f"user_id: {st.session_state.current_user_id}")
        st.text(f"email: {st.session_state.current_user_email or '(none)'}")
        st.text(f"threads: {len(st.session_state.thread_order)}")
        st.text(f"active: {st.session_state.active_thread}")
        tid = st.session_state.active_thread
        if tid:
            st.text(f"messages in thread: {len(st.session_state.conversations.get(tid, []))}")

# ── Main chat area ───────────────────────────────────────────────────────

for msg in _get_messages():
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("What would you like to know?"):
    uid = st.session_state.current_user_id
    if uid is None:
        st.error("Please select a user in the sidebar.")
    else:
        tid = st.session_state.active_thread
        st.session_state.conversations[tid].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            accumulated_text = ""

            for mode, data in get_agent().stream(prompt, tid, uid):
                if mode == "messages":
                    msg_chunk, metadata = data
                    node = metadata.get("langgraph_node", "")
                    if node in DOMAIN_NODES and isinstance(msg_chunk, AIMessageChunk):
                        text = _extract_text(msg_chunk.content)
                        if text:
                            accumulated_text += text
                            response_placeholder.markdown(accumulated_text + "▌")

                elif mode == "updates":
                    if not isinstance(data, dict):
                        continue
                    for node_name, node_output in data.items():
                        if node_name == "intent" and "intent" in node_output:
                            st.status(
                                f"Intent: **{node_output['intent']}**",
                                state="complete",
                            )
                        if node_name in DOMAIN_NODES and "messages" in node_output:
                            for m in node_output["messages"]:
                                if isinstance(m, AIMessage) and m.tool_calls:
                                    for tc in m.tool_calls:
                                        with st.expander(
                                            f"🔧 Tool call: {tc['name']}",
                                            expanded=False,
                                        ):
                                            st.json(tc["args"])
                                elif isinstance(m, ToolMessage):
                                    with st.expander(
                                        f"📦 Result: {m.name}", expanded=False
                                    ):
                                        st.code(str(m.content), language="json")

            if accumulated_text:
                response_placeholder.markdown(accumulated_text)
            else:
                accumulated_text = "I couldn't generate a response."
                response_placeholder.markdown(accumulated_text)

            st.session_state.conversations[tid].append(
                {"role": "assistant", "content": accumulated_text}
            )
