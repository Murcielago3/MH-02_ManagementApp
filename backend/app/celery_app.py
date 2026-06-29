from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.task_default_queue = "default"
celery_app.conf.task_routes = {}
celery_app.conf.accept_content = ["json"]
celery_app.conf.result_serializer = "json"
celery_app.conf.task_serializer = "json"

# Run scheduled reminders in the studio's local time, not UTC.
celery_app.conf.timezone = settings.TIMEZONE
celery_app.conf.enable_utc = False

# Make the task module importable by the worker and beat.
celery_app.conf.imports = ("app.tasks",)

# ─── Scheduled reminders (Celery Beat) ───
# Requires the `beat` service to be running (see docker-compose*.yml). Run
# exactly one beat instance, or messages get sent multiple times.
celery_app.conf.beat_schedule = {
    # Monthly report to the management channel — 1st of each month at 09:00.
    "monthly-admin-report": {
        "task": "app.tasks.monthly_admin_report",
        "schedule": crontab(day_of_month="1", hour=9, minute=0),
    },
    # Timesheet nudge to the common channel — every Sunday at 12:00 noon.
    "weekly-timesheet-reminder": {
        "task": "app.tasks.weekly_timesheet_reminder",
        "schedule": crontab(day_of_week="sun", hour=12, minute=0),
    },
    # Daily task briefing to the common channel — every weekday at 09:00.
    "daily-task-reminder": {
        "task": "app.tasks.daily_task_reminder",
        "schedule": crontab(day_of_week="mon-sat", hour=9, minute=0),
    },
}

# Auto-discover tasks in app modules.
celery_app.autodiscover_tasks(["app"])
