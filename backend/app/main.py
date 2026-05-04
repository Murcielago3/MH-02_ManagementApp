from fastapi import FastAPI
from app.routers import auth

app = FastAPI(title="Studio MH02")
app.include_router(auth.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

