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


LOG_LEVEL = settings.LOG_LEVEL
LOGS_JOURNAL_PATH = settings.LOGS_JOURNAL_NAME

logs_file_formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(pathname)s: %(message)s')
console_formatter = CustomJsonFormatter('%(level)s %(pathname)s: %(message)s')

# init default logger
logger = logging.getLogger()

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
