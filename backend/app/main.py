from fastapi import FastAPI
from fastapi.security import HTTPBearer
from app.routers import auth, users, clients, projects, dashboard

security = HTTPBearer()
app = FastAPI(title="Studio MH02")
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(projects.router)
app.include_router(dashboard.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

