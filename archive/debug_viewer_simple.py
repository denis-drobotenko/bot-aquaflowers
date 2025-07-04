import logging
import json
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import sys
import os

# Добавляем src в путь
sys.path.insert(0, 'src')

app = FastAPI()

# Хранилище логов
logs_storage = []

class DebugHandler(logging.Handler):
    def emit(self, record):
        try:
            log_data = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'logger': record.name,
                'level': record.levelname,
                'message': record.getMessage(),
                'session_id': self.get_session_id(record.getMessage())
            }
            logs_storage.append(log_data)
            
            if len(logs_storage) > 500:
                logs_storage.pop(0)
        except:
            pass
    
    def get_session_id(self, message):
        import re
        patterns = [r'Session: ([^\s,]+)', r'session_id[=:\s]+([^\s,]+)']
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        return None

def setup_logging():
    handler = DebugHandler()
    for logger_name in ['ai_pipeline', 'json_processor', 'command_handler', 'whatsapp_utils', 'webhook_flow']:
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)

@app.get("/")
async def main_page():
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AuraFlora Debug</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .header { background: #4CAF50; color: white; padding: 20px; text-align: center; }
        .container { display: grid; grid-template-columns: 300px 1fr; gap: 20px; margin-top: 20px; }
        .panel { background: white; padding: 20px; border-radius: 8px; }
        .session { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; }
        .session:hover { background: #f0f0f0; }
        .session.active { background: #e3f2fd; }
        .message { margin: 15px 0; padding: 15px; border-radius: 8px; }
        .message.user { background: #e3f2fd; }
        .message.assistant { background: #f3e5f5; }
        .debug-btn { background: #2196F3; color: white; border: none; padding: 5px 10px; margin-top: 10px; cursor: pointer; }
        .logs { background: #f9f9f9; padding: 10px; margin-top: 10px; font-family: monospace; font-size: 12px; max-height: 200px; overflow-y: auto; }
        .log { margin: 5px 0; padding: 5px; background: white; border-left: 3px solid #ddd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AuraFlora Debug Interface</h1>
    </div>
    
    <div class="container">
        <div class="panel">
            <h3>Сессии</h3>
            <button onclick="loadSessions()">Обновить</button>
            <div id="sessions"></div>
        </div>
        
        <div class="panel">
            <h3>Диалог</h3>
            <div id="dialog">Выберите сессию</div>
        </div>
    </div>

    <script>
        async function loadSessions() {
            const response = await fetch('/api/sessions');
            const sessions = await response.json();
            
            document.getElementById('sessions').innerHTML = sessions.map(s => 
                `<div class="session" onclick="loadDialog('${s.session_id}')">
                    ${s.sender_id}<br>
                    <small>${s.message_count} сообщений</small>
                </div>`
            ).join('');
        }
        
        async function loadDialog(sessionId) {
            document.querySelectorAll('.session').forEach(s => s.classList.remove('active'));
            event.target.classList.add('active');
            
            const response = await fetch(`/api/messages/${sessionId}`);
            const data = await response.json();
            
            document.getElementById('dialog').innerHTML = data.messages.map((msg, i) => {
                const logs = data.logs.filter(log => 
                    Math.abs(new Date(log.timestamp) - new Date(msg.timestamp)) < 30000
                );
                
                return `<div class="message ${msg.role}">
                    <strong>${msg.role === 'user' ? 'Пользователь' : 'AuraFlora'}</strong>
                    <div>${msg.content}</div>
                    ${logs.length > 0 ? `
                        <button class="debug-btn" onclick="toggleLogs(${i})">Логи (${logs.length})</button>
                        <div class="logs" id="logs-${i}" style="display:none">
                            ${logs.map(log => `<div class="log">[${log.level}] ${log.logger}: ${log.message}</div>`).join('')}
                        </div>
                    ` : ''}
                </div>`;
            }).join('');
        }
        
        function toggleLogs(index) {
            const logs = document.getElementById(`logs-${index}`);
            logs.style.display = logs.style.display === 'none' ? 'block' : 'none';
        }
        
        loadSessions();
    </script>
</body>
</html>
    """
    return HTMLResponse(html)

@app.get("/api/sessions")
async def get_sessions():
    try:
        from src import database
        
        session_ids = set()
        for log in logs_storage:
            if log.get('session_id'):
                session_ids.add(log['session_id'])
        
        sessions = []
        for sid in session_ids:
            try:
                history = database.get_conversation_history(sid, limit=50)
                if history:
                    sessions.append({
                        'session_id': sid,
                        'sender_id': sid.split('_')[0],
                        'message_count': len(history),
                        'last_time': max(h.get('timestamp', datetime.min) for h in history).isoformat()
                    })
            except:
                pass
        
        return sessions
    except:
        return []

@app.get("/api/messages/{session_id}")
async def get_messages(session_id: str):
    try:
        from src import database
        
        history = database.get_conversation_history(session_id, limit=100)
        messages = []
        
        for msg in history:
            messages.append({
                'role': msg.get('role', 'unknown'),
                'content': msg.get('content', ''),
                'timestamp': msg.get('timestamp', datetime.now()).isoformat()
            })
        
        session_logs = [log for log in logs_storage if log.get('session_id') == session_id]
        
        return {'messages': messages, 'logs': session_logs}
    except:
        return {'messages': [], 'logs': []}

if __name__ == "__main__":
    import uvicorn
    setup_logging()
    print("Debug viewer: http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001) 