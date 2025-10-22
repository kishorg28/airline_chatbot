from fastapi import FastAPI
from app.routes import router

# FastAPI app instance
app = FastAPI(title="Configurable Airline Support Agent API")
app.include_router(router)
