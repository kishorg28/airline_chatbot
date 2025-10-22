# chat_ui.py
import streamlit as st
import requests
import os

st.set_page_config(page_title="Airline Support", layout="centered")
st.title("✈️ Airline Support Chat")

API_URL = "http://127.0.0.1:8000/chat"
USER_ID = "hackathon-user-01"

# --- Bot Selection ---
available_bots = [f.replace("_config.json", "") for f in os.listdir("configs") if f.endswith("_config.json")]

if not available_bots:
    st.warning("No bots have been built yet. Please use the Admin UI to build a bot first.")
    st.stop()

selected_bot = st.selectbox("Select a Bot to talk to:", available_bots)

session_key = f"messages_{selected_bot}"
if session_key not in st.session_state:
    st.session_state[session_key] = [{"role": "assistant", "content": f"Hello! I am the {selected_bot} assistant. How can I help you?"}]

# --- Display Chat History ---
for message in st.session_state[session_key]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- User Input ---
if prompt := st.chat_input("Ask a question..."):
    st.session_state[session_key].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        try:
            payload = {"bot_id": selected_bot, "user_id": USER_ID, "message": prompt}
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            assistant_response = response.json()["response"]
            message_placeholder.markdown(assistant_response)
            st.session_state[session_key].append({"role": "assistant", "content": assistant_response})
        except requests.RequestException as e:
            st.error(f"Error connecting to backend: {e}")