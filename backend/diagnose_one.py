"""Read-only before/after for ONE employee on ONE project across the two
approval pushes.

    5747a57  2026-07-03 23:09 IST  status became derived: PM + admin required
    40e40db  2026-07-10 10:18 IST  second admin added: PM + admin + admin2

Writes nothing. Override the targets with argv:
    python diagnose_one.py "Harsh Dhanraj Rode" "ADANI MOTILAL NAGAR"
"""
import asyncio
import sys
from datetime import datetime

from sqlalchemy import text

from app.database import AsyncSessionLocal

EMPLOYEE = sys.argv[1] if len(sys.argv) > 1 else "Harsh Dhanraj Rode"
PROJECT = sys.argv[2] if len(sys.argv) > 2 else "ADANI MOTILAL NAGAR"

# The approval columns are plain TIMESTAMP (no tz) — the startup ALTER in
# main.py used "TIMESTAMP", so compare against naive UTC, not IST-aware values.
PUSH_2STAGE = datetime.fromisoformat("2026-07-03 17:39:20")   # 23:09:20 IST
PUSH_3STAGE = datetime.fromisoformat("2026-07-10 04:48:34")   # 10:18:34 IST


async def main():
    async with AsyncSessionLocal() as db:
        emp = (await db.execute(text(
            "SELECT id, name, role FROM users WHERE name ILIKE :n ORDER BY id LIMIT 1"
        ), {"n": f"%{EMPLOYEE}%"})).first()
        proj = (await db.execute(text(
            "SELECT id, project_number, name FROM projects WHERE name ILIKE :n ORDER BY id LIMIT 1"
        ), {"n": f"%{PROJECT}%"})).first()

        if not emp:
            print(f"No user matching {EMPLOYEE!r}")
            return
        if not proj:
            print(f"No project matching {PROJECT!r}")
            return

        print(f"employee : #{emp.id} {emp.name} ({emp.role})")
        print(f"project  : #{proj.id} {proj.project_number} — {proj.name}")
        print()

        # ── When the Jul 3 migration actually ran on this server ──
        # It stamped every then-approved row with a single NOW(). Rows sharing
        # that timestamp were approved BEFORE the gate existed.
        print("=" * 78)
        print("WHEN THE JUL 3 CHANGE ACTUALLY HIT THIS SERVER")
        print("=" * 78)
        rows = (await db.execute(text(
            "SELECT pm_approved_at AS ts, COUNT(*) AS n FROM weekly_timesheets"
            " WHERE pm_approved_at IS NOT NULL"
            " GROUP BY pm_approved_at ORDER BY n DESC LIMIT 3"
        ))).all()
        for r in rows:
            print(f"  {r.ts}   {r.n} timesheets share this exact timestamp")
        print("  (the row with many sheets sharing one timestamp = the migration run;")
        print("   those were all approved under the OLD single-step rule)")

        # ── Every week this employee logged to this project ──
        print()
        print("=" * 78)
        print(f"EVERY WEEK {emp.name} LOGGED TO THIS PROJECT")
        print("=" * 78)
        print(f"  {'week':<12} {'hrs':>6} {'status':<15} {'PM':<3} {'A1':<3} {'A2':<3}  counts?")
        rows = (await db.execute(text(
            "SELECT wt.id, wt.week_start, wt.status, wte.hours, wte.employee_cost,"
            "       (wt.pm_approved_at IS NOT NULL) AS pm,"
            "       (wt.admin_approved_at IS NOT NULL) AS a1,"
            "       (wt.admin2_approved_at IS NOT NULL) AS a2"
            "  FROM weekly_timesheet_entries wte"
            "  JOIN weekly_timesheets wt ON wt.id = wte.timesheet_id"
            " WHERE wt.employee_id = :e AND wte.project_id = :p"
            " ORDER BY wt.week_start"
        ), {"e": emp.id, "p": proj.id})).all()

        counted_h = counted_c = lost_h = 0.0
        for r in rows:
            ok = r.status == "approved"
            h = float(r.hours or 0)
            if ok:
                counted_h += h
                counted_c += float(r.employee_cost or 0)
            elif r.status != "rejected":
                lost_h += h
            mark = "yes" if ok else ("REJECTED" if r.status == "rejected" else "NO — invisible")
            print(f"  {str(r.week_start):<12} {h:>6.1f} {r.status:<15}"
                  f" {'Y' if r.pm else '·':<3} {'Y' if r.a1 else '·':<3} {'Y' if r.a2 else '·':<3}  {mark}")

        print()
        print(f"  counting now : {counted_h:>8.1f} h   cost {counted_c:>12,.2f}")
        print(f"  NOT counting : {lost_h:>8.1f} h")

        # ── Project-wide, all employees ──
        print()
        print("=" * 78)
        print("WHOLE PROJECT — what the page shows vs what was actually worked")
        print("=" * 78)
        rows = (await db.execute(text(
            "SELECT u.name,"
            "  COALESCE(SUM(wte.hours) FILTER (WHERE wt.status='approved'),0) AS shown_h,"
            "  COALESCE(SUM(wte.employee_cost) FILTER (WHERE wt.status='approved'),0) AS shown_c,"
            "  COALESCE(SUM(wte.hours) FILTER (WHERE wt.status NOT IN ('approved','rejected')),0) AS lost_h"
            "  FROM weekly_timesheet_entries wte"
            "  JOIN weekly_timesheets wt ON wt.id = wte.timesheet_id"
            "  JOIN users u ON u.id = wt.employee_id"
            " WHERE wte.project_id = :p"
            " GROUP BY u.name ORDER BY lost_h DESC, shown_h DESC"
        ), {"p": proj.id})).all()
        ts_h = ts_c = tl_h = 0.0
        for r in rows:
            ts_h += float(r.shown_h); ts_c += float(r.shown_c); tl_h += float(r.lost_h)
            print(f"  {r.name[:26]:<26} shown {float(r.shown_h):>7.1f}h"
                  f"  cost {float(r.shown_c):>11,.2f}   missing {float(r.lost_h):>7.1f}h")
        print(f"  {'TOTAL':<26} shown {ts_h:>7.1f}h  cost {ts_c:>11,.2f}   missing {tl_h:>7.1f}h")

        # ── The project number as it stood before each push ──
        # A sheet counted at time T if it was approved and its approval predates T.
        print()
        print("=" * 78)
        print("PROJECT HOURS AS THEY STOOD AT EACH PUSH")
        print("=" * 78)
        for label, cutoff in (("before Jul 3 23:09 push", PUSH_2STAGE),
                              ("before Jul 10 10:18 push", PUSH_3STAGE),
                              ("today", None)):
            if cutoff:
                q = ("SELECT COALESCE(SUM(wte.hours),0) AS h, COALESCE(SUM(wte.employee_cost),0) AS c"
                     "  FROM weekly_timesheet_entries wte"
                     "  JOIN weekly_timesheets wt ON wt.id = wte.timesheet_id"
                     " WHERE wte.project_id = :p AND wt.status='approved'"
                     "   AND COALESCE(wt.admin_approved_at, wt.pm_approved_at) < :t")
                r = (await db.execute(text(q), {"p": proj.id, "t": cutoff})).first()
            else:
                q = ("SELECT COALESCE(SUM(wte.hours),0) AS h, COALESCE(SUM(wte.employee_cost),0) AS c"
                     "  FROM weekly_timesheet_entries wte"
                     "  JOIN weekly_timesheets wt ON wt.id = wte.timesheet_id"
                     " WHERE wte.project_id = :p AND wt.status='approved'")
                r = (await db.execute(text(q), {"p": proj.id})).first()
            print(f"  {label:<26} {float(r.h):>8.1f} h   cost {float(r.c):>12,.2f}")
        print()
        print("  NOTE: rows approved before Jul 3 carry the migration's timestamp,")
        print("  not their true approval time — so the first line is a floor, not exact.")


if __name__ == "__main__":
    asyncio.run(main())
