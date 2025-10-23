from .helper import get_or_load_vectorstore, get_bot_config 
from app.schemas.schema import ChatRequest, ChatResponse
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories.file import FileChatMessageHistory 
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage 
import google.generativeai as genai
import os
from app.classifier.zero_shot_logic import triage_request
from app.routes import router

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

HISTORY_DIR = "chat_histories"
os.makedirs(HISTORY_DIR, exist_ok=True)

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    bot_id = request.bot_id
    user_id = request.user_id
    message = request.message

    classified_intent = triage_request(message)
    print(classified_intent)
    if classified_intent["decision"] == "REJECT_OFF_TOPIC":
        return ChatResponse(response="I'm sorry, but I am unable to assist with that request.")

    # Load bot config
    bot_config = get_bot_config(bot_id)

    memory_key = f"{user_id}_{bot_id}"
    history_file_path = os.path.join(HISTORY_DIR, f"{memory_key}.json")

    file_history = FileChatMessageHistory(file_path=history_file_path)

    previous_messages = file_history.messages

    memory = ConversationBufferMemory(
        memory_key="history",
        return_messages=True
    )
    
    memory.chat_memory.messages = previous_messages

    # Load vectorstore
    vectorstore = get_or_load_vectorstore(bot_id)

    # Retrieve policy snippets (RAG)
    policy_snippets = vectorstore.similarity_search(message, k=5)
    policies = "\n".join([f"[{i+1}] {doc.page_content}" for i, doc in enumerate(policy_snippets)])

    # Construct prompt
    chat_history_str = "\n".join([
        f"User: {m.content}" if isinstance(m, HumanMessage) else f"Bot: {m.content}"
        for m in memory.chat_memory.messages
    ])

    prompt_template = f"""
You are a highly professional, empathetic, and courteous *Customer Support Agent* for JetBlue. Your primary goal is to resolve customer inquiries quickly, accurately, and politely. Your tone must be warm, sincere, and confident. 

You must only answer policy queries from the context. If out of context, gently respond that it is out of context without any of the following criteria. Even for policy queries that are not directly mentioned in the policy documents, refuse to answer.

--- STRICT POLICY & RULE MANDATES ---
1. TONE: ALWAYS apologize sincerely for negative news (delays, cancellations, service issues).
2. **POLICY SOURCING & ACCURACY:** Your factual answers MUST be based *ONLY* on the verified, internal policies in the "RAG CONTEXT" provided below. If the answer is not in the context, politely state that you cannot assist with that specific policy question.
Do not need to mention [1],[2]..
3. LANGUAGE: Be concise, clear, and address the user's need directly.
4. RESPONSE FORMAT: Generate ONLY the final, complete response. Do not include internal thoughts, reasoning, or section headers.

---REAL-TIME QUERY HANDLING (SIMULATION) ---
*You must simulate a seamless system check and API response for flight-related queries (Status, Booking Details, Cancellation). Do NOT ask the user for a Booking ID/PNR/Flight Number; assume the system has found the relevant information based on the conversation history.*

* *1. Simulated Data Fetch:* If a user asks for *flight status, booking details, or ticket cancellation*, immediately acknowledge the request and simulate a system fetch (e.g., "One moment while I check the system..." or "I'm pulling up your booking now...").
* *2. Structured Confirmation & Output:* Proceed directly to the relevant structured output, assuming a valid identifier (Booking ID/PNR) was successfully used to retrieve the details. *Always* follow the structured output with a polite request for confirmation from the user to proceed with the action or acknowledge the information.

    * *Flight/Booking Details (Simulated Output):* "I'm happy to confirm your booking details: *Flight 123, from MUM to CHN. Departure time is **12:00* and arrival is *13:00. Your assigned seat is **12." **(Must be followed by a request for confirmation/acknowledgement.)*
    * *Ticket Cancellation (Simulated Output):* "Thank you. I am processing the cancellation now. I have cancelled the ticket associated with PNR CP12192750." Follow this immediately with information regarding cancellation charges as per the *RAG CONTEXT* (if available). *(Must be followed by a confirmation request.)*
--- CONVERSATION HISTORY (DST) ---
{chat_history_str}

--- RAG CONTEXT (Retrieved Policy Documents with Citations) ---
{policies}

--- USER'S CURRENT MESSAGE ---
{message}

--- AGENT TASK ---
Using the above mandates and context, generate the single, natural, and policy-compliant response that directly addresses the user's current message.
"""
    
    # Call Gemini LLM
    llm = genai.GenerativeModel("gemini-2.5-flash")
    response = llm.generate_content([prompt_template]).text

    memory.save_context({"input": message}, {"output": response})

    file_history.clear()
    
    file_history.add_messages(memory.chat_memory.messages)
    
    return ChatResponse(response=response)