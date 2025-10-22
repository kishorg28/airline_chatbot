import os
from dotenv import load_dotenv
from fastapi import FastAPI
from app.routes import router

# Load environment variables from .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# FastAPI app instance
app = FastAPI(title="Configurable Airline Support Agent API")
app.include_router(router)
