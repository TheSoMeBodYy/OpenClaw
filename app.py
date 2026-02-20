import streamlit as st
from agent import Agent
from config import init_config
from todo import load_todos

# Streamlit page configuration
st.set_page_config(page_title="OpenClaw", layout="wide")

# Initialize session config
init_config()

# ================= CONFIGURATION PANEL =================

st.sidebar.title("Configuration")

with st.sidebar.expander("User Profile", expanded=True):
    st.session_state.config["user_name"] = st.text_input(
        "User Name", st.session_state.config["user_name"]
    )
    st.session_state.config["user_info"] = st.text_area(
        "User Info", st.session_state.config["user_info"]
    )

with st.sidebar.expander("Agent Persona", expanded=True):
    st.session_state.config["agent_name"] = st.text_input(
        "Agent Name", st.session_state.config["agent_name"]
    )
    st.session_state.config["agent_role"] = st.text_input(
        "Agent Role", st.session_state.config["agent_role"]
    )
    st.session_state.config["system_instructions"] = st.text_area(
        "System Instructions",
        st.session_state.config.get("system_instructions", "")
    )

# Initialize agent instance
if "agent" not in st.session_state:
    st.session_state.agent = Agent(st.session_state.config)
else:
    st.session_state.agent.config = st.session_state.config

page = st.sidebar.radio("Navigation", ["Agent Interface", "Under the Hood"])

if "chat" not in st.session_state:
    st.session_state.chat = []

# ================= PAGE: AGENT INTERFACE =================

if page == "Agent Interface":
    st.title("OpenClaw")

    # Proactive suggestion
    proactive = st.session_state.agent.proactive_check()
    if proactive:
        st.info(proactive)

    # Chat history rendering
    for role, msg in st.session_state.chat:
        with st.chat_message(role):
            st.write(msg)

    user_input = st.chat_input("Message")

    if user_input:
        st.session_state.chat.append(("user", user_input))
        response = st.session_state.agent.reasoning_loop(user_input)
        st.session_state.chat.append(("assistant", response))
        st.rerun()

    # To-Do board display
    st.subheader("To-Do Board")
    todos = load_todos()
    for t in todos:
        icon = "Done" if t["done"] else "Pending"
        st.write(f"{icon} - {t['task']}")

# ================= PAGE: DEBUG VIEW =================

elif page == "Under the Hood":
    st.title("Debug & Memory")

    st.subheader("Working Memory")
    st.json(st.session_state.agent.get_working_memory())

    st.subheader("Internal Log")
    st.write("\n".join(st.session_state.agent.get_internal_log()))

    st.subheader("Long-Term Storage")
    collection = st.session_state.agent.memory.collection.get()
    st.json(collection)

    if "distances" in collection:
        st.subheader("Relevance Scores")
        st.json(collection["distances"])