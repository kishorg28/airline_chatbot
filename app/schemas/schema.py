from pydantic import BaseModel

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
