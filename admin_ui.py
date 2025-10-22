# admin_ui.py
import streamlit as st
import requests

st.set_page_config(page_title="Bot Configuration", layout="wide")
st.title("🤖 Bot Builder Platform")
st.write("Create and configure a new conversational AI agent.")

API_URL = "http://127.0.0.1:8000/build"

with st.form("bot_builder_form"):
    st.header("Bot Configuration")
    bot_id = st.text_input("Bot ID (a unique identifier, e.g., 'jetblue_v1')", "airline_support_bot")
    bot_name = st.text_input("Bot Name (e.g., 'JetBlue Support Assistant')", "Airline Support Assistant")

    st.subheader("Knowledge Base")
    st.write("Enter URLs of webpages the bot should know about (e.g., policy pages).")
    url1 = st.text_input("URL 1", "https://www.jetblue.com/traveling-together/traveling-with-pets")
    url2 = st.text_input("URL 2", "https://www.jetblue.com/flying-with-us/our-fares")

    st.subheader("Bot Personality")
    system_prompt = st.text_area(
        "System Prompt (Instructions for the AI)",
        "You are a friendly and helpful airline support agent. You must use the 'get_policy_info' tool to answer any questions about policies. When using this tool, you must provide the user's query and the bot_id. Your current bot_id is '{bot_id}'. Be concise and professional.",
        height=200
    )

    submitted = st.form_submit_button("Build Bot")
    if submitted:
        urls = [url for url in [url1, url2] if url]
        if not all([bot_id, bot_name, system_prompt, urls]):
            st.error("Please fill out all fields.")
        else:
            with st.spinner("Building bot... This may take a moment."):
                config_payload = {
                    "bot_id": bot_id,
                    "bot_name": bot_name,
                    "system_prompt": system_prompt,
                    "knowledge_urls": urls
                }
                try:
                    response = requests.post(API_URL, json=config_payload)
                    if response.status_code == 200:
                        st.success(f"Bot '{bot_name}' built successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"Error building bot: {response.text}")
                except requests.RequestException as e:
                    st.error(f"Could not connect to the backend API. Is it running? Error: {e}")