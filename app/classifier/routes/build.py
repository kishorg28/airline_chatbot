# build_endpoint.py
from fastapi import APIRouter, HTTPException
from helper import bot_configs, get_or_load_vectorstore
from schemas.schema import BotConfigRequest
from app.ingest import create_knowledge_base_async
import os
import json

router = APIRouter()

@router.post("/build")
async def build_bot(config: BotConfigRequest):
    bot_id = config.bot_id
    bot_configs[bot_id] = config.dict()

    # Create knowledge base
    success = await create_knowledge_base_async(bot_id, config.knowledge_urls)
    if not success:
        raise HTTPException(status_code=400, detail="Could not create knowledge base. Check URLs.")

    # Load FAISS index for immediate use
    vectorstore = get_or_load_vectorstore(bot_id)

    # Save bot config
    os.makedirs("configs", exist_ok=True)
    with open(f"configs/{bot_id}_config.json", "w") as f:
        json.dump(config.dict(), f)

    return {"message": f"Bot '{bot_id}' built and configured successfully."}
