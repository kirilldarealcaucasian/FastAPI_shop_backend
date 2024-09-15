from celery import Celery
from celery.schedules import crontab
# from core.config import settings


# Convert the relative path to an absolute import path

celery = Celery(
    "tasks1",
    # broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    broker="redis://127.0.0.1:6379",
    include=["application.tasks.tasks1"],
    broker_connection_retry_on_startup=True,
)

# celery -A infrastructure.celery.app:celery worker -l DEBUG --pool=solo


celery.conf.beat_schedule = {
    # 'save-logs-every-minute': {
    #     'task': 'application.tasks.tasks1.save_log',
    #     'schedule': crontab(minute='*/1'),  # run every minute
    #     'args': (),
    # },
    "remove-expired-carts-every-ten-minutes": {
        "task": "application.tasks.tasks1.remove_expired_carts",
        "schedule": crontab(minute='*/10'),  # run every minute,
        "args": (),
    }
}

celery.conf.event_serializer = 'pickle'
celery.conf.task_serializer = 'pickle'
celery.conf.result_serializer = 'pickle'
celery.conf.accept_content = ['application/json', 'application/x-python-serialize']

