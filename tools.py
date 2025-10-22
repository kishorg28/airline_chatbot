import os
import json
from langchain.tools import tool
from langchain_community.vectorstores.faiss import FAISS
from langchain_huggingface import HuggingFaceEmbeddings # <-- UPDATED IMPORT

INDEX_DIR = "faiss_indexes"
retriever_cache = {}
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

@tool
def get_policy_info(query: str, bot_id: str) -> str:
    """
    Use this to answer questions about the policies of a specific bot.
    You MUST provide both the user's query and the bot_id.
    """
    global retriever_cache
    
    if bot_id not in retriever_cache:
        print(f"Loading index for bot_id '{bot_id}' into cache...")
        index_path = os.path.join(INDEX_DIR, bot_id)
        if not os.path.exists(index_path):
            return f"Error: No knowledge base found for bot_id '{bot_id}'."
        vector_store = FAISS.load_local(index_path, embeddings_model, allow_dangerous_deserialization=True)
        retriever_cache[bot_id] = vector_store.as_retriever()

    retriever = retriever_cache[bot_id]
    docs = retriever.invoke(query)
    
    if not docs:
        return "I could not find any relevant information in the knowledge base."
        
    return "\n---\n".join([doc.page_content for doc in docs])

@tool
def get_booking_details(pnr: str) -> str:
    """Gets a customer's booking details using their PNR number."""
    print(f"--- FAKE API: Getting booking for PNR '{pnr}' ---")
    mock_response = {"pnr": pnr, "flight_id": "PSG123", "status": "On Time"}
    return json.dumps(mock_response)