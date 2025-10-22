import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


from ingest import create_knowledge_base_async


# Load environment variables from .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# FastAPI app instance
app = FastAPI(title="Configurable Airline Support Agent API")


# In-memory stores
bot_configs = {}
memory_store = {}
policy_vectorstores = {}


class BotConfigRequest(BaseModel):
    bot_id: str
    bot_name: str
    system_prompt: str
    knowledge_urls: list[str]  # matches admin UI payload


class ChatRequest(BaseModel):
    bot_id: str
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/build")
async def build_bot(config: BotConfigRequest):
    bot_id = config.bot_id
    bot_configs[bot_id] = config.dict()

    success = await create_knowledge_base_async(bot_id, config.knowledge_urls)
    if not success:
        raise HTTPException(status_code=400, detail="Could not create knowledge base. Check URLs.")

    # Load FAISS index after creation for immediate use
    save_path = os.path.join("faiss_indexes", bot_id)
    try:
        vectorstore = FAISS.load_local(
        save_path,
        HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"),
        allow_dangerous_deserialization=True
    )
        policy_vectorstores[bot_id] = vectorstore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed loading index: {e}")


    with open(f"configs/{bot_id}_config.json", "w") as f:
        json.dump(config.dict(), f)

    return {"message": f"Bot '{bot_id}' built and configured successfully."}
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    bot_id = request.bot_id
    user_id = request.user_id
    message = request.message

    if bot_id not in bot_configs:
        try:
            with open(f"configs/{bot_id}_config.json", "r") as f:
                bot_configs[bot_id] = json.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Bot '{bot_id}' not found.")

    bot_config = bot_configs[bot_id]

    memory_key = f"{user_id}_{bot_id}"
    if memory_key not in memory_store:
        memory_store[memory_key] = ConversationBufferMemory(memory_key="history", return_messages=True)
    memory = memory_store[memory_key]

    vectorstore = policy_vectorstores.get(bot_id)
    if not vectorstore:
        raise HTTPException(status_code=404, detail="Policy vectorstore not built yet.")

    # Retrieve most relevant policy chunks
    policy_snippets = vectorstore.similarity_search(message, k=5)
    relevant_policies = "\n".join([doc.page_content for doc in policy_snippets])

    # Construct prompt for Gemini LLM
    prompt_template = """
You are an airline customer support bot.
Your responses must strictly follow the policies below while being empathetic.

---POLICIES---
{policies}

---CONVERSATION HISTORY---
{history}

---USER QUERY---
{input}
---
"""
    chat_history_str = "\n".join(
        f"User: {m['input']}\nBot: {m['output']}" for m in getattr(memory.chat_memory, "messages", [])
    )
    prompt = prompt_template.format(
        policies=relevant_policies,
        history=chat_history_str,
        input=message,
    )

    # Call Gemini LLM
    llm = ChatGoogleGenerativeAI(model="gemini-1.0", temperature=0, api_key=GOOGLE_API_KEY)
    response = llm.invoke(prompt)

    # Save conversation context
    memory.save_context({"input": message}, {"output": response})

    return ChatResponse(response=response)