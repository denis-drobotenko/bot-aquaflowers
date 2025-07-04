import argparse
from datetime import datetime, timedelta
from google.cloud import logging

def filter_useful_logs(logs_data):
    useful_logs = []
    useful_keywords = [
        'webhook', 'message', 'ai', 'session', 'user', 'bot', 'response',
        'dialog', 'conversation', 'whatsapp', 'send', 'receive',
        'catalog', 'order', 'product', 'flower', 'bouquet',
        'error', 'exception', 'warning'
    ]
    exclude_keywords = [
        'shutting down', 'startup', 'application startup',
        'uvicorn', 'fastapi', 'middleware', 'cors',
        'health check', 'root endpoint', 'static files'
    ]
    for log in logs_data:
        text = log.get('textPayload', '').lower()
        if any(exclude in text for exclude in exclude_keywords):
            continue
        if any(keyword in text for keyword in useful_keywords):
            useful_logs.append(log)
    return useful_logs

def download_logs_api(period_min=20, output_file='logs.log'):
    try:
        print(f"Connecting to Google Cloud Logging API for last {period_min} minutes...")
        client = logging.Client()
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=period_min)
        filter_str = f'''
        resource.type="cloud_run_revision"
        resource.labels.service_name="auraflora-bot"
        timestamp >= "{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        timestamp < "{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        '''
        print(f"Getting logs from {start_time} to {end_time}...")
        entries = client.list_entries(
            filter_=filter_str,
            page_size=5000,
            max_results=5000
        )
        logs_data = []
        for entry in entries:
            log_entry = {
                'timestamp': entry.timestamp.isoformat() if entry.timestamp else '',
                'textPayload': str(entry.payload) if entry.payload else '',
            }
            logs_data.append(log_entry)
        print(f"Total raw logs: {len(logs_data)}")
        useful_logs = filter_useful_logs(logs_data)
        print(f"Filtered useful logs: {len(useful_logs)}")
        with open(output_file, 'w', encoding='utf-8') as f:
            for log in useful_logs:
                timestamp = log.get('timestamp', '')
                text = log.get('textPayload', '')
                f.write(f"[{timestamp}] {text}\n")
        print(f"Saved {len(useful_logs)} logs to {output_file}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download logs from Google Cloud Logging API and save to logs.log")
    parser.add_argument('--minutes', type=int, default=20, help='Period in minutes to fetch logs for (default: 20)')
    parser.add_argument('--output', type=str, default='logs.log', help='Output file (default: logs.log)')
    args = parser.parse_args()
    download_logs_api(args.minutes, args.output) 