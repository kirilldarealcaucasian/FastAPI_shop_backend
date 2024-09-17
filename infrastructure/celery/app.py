from celery import Celery
from celery.exceptions import CeleryError
from celery.schedules import crontab
from core.config import settings
from dataclasses import dataclass, field

from logger import logger


@dataclass
class CeleryClient:
    app_name: str
    broker_connection_str: str
    broker_connection_retry_on_startup: field(init=False, default=True)
    tasks_include_path: field(default_factory=list)

    def get_celery_client(self) -> Celery:
        try:
            return Celery(
                self.app_name,
                broker=self.broker_connection_str,
                include=[path for path in self.tasks_include_path],
                broker_connection_retry_on_startup=self.broker_connection_retry_on_startup
            )
        except CeleryError:
            extra = {
                "broker": self.broker_connection_str
            }
            logger.error(
                "failed to create connection to celery",
                exc_info=True,
                extra=extra
            )

# how to start celery: celery -A infrastructure.celery.app:celery worker -l DEBUG --pool=solo


client = CeleryClient(
    app_name="tasks1",
    broker_connection_str=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    tasks_include_path=["application.tasks.tasks1"],
    broker_connection_retry_on_startup=True
)
celery: Celery = client.get_celery_client()


celery.conf.beat_schedule = {  # tasks that are run recurrently
    "save-logs-every-minute": {
        "task": "application.tasks.tasks1.save_log",
        "schedule": crontab(minute="*/1"),  # run every minute
        "args": (),
    },
    "remove-expired-carts-every-ten-minutes": {
        "task": "application.tasks.tasks1.remove_expired_carts",
        # "schedule": crontab(minute="*/10"),  # run every 10 minutes,
        "schedule": crontab(minute="*/1"),  # run every 10 minutes,
        "args": (),
    }
}


celery.conf.event_serializer = 'pickle'
celery.conf.task_serializer = 'pickle'
celery.conf.result_serializer = 'pickle'
celery.conf.accept_content = ['application/json', 'application/x-python-serialize']
