from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Create Celery instance
celery_app = Celery(
    "github_repo_evaluator",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["app.tasks.scan_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "app.tasks.scan_tasks.scan_user_repositories": {"queue": "scan_queue"},
        "app.tasks.scan_tasks.scan_single_repository": {"queue": "scan_queue"},
        "app.tasks.scan_tasks.analyze_repository_content": {"queue": "analysis_queue"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    result_expires=3600,  # 1 hour
)

# Optional: Configure periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-expired-scans": {
        "task": "app.tasks.scan_tasks.cleanup_expired_scans",
        "schedule": 3600.0,  # Run every hour
    },
}

if __name__ == "__main__":
    celery_app.start()