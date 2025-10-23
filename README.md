# Airline Support Chatbot

A FastAPI and Streamlit-based AI agent that provides airline policy support using a custom knowledge base.

---

## ⚙️ Installation

1. Clone this repository:
git clone https://github.com/yourusername/airline-support-chatbot.git
cd airline-support-chatbot


2. Create and activate a virtual environment:
python -m venv .venv
source .venv/bin/activate # On macOS/Linux
.venv\Scripts\activate # On Windows


3. Install dependencies:
pip install -r requirements.txt


---

## 🚀 Run the Backend (FastAPI)

Start the FastAPI application using **Uvicorn** (enables live reloading):
python -m uvicorn app.main:app --reload


Once the server starts, open your browser and visit:

http://127.0.0.1:8000/docs

This will open the Swagger UI for API testing.

---

## 💻 Run the Admin Dashboard (Streamlit)

Navigate to the UI directory and start the Admin dashboard:

cd app/ui
streamlit run admin_ui.py

---

## 💬 Run the Chat Interface (Streamlit)

To launch the chat user interface:

cd app/ui
streamlit run chat_ui.py

The chatbot UI will open in your default browser.

