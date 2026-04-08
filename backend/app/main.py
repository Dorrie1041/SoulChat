from fastapi import FastAPI
from sqlalchemy import text

from app.db import engine, SessionLocal
from app.routes.chat import router as chat_router

app = FastAPI(title="SoulChat Backend")
app.include_router(chat_router)

@app.get("/")
async def root():
    return {"message": "SoulChat backend is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/db-test")
def db_test():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT NOW();"))
        now_value = result.scalar()
        return {"database_connected": True, "server_time": str(now_value)}
    finally:
        db.close()

@app.get("/chat")
async def chat():
    return {"reply": "Hello from FastAPI"}


