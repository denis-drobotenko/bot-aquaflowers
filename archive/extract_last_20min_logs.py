import re
from datetime import datetime, timedelta

USER_ID = '79084634603'
LOG_FILE = 'logs.log'
OUT_FILE = 'petr_logs_last_20min.txt'

now = datetime.utcnow()
with open(LOG_FILE, encoding='utf-8') as f, open(OUT_FILE, 'w', encoding='utf-8') as out:
    for line in f:
        if USER_ID not in line:
            continue
        m = re.search(r'\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
        if not m:
            continue
        log_time = datetime.strptime(m.group(1), '%Y-%m-%dT%H:%M:%S')
        if (now - log_time).total_seconds() <= 1200:
            out.write(line) 