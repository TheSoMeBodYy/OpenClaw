import streamlit as st


def init_config():
    """
    Initialize default configuration in Streamlit session state.
    Ensures persona and user profile persist across reruns.
    """
    if "config" not in st.session_state:
        st.session_state.config = {
            "user_name": "User",
            "user_info": "",
            "agent_name": "OpenClaw",
            "agent_role": "Autonomous AI Agent",
            "system_instructions": ""
        }