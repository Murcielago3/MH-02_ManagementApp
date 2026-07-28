"""Read-only diagnosis of why approved-timesheet numbers stopped moving.

Everything downstream (project cost/hours, reserve balance, dashboard, salary
costing) keys off `weekly_timesheets.status = 'approved'`. Since the two-stage
approval landed, that status is *derived* from the approval slots:

    admin's own timesheet  -> admin slot
    everyone else's        -> PM slot + admin slot + second-admin slot

so a timesheet stalls forever if the org can't fill one of those slots. This
script reports where things are stuck. It writes nothing.

Run:  docker compose exec api python diagnose_timesheets.py
"""
import asyncio
from datetime import date

from sqlalchemy import text

from app.database import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 72)
        print("ROSTER — who can fill each approval slot")
        print("=" * 72)
        rows = (await db.execute(text(
            "SELECT role, COUNT(*) AS n,"
            "       COUNT(*) FILTER (WHERE end_date IS NULL OR end_date >= CURRENT_DATE) AS active"
            "  FROM users GROUP BY role ORDER BY role"
        ))).all()
        roles = {r.role: (r.n, r.active) for r in rows}
        for role, (n, active) in roles.items():
            print(f"  {role:<18} {n:>3} total, {active:>3} active")

        admins = roles.get("admin", (0, 0))[1]
        pms = roles.get("project_manager", (0, 0))[1]
        print()
        if pms == 0:
            print("  !! No active project_manager. The PM slot on every non-admin")
            print("     timesheet can NEVER be filled — admins cannot fill it.")
        if admins < 2:
            print("  !! Fewer than 2 active admins. The second-admin slot can NEVER")
            print("     be filled — the same admin is refused both admin slots.")
        if pms > 0 and admins >= 2:
            print("  Roster can satisfy all three slots.")

        print()
        print("=" * 72)
        print("TIMESHEETS BY STATUS")
        print("=" * 72)
        rows = (await db.execute(text(
            "SELECT status, COUNT(*) AS n, MIN(week_start) AS oldest, MAX(week_start) AS newest"
            "  FROM weekly_timesheets GROUP BY status ORDER BY status"
        ))).all()
        for r in rows:
            print(f"  {r.status:<16} {r.n:>4}   weeks {r.oldest} .. {r.newest}")

        print()
        print("=" * 72)
        print("LAST FULL APPROVAL — when the numbers last moved")
        print("=" * 72)
        r = (await db.execute(text(
            "SELECT MAX(GREATEST("
            "  COALESCE(pm_approved_at,    '-infinity'::timestamptz),"
            "  COALESCE(admin_approved_at, '-infinity'::timestamptz),"
            "  COALESCE(admin2_approved_at,'-infinity'::timestamptz))) AS last_at,"
            "  MAX(week_start) AS last_week"
            "  FROM weekly_timesheets WHERE status = 'approved'"
        ))).first()
        print(f"  most recent approval action : {r.last_at}")
        print(f"  latest fully-approved week  : {r.last_week}")
        if r.last_week:
            print(f"  ({(date.today() - r.last_week).days} days ago)")

        print()
        print("=" * 72)
        print("STUCK TIMESHEETS — submitted but never fully approved")
        print("=" * 72)
        rows = (await db.execute(text(
            "SELECT wt.id, u.name, u.role, wt.week_start, wt.status, wt.total_hours,"
            "       (wt.pm_approved_at     IS NOT NULL) AS pm,"
            "       (wt.admin_approved_at  IS NOT NULL) AS a1,"
            "       (wt.admin2_approved_at IS NOT NULL) AS a2"
            "  FROM weekly_timesheets wt JOIN users u ON u.id = wt.employee_id"
            " WHERE wt.status NOT IN ('approved', 'rejected')"
            " ORDER BY wt.week_start"
        ))).all()
        if not rows:
            print("  none")
        stuck_hours = 0.0
        for r in rows:
            missing = []
            if r.role != "admin":
                if not r.pm:
                    missing.append("PM")
                if not r.a2:
                    missing.append("admin#2")
            if not r.a1:
                missing.append("admin#1")
            stuck_hours += float(r.total_hours or 0)
            print(f"  #{r.id:<5} {r.name[:22]:<22} {r.week_start}  {r.status:<15}"
                  f" {float(r.total_hours or 0):>6.1f}h   missing: {', '.join(missing) or '-'}")
        print(f"\n  {len(rows)} stuck timesheets, {stuck_hours:.1f} hours not counted anywhere.")

        print()
        print("=" * 72)
        print("HOURS MISSING FROM EACH PROJECT")
        print("=" * 72)
        rows = (await db.execute(text(
            "SELECT p.project_number, p.name,"
            "       COALESCE(SUM(wte.hours) FILTER (WHERE wt.status = 'approved'), 0) AS counted,"
            "       COALESCE(SUM(wte.hours) FILTER (WHERE wt.status NOT IN ('approved','rejected')), 0) AS stuck"
            "  FROM projects p"
            "  JOIN weekly_timesheet_entries wte ON wte.project_id = p.id"
            "  JOIN weekly_timesheets wt ON wt.id = wte.timesheet_id"
            " GROUP BY p.id, p.project_number, p.name"
            " HAVING COALESCE(SUM(wte.hours) FILTER (WHERE wt.status NOT IN ('approved','rejected')), 0) > 0"
            " ORDER BY stuck DESC"
        ))).all()
        if not rows:
            print("  none")
        for r in rows:
            print(f"  {str(r.project_number)[:12]:<12} {r.name[:34]:<34}"
                  f" counted {float(r.counted):>7.1f}h   MISSING {float(r.stuck):>7.1f}h")

        print()
        print("=" * 72)
        print("APPROVED BUT UNCOSTED — entries whose employee_cost never froze")
        print("=" * 72)
        rows = (await db.execute(text(
            "SELECT u.name, COUNT(*) AS n, COALESCE(SUM(wte.hours), 0) AS hrs"
            "  FROM weekly_timesheet_entries wte"
            "  JOIN weekly_timesheets wt ON wt.id = wte.timesheet_id"
            "  JOIN users u ON u.id = wt.employee_id"
            " WHERE wt.status = 'approved' AND (wte.employee_cost IS NULL OR wte.employee_cost = 0)"
            "   AND wte.hours > 0"
            " GROUP BY u.name ORDER BY hrs DESC"
        ))).all()
        if not rows:
            print("  none — every approved entry carries a frozen cost")
        for r in rows:
            print(f"  {r.name[:28]:<28} {r.n:>4} entries  {float(r.hrs):>7.1f}h costed at 0")
            print("       (no salary_history covering those weeks)")


if __name__ == "__main__":
    asyncio.run(main())
