# chat_endpoint.py
from fastapi import FastAPI, HTTPException
from .helper import memory_store, get_or_load_vectorstore, get_bot_config
from app.schemas.schema import ChatRequest, ChatResponse
from langchain.memory import ConversationBufferMemory
import google.generativeai as genai
import os
from app.classifier.zero_shot_logic import triage_request

app = FastAPI()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    bot_id = request.bot_id
    user_id = request.user_id
    message = request.message

    classified_intent = triage_request(message)
    if classified_intent["decision"] == "REJECT_OFF_TOPIC" and classified_intent["on_topic_score"] < 0.2:
        return ChatResponse(response="I'm sorry, but I am unable to assist with that request.")

    # Load bot config
    bot_config = get_bot_config(bot_id)

    # Load or create memory for this user-bot pair
    memory_key = f"{user_id}_{bot_id}"
    if memory_key not in memory_store:
        memory_store[memory_key] = ConversationBufferMemory(memory_key="history", return_messages=True)
    memory = memory_store[memory_key]

    # Load vectorstore
    vectorstore = get_or_load_vectorstore(bot_id)

    # Retrieve policy snippets (RAG)
    policy_snippets = vectorstore.similarity_search(message, k=5)
    policies = "\n".join([f"[{i+1}] {doc.page_content}" for i, doc in enumerate(policy_snippets)])

    # Construct prompt
    chat_history_str = "\n".join([
        f"User: {m.content}" if m.type == "human" else f"Bot: {m.content}"
        for m in memory.chat_memory.messages
    ])

    prompt_template = f"""
You are a highly professional, empathetic, and courteous Customer Support Agent for {bot_config.get('airline_name', 'the airline')}. Your primary goal is to resolve customer inquiries quickly, accurately, and politely. Your tone must be warm, sincere, and confident.

--- STRICT POLICY & RULE MANDATES ---
1. TONE: ALWAYS apologize sincerely for negative news (delays, cancellations, service issues).
2. GROUNDING & CITATION: Your factual answers MUST be based **ONLY** on the "RAG CONTEXT" provided below. You **MUST** include a **citation tag** (e.g., [1], [2]) corresponding to the policy chunk used in your answer. If the answer is not in the context, politely state that you cannot assist with that specific policy question.
3. LANGUAGE: Be concise, clear, and address the user's need directly.
4. RESPONSE FORMAT: Generate ONLY the final, complete response. Do not include internal thoughts, reasoning, or section headers.

--- CONVERSATION HISTORY (DST) ---
{chat_history_str}

--- RAG CONTEXT (Retrieved Policy Documents with Citations) ---
{policies}

--- USER'S CURRENT MESSAGE ---
{message}

--- AGENT TASK ---
Using the above mandates and context, generate the single, natural, and policy-compliant response that directly addresses the user's current message, including citation tags.
"""

    # Call Gemini LLM
    llm = genai.GenerativeModel("gemini-2.5-flash")
    response = llm.generate_content([prompt_template]).text

    # Save conversation context
    memory.save_context({"input": message}, {"output": response})

    return ChatResponse(response=response)
