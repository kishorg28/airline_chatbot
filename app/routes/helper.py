# bot_manager.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from fastapi import HTTPException
import os
import json

# Global stores
bot_configs = {}
memory_store = {}
policy_vectorstores = {}

# Shared function to load or build vectorstore
def get_or_load_vectorstore(bot_id: str) -> FAISS:
    if bot_id in policy_vectorstores:
        return policy_vectorstores[bot_id]

    save_path = os.path.join("faiss_indexes", bot_id)
    if not os.path.exists(save_path):
        raise HTTPException(status_code=404, detail="Vectorstore not found. Build the bot first.")

    try:
        vectorstore = FAISS.load_local(
            save_path,
            HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"),
            allow_dangerous_deserialization=True
        )
        policy_vectorstores[bot_id] = vectorstore
        return vectorstore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed loading index: {e}")

# Shared function to get or load bot config
def get_bot_config(bot_id: str) -> dict:
    if bot_id in bot_configs:
        return bot_configs[bot_id]

    try:
        with open(f"configs/{bot_id}_config.json", "r") as f:
            config = json.load(f)
        bot_configs[bot_id] = config
        return config
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Bot '{bot_id}' not found.")
