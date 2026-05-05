from fastapi import FastAPI
from fastapi.security import HTTPBearer
from app.routers import auth, users

security = HTTPBearer()
app = FastAPI(title="Studio MH02")
app.include_router(auth.router)
app.include_router(users.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

