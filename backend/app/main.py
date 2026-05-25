from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.routers import auth, users, clients, projects, dashboard, expenses, leaves, attendance, tasks, timesheets, uploads, reimbursements, weekly_timesheets, bank_accounts, invoices, teams, settings as settings_router


security = HTTPBearer()
app = FastAPI(title="Studio MH02")

# CORS – allow the Vite dev server to reach the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(weekly_timesheets.router)
app.include_router(bank_accounts.router)
app.include_router(invoices.router)
app.include_router(teams.router)
app.include_router(settings_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def run_migrations():
    """Add any missing columns to existing tables.

    Each ALTER runs in its own transaction so a failure on one (e.g. column
    already exists in Postgres) doesn't abort the rest. Works on both Postgres
    and SQLite.
    """
    from app.database import engine
    from sqlalchemy import text

    # Columns to ensure exist on the projects table: (column_name, sql_definition)
    project_columns = [
        ("partner_remuneration", "NUMERIC(10, 2) DEFAULT 0"),
        ("employee_remuneration", "NUMERIC(10, 2) DEFAULT 0"),
        ("project_remuneration", "NUMERIC(10, 2) DEFAULT 0"),
        ("total_assigned_hours", "NUMERIC(10, 2) DEFAULT 0"),
        ("partner_hourly_rate", "NUMERIC(10, 2) DEFAULT 0"),
        ("billed_amount", "NUMERIC(12, 2) DEFAULT 0"),
        ("color", "VARCHAR DEFAULT '#287475'"),
        ("work_order_urls", "VARCHAR"),
        ("advance_amount", "NUMERIC(12, 2) DEFAULT 0"),
    ]

    for col_name, col_def in project_columns:
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text(f"ALTER TABLE projects ADD COLUMN {col_name} {col_def}")
                )
        except Exception:
            pass  # Column already exists in this DB — skip and continue

    # Create the settings table (singleton) if missing — covers both Postgres and SQLite.
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    company_name VARCHAR,
                    company_address VARCHAR,
                    company_gstin VARCHAR,
                    company_phone VARCHAR,
                    company_email VARCHAR,
                    company_signatory_name VARCHAR,
                    company_signatory_role VARCHAR,
                    working_hours_per_month NUMERIC(6, 2),
                    salary_months_per_year NUMERIC(4, 2)
                )
            """))
    except Exception:
        pass

