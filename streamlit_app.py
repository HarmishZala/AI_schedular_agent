import streamlit as st
import requests
import datetime

BASE_URL = "http://localhost:8000"  # Backend endpoint

# --- Set Streamlit dark theme ---
st.set_page_config(
    page_title="AI Scheduler",
    page_icon="🗓️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for dark mode and modern look ---
st.markdown(
    """
    <style>
    .stApp {background-color: #181c20; color: #f3f6fa;}
    .main {background-color: #181c20;}
    .stTextInput > div > div > input {font-size: 1.1rem; padding: 0.5rem; border-radius: 8px; background: #23272e; color: #f3f6fa; border: 1px solid #333;}
    .stButton > button {font-size: 1.1rem; border-radius: 8px; background: linear-gradient(90deg, #4F8BF9 0%, #1e293b 100%); color: white; border: none;}
    .stMarkdown {font-size: 1.08rem; color: #f3f6fa;}
    .stToast {font-size: 1.08rem; color: #f3f6fa; background: #23272e;}
    .stCaption {color: #b0b8c1;}
    .custom-card {background: #23272e; border-radius: 12px; padding: 1.2rem 1.5rem; margin-top: 1.2rem; box-shadow: 0 2px 8px #10151a; color: #f3f6fa;}
    .custom-header {margin-bottom: 1.5rem; font-size: 1.15rem; color: #f3f6fa;}
    .custom-sub {color: #b0b8c1;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🗓️ AI Scheduler")
st.caption("Your smart, beautiful calendar assistant.")

with st.container():
    st.markdown("""
    <div class='custom-header'>
        <b>What would you like to do?</b> <br>
        <span class='custom-sub'>E.g. <i>Schedule a meeting with Alice at 2pm tomorrow</i>, <i>Show my schedule for Friday</i>, <i>Delete all events between 2-7pm from tomorrow onwards</i></span>
    </div>
    """, unsafe_allow_html=True)

    with st.form(key="query_form", clear_on_submit=True):
        user_input = st.text_input(
            "Scheduling request",  # Non-empty label for accessibility
            placeholder="Type your scheduling request...",
            label_visibility="collapsed"
        )
        submit_button = st.form_submit_button("Send")

if submit_button and user_input.strip():
    try:
        with st.spinner("Agent is working on your request..."):
            payload = {"question": user_input}
            response = requests.post(f"{BASE_URL}/query", json=payload)

        if response.status_code == 200:
            answer = response.json().get("answer", "No answer returned.")
            # If it's a short confirmation, show as toast
            if answer.strip().startswith("Event '") or answer.strip().startswith("Event updated") or answer.strip().startswith("Event deleted") or answer.strip().startswith("Deleted "):
                st.toast(answer, icon="✅")
            else:
                st.markdown(f"<div class='custom-card'>" + answer + "</div>", unsafe_allow_html=True)
        else:
            st.error("Agent failed to respond: " + response.text)

    except Exception as e:
        st.error(f"The response failed due to {e}")