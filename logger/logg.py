import logging
import os
from datetime import datetime
from pythonjsonlogger import jsonlogger
from dotenv import load_dotenv
from core.config import settings

load_dotenv()


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


class CustomConsoleFormatter(logging.Formatter):
    def format(self, record):
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        level = record.levelname
        message = record.getMessage()
        path = record.pathname
        exc_text = record.exc_text
        exc_info = record.exc_info
        line = record.lineno

        extras = ", ".join(
            f"{k}={v}"
            for k, v in record.__dict__.items()
            if k
            not in [
                "args",
                "levelname",
                "levelno",
                "lineno",
                "pathname",
                "module",
                "msg",
                "name",
                "filename"
                "process",
                "processName",
                "thread",
                "threadName",
                "stack_info",
                "func_name",
                "created",
                "msecs",
                "relativeCreated",
                "funcName",
            ]
        )

        blue_text = "\033[94m"
        reset_color = "\033[0m"

        return f"""{blue_text}{timestamp} [{level}] {path}[line:{line}]: {message} {reset_color} {exc_text if exc_text else ''} {exc_info if exc_info else ''} {'extra: ' + extras if extras else ''}"""  # noqa


LOG_LEVEL = settings.LOG_LEVEL
LOGS_JOURNAL_PATH = settings.LOGS_JOURNAL_NAME

logs_file_formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(pathname)s: %(message)s')
console_formatter = CustomJsonFormatter('\033[94m %(level)s %(pathname)s: %(message)s \033[0m')


# init default logger
logger = logging.getLogger(__file__)

# define format for logs in the logs journal and where to write logs
file_handler = logging.FileHandler(
    filename=os.path.normpath(LOGS_JOURNAL_PATH),
    mode="a"
)

file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(logs_file_formatter)

# define format for logs in the console and where to stream logs
logHandler = logging.StreamHandler()
logHandler.setFormatter(console_formatter)
logger.setLevel(LOG_LEVEL)


logger.addHandler(file_handler)
logger.addHandler(logHandler)
