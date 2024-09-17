import json
from time import strptime, mktime
from core.config import settings


def parse_logs_journal() -> bytes:
    # extracts logs from the journal and converts into bytes

    with open(settings.LOGS_JOURNAL_NAME, "r") as f:
        logs = []
        for line in f:
            line.rstrip()
            res = json.loads(line)  # convert to dict
            # convert from string representation of time to unix time
            time_struct = strptime(res.pop("timestamp"), "%Y-%m-%dT%H:%M:%S.%fZ")
            unix_time = int(mktime(time_struct))
            res["unix_time"] = unix_time
            logs.append(res)
        if not logs:
            return b''
        json_data = json.dumps(logs)
        encoded_json = json_data.encode("utf-8")
    return encoded_json
