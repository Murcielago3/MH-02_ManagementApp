from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.routers import auth, users, clients, projects, dashboard, expenses, leaves, attendance, tasks, timesheets, uploads, reimbursements


security = HTTPBearer()
app = FastAPI(title="Studio MH02")

# CORS – allow the Vite dev server to reach the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files (profile photos, documents)
os.makedirs("static/uploads/photos", exist_ok=True)
os.makedirs("static/uploads/documents", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(projects.router)
app.include_router(dashboard.router)
app.include_router(expenses.router)
app.include_router(leaves.router)
app.include_router(attendance.router)
app.include_router(tasks.router)
app.include_router(timesheets.router)
app.include_router(uploads.router)
app.include_router(reimbursements.router)



@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def run_migrations():
    """Add any missing columns to existing tables."""
    from app.database import engine
    from sqlalchemy import text
    async with engine.begin() as conn:
        # Add color column to projects if missing
        try:
            await conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS color VARCHAR DEFAULT '#287475'"))
        except Exception:
            pass  # Column already exists or DB doesn't support IF NOT EXISTS

