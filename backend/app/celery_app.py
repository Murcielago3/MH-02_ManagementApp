from celery import Celery
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

# Auto-discover tasks in app modules if any are added later.
celery_app.autodiscover_tasks(["app"])
