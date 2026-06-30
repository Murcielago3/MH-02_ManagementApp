from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.routers import auth, users, clients, projects, dashboard, expenses, leaves, attendance, tasks, timesheets, uploads, reimbursements, weekly_timesheets, bank_accounts, invoices, teams, settings as settings_router, estimates, salary_slips, holidays, subtasks, salary as salary_router


security = HTTPBearer()
app = FastAPI(title="Studio MH02")

# CORS – allow the Vite dev server to reach the API.
# allow_credentials=True is incompatible with allow_origins=["*"] (browsers
# reject the wildcard when credentials are signalled). The app authenticates
# via bearer tokens in the Authorization header, not cookies, so credentials
# can stay off. allow_origin_regex matches any LAN/loopback origin so it
# works from every PC on the network without listing each one.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
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
app.include_router(estimates.router)
app.include_router(salary_slips.router)
app.include_router(holidays.router)
app.include_router(subtasks.router)
app.include_router(subtasks.single_router)
app.include_router(salary_router.router)


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

    # Create estimates tables if missing
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS estimates (
                    id SERIAL PRIMARY KEY,
                    project_name VARCHAR NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    working_days INTEGER DEFAULT 0,
                    partner_pay_per_hour NUMERIC(10, 2) DEFAULT 0,
                    partner_cost NUMERIC(12, 2) DEFAULT 0,
                    team_cost NUMERIC(12, 2) DEFAULT 0,
                    grand_total NUMERIC(12, 2) DEFAULT 0,
                    project_color VARCHAR DEFAULT '#287475',
                    status VARCHAR DEFAULT 'draft',
                    created_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS estimate_employees (
                    id SERIAL PRIMARY KEY,
                    estimate_id INTEGER REFERENCES estimates(id) ON DELETE CASCADE,
                    emp_type VARCHAR NOT NULL,
                    base_pay NUMERIC(10, 2) NOT NULL,
                    hrs_per_day NUMERIC(4, 1) DEFAULT 8,
                    pay_per_hour NUMERIC(10, 2) DEFAULT 0,
                    total_hours NUMERIC(10, 2) DEFAULT 0,
                    total_cost NUMERIC(12, 2) DEFAULT 0
                )
            """))
    except Exception:
        pass

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

    # Add the TDS column to settings if missing
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE settings ADD COLUMN tds_percent NUMERIC(5, 2)"))
    except Exception:
        pass

    # Add salary-slip-related employee columns if missing
    user_columns = [
        ("gender", "VARCHAR"),
        ("location", "VARCHAR"),
        ("bank_name", "VARCHAR"),
        ("bank_account_number", "VARCHAR"),
        ("paid_leave_balance", "NUMERIC(6, 1) DEFAULT 0"),
        ("leave_accrued_through", "VARCHAR"),
    ]
    for col_name, col_def in user_columns:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
        except Exception:
            pass

    # Leave request paid/unpaid split columns
    for col_name, col_def in [("paid_days", "INTEGER DEFAULT 0"), ("unpaid_days", "INTEGER DEFAULT 0")]:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(f"ALTER TABLE leave_requests ADD COLUMN {col_name} {col_def}"))
        except Exception:
            pass

    # Salary slip leave-deduction columns
    for col_name, col_def in [
        ("paid_leave_days", "NUMERIC(5, 1) DEFAULT 0"),
        ("unpaid_leave_days", "NUMERIC(5, 1) DEFAULT 0"),
        ("leave_deduction", "NUMERIC(12, 2) DEFAULT 0"),
    ]:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(f"ALTER TABLE salary_slips ADD COLUMN {col_name} {col_def}"))
        except Exception:
            pass

    # Per-day hours breakdown on timesheet entries (Mon..Sun JSON array)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE weekly_timesheet_entries ADD COLUMN daily_hours JSON"))
    except Exception:
        pass

    # Company-wide holidays table
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS holidays (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL UNIQUE,
                    name VARCHAR NOT NULL
                )
            """))
    except Exception:
        pass

    # Per-task subtasks
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS subtasks (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                    title VARCHAR NOT NULL,
                    description VARCHAR,
                    duration_hours NUMERIC(6, 2),
                    status VARCHAR DEFAULT 'pending',
                    created_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
    except Exception:
        pass

    # Effective-dated salary history (point-in-time pay). SERIAL on Postgres,
    # but CREATE TABLE IF NOT EXISTS is portable enough for our two backends.
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS salary_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    monthly_salary NUMERIC(10, 2),
                    salary_hour NUMERIC(8, 2),
                    smpy NUMERIC(4, 2),
                    whpm NUMERIC(6, 2),
                    hourly_rate NUMERIC(10, 2),
                    effective_from DATE NOT NULL,
                    effective_to DATE,
                    note VARCHAR,
                    created_at TIMESTAMP DEFAULT NOW(),
                    CONSTRAINT uq_salary_user_effrom UNIQUE (user_id, effective_from)
                )
            """))
    except Exception:
        pass

    # Frozen employee cost + per-rate-period breakdown on timesheet entries.
    for col_name, col_def in [
        ("employee_cost", "NUMERIC(12, 2)"),
        ("cost_breakdown", "JSON"),
    ]:
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text(f"ALTER TABLE weekly_timesheet_entries ADD COLUMN {col_name} {col_def}")
                )
        except Exception:
            pass

    # Create the salary_slips table if missing
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS salary_slips (
                    id SERIAL PRIMARY KEY,
                    employee_id INTEGER NOT NULL REFERENCES users(id),
                    month VARCHAR NOT NULL,
                    base_salary NUMERIC(12, 2) DEFAULT 0,
                    tds_percent NUMERIC(5, 2) DEFAULT 0,
                    tds_amount NUMERIC(12, 2) DEFAULT 0,
                    reimbursement_total NUMERIC(12, 2) DEFAULT 0,
                    net_total NUMERIC(12, 2) DEFAULT 0,
                    payout_date DATE,
                    status VARCHAR DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW(),
                    approved_at TIMESTAMP,
                    CONSTRAINT uq_salary_slip_employee_month UNIQUE (employee_id, month)
                )
            """))
    except Exception:
        pass

