"""
Debug интерфейс для просмотра диалогов AuraFlora
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import sys
import os

# Добавляем src в путь
sys.path.append('src')

try:
    from src import database
    from src.config import Config
except ImportError:
    # Fallback если не можем импортировать
    database = None
    Config = None

app = FastAPI(title="AuraFlora Debug Viewer")

# Хранилище логов в памяти
debug_logs = []

class DebugLogHandler(logging.Handler):
    """Собирает логи для отладки"""
    
    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'logger_name': record.name,
                'level': record.levelname,
                'message': record.getMessage(),
                'session_id': self._extract_session_id(record.getMessage())
            }
            debug_logs.append(log_entry)
            
            # Ограничиваем размер до 1000 записей
            if len(debug_logs) > 1000:
                debug_logs.pop(0)
                
        except Exception:
            pass  # Игнорируем ошибки в логгере
    
    def _extract_session_id(self, message: str) -> Optional[str]:
        """Извлекает session_id из сообщения лога"""
        import re
        patterns = [
            r'Session: ([^,\s]+)',
            r'session_id[=:\s]+([^,\s]+)',
            r'for session ([^,\s]+)',
            r'Session ID: ([^,\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        return None

def setup_debug_logging():
    """Настраивает сбор логов для отладки"""
    handler = DebugLogHandler()
    
    loggers = [
        'ai_pipeline',
        'json_processor', 
        'command_handler',
        'whatsapp_utils',
        'webhook_flow'
    ]
    
    for logger_name in loggers:
        target_logger = logging.getLogger(logger_name)
        target_logger.addHandler(handler)
        target_logger.setLevel(logging.INFO)

@app.get("/", response_class=HTMLResponse)
async def debug_interface():
    """Главная страница отладки диалогов"""
    
    html_content = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraFlora Debug Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f2f5;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .container {
            max-width: 1400px;
            margin: 20px auto;
            padding: 0 20px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
            height: 80vh;
        }
        
        .sessions-panel {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow-y: auto;
        }
        
        .dialog-panel {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow-y: auto;
        }
        
        .refresh-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 15px;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .refresh-btn:hover {
            background: #45a049;
        }
        
        .session-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.3s;
            border-left: 4px solid transparent;
        }
        
        .session-item:hover {
            background: #e9ecef;
            transform: translateY(-1px);
        }
        
        .session-item.active {
            background: #e3f2fd;
            border-left-color: #2196F3;
        }
        
        .session-id {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .session-meta {
            font-size: 12px;
            color: #666;
        }
        
        .message {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 10px;
            position: relative;
        }
        
        .message.user {
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
            margin-left: 20px;
        }
        
        .message.assistant {
            background: #f3e5f5;
            border-left: 4px solid #9c27b0;
            margin-right: 20px;
        }
        
        .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .message-role {
            font-weight: bold;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
        }
        
        .message-time {
            font-size: 12px;
            color: #666;
        }
        
        .message-content {
            margin-bottom: 10px;
            white-space: pre-wrap;
        }
        
        .debug-btn {
            background: #2196F3;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: background 0.3s;
        }
        
        .debug-btn:hover {
            background: #1976D2;
        }
        
        .debug-details {
            background: #f5f5f5;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
        }
        
        .log-entry {
            background: white;
            border-radius: 4px;
            padding: 8px;
            margin-bottom: 8px;
            border-left: 3px solid #ddd;
        }
        
        .log-entry.ai_pipeline { border-left-color: #FF6B6B; }
        .log-entry.json_processor { border-left-color: #4ECDC4; }
        .log-entry.command_handler { border-left-color: #45B7D1; }
        .log-entry.whatsapp_utils { border-left-color: #96CEB4; }
        .log-entry.webhook_flow { border-left-color: #FFEAA7; }
        
        .log-level {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            margin-right: 8px;
        }
        
        .log-level.INFO { background: #d4edda; color: #155724; }
        .log-level.WARNING { background: #fff3cd; color: #856404; }
        .log-level.ERROR { background: #f8d7da; color: #721c24; }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
        }
        
        .empty-state {
            text-align: center;
            padding: 50px;
            color: #999;
        }
        
        .deploy-controls {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .deploy-controls h3 {
            margin-bottom: 10px;
            color: #856404;
        }
        
        .deploy-id-display {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 8px 12px;
            font-family: monospace;
            margin-bottom: 10px;
            word-break: break-all;
        }
        
        .new-deploy-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .new-deploy-btn:hover {
            background: #c82333;
        }
        
        .new-deploy-btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌸 AuraFlora Debug Viewer</h1>
        <p>Просмотр диалогов с детальной отладкой AI пайплайна</p>
    </div>
    
    <div class="container">
        <div class="grid">
            <div class="sessions-panel">
                <div class="deploy-controls">
                    <h3>🎯 Управление DEPLOY_ID</h3>
                    <div class="deploy-id-display" id="current-deploy-id">Загрузка...</div>
                    <button class="new-deploy-btn" onclick="generateNewDeployId()" id="new-deploy-btn">
                        🔄 Новый DEPLOY_ID
                    </button>
                </div>
                <h3>📱 Сессии пользователей</h3>
                <button class="refresh-btn" onclick="loadSessions()">🔄 Обновить</button>
                <div id="sessions-list">
                    <div class="loading">Загрузка сессий...</div>
                </div>
            </div>
            
            <div class="dialog-panel">
                <h3>💬 Диалог</h3>
                <div id="dialog-content">
                    <div class="empty-state">
                        Выберите сессию для просмотра диалога
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentSessionId = null;
        
        // Загрузка текущего DEPLOY_ID
        async function loadCurrentDeployId() {
            try {
                const response = await fetch('/deploy-id');
                const data = await response.json();
                document.getElementById('current-deploy-id').textContent = data.deploy_id;
            } catch (error) {
                document.getElementById('current-deploy-id').textContent = 'Ошибка загрузки';
                console.error('Error loading deploy ID:', error);
            }
        }
        
        // Генерация нового DEPLOY_ID
        async function generateNewDeployId() {
            const button = document.getElementById('new-deploy-btn');
            button.disabled = true;
            button.textContent = '⏳ Генерация...';
            
            try {
                const response = await fetch('/deploy-id/generate', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('current-deploy-id').textContent = data.new_deploy_id;
                    alert(`✅ DEPLOY_ID изменен!\nСтарый: ${data.old_deploy_id}\nНовый: ${data.new_deploy_id}\n\nТеперь все новые сообщения будут в новых сессиях!`);
                    
                    // Обновляем список сессий
                    loadSessions();
                } else {
                    alert('❌ Ошибка при смене DEPLOY_ID: ' + data.error);
                }
            } catch (error) {
                alert('❌ Ошибка при смене DEPLOY_ID: ' + error.message);
                console.error('Error generating deploy ID:', error);
            } finally {
                button.disabled = false;
                button.textContent = '🔄 Новый DEPLOY_ID';
            }
        }
        
        // Загрузка сессий
        async function loadSessions() {
            try {
                const response = await fetch('/api/sessions');
                const sessions = await response.json();
                
                const container = document.getElementById('sessions-list');
                
                if (sessions.length === 0) {
                    container.innerHTML = '<div class="empty-state">Нет активных сессий</div>';
                    return;
                }
                
                container.innerHTML = sessions.map(session => `
                    <div class="session-item" onclick="selectSession('${session.session_id}')">
                        <div class="session-id">${session.sender_id}</div>
                        <div class="session-meta">
                            📅 ${formatDateTime(session.last_message_time)}<br>
                            💬 ${session.message_count} сообщений
                        </div>
                    </div>
                `).join('');
                
            } catch (error) {
                document.getElementById('sessions-list').innerHTML = 
                    '<div class="empty-state">Ошибка загрузки сессий</div>';
                console.error('Error loading sessions:', error);
            }
        }
        
        // Выбор сессии
        async function selectSession(sessionId) {
            // Обновляем UI
            document.querySelectorAll('.session-item').forEach(item => {
                item.classList.remove('active');
            });
            event.target.closest('.session-item').classList.add('active');
            
            currentSessionId = sessionId;
            
            // Загружаем диалог
            document.getElementById('dialog-content').innerHTML = 
                '<div class="loading">Загрузка диалога...</div>';
            
            try {
                const response = await fetch(`/api/session/${sessionId}/messages`);
                const data = await response.json();
                
                displayDialog(data.messages, data.logs);
                
            } catch (error) {
                document.getElementById('dialog-content').innerHTML = 
                    '<div class="empty-state">Ошибка загрузки диалога</div>';
                console.error('Error loading dialog:', error);
            }
        }
        
        // Отображение диалога
        function displayDialog(messages, logs) {
            const container = document.getElementById('dialog-content');
            
            if (messages.length === 0) {
                container.innerHTML = '<div class="empty-state">Нет сообщений в диалоге</div>';
                return;
            }
            
            container.innerHTML = messages.map((message, index) => {
                // Находим логи для этого сообщения (в окне ±30 секунд)
                const messageTime = new Date(message.timestamp);
                const messageLogs = logs.filter(log => {
                    const logTime = new Date(log.timestamp);
                    return Math.abs(logTime - messageTime) < 30000; // 30 секунд
                });
                
                return `
                    <div class="message ${message.role}">
                        <div class="message-header">
                            <span class="message-role">
                                ${message.role === 'user' ? '👤 Пользователь' : '🤖 AuraFlora'}
                            </span>
                            <span class="message-time">${formatTime(message.timestamp)}</span>
                        </div>
                        
                        <div class="message-content">${escapeHtml(message.content)}</div>
                        
                        ${messageLogs.length > 0 ? `
                            <button class="debug-btn" onclick="toggleDebug(${index})">
                                🔍 Показать детали (${messageLogs.length} логов)
                            </button>
                            
                            <div class="debug-details" id="debug-${index}" style="display: none;">
                                ${formatLogs(messageLogs)}
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
        }
        
        // Переключение отображения деталей
        function toggleDebug(index) {
            const details = document.getElementById(`debug-${index}`);
            const button = details.previousElementSibling;
            
            if (details.style.display === 'none') {
                details.style.display = 'block';
                button.textContent = button.textContent.replace('Показать', 'Скрыть');
            } else {
                details.style.display = 'none';
                button.textContent = button.textContent.replace('Скрыть', 'Показать');
            }
        }
        
        // Форматирование логов
        function formatLogs(logs) {
            return logs.map(log => `
                <div class="log-entry ${log.logger_name}">
                    <span class="log-level ${log.level}">${log.level}</span>
                    <strong>${log.logger_name}</strong>
                    <span style="color: #888; font-size: 11px;">[${formatTime(log.timestamp)}]</span>
                    <div style="margin-top: 5px;">${escapeHtml(log.message)}</div>
                </div>
            `).join('');
        }
        
        // Утилиты форматирования
        function formatDateTime(timestamp) {
            return new Date(timestamp).toLocaleString('ru-RU');
        }
        
        function formatTime(timestamp) {
            return new Date(timestamp).toLocaleTimeString('ru-RU');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', () => {
            loadCurrentDeployId();
            loadSessions();
            
            // Обновляем каждые 30 секунд
            setInterval(loadSessions, 30000);
        });
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/api/sessions")
async def get_sessions():
    """API для получения списка активных сессий"""
    try:
        sessions = []
        
        # Получаем уникальные session_id из логов
        session_ids = set()
        for log_entry in debug_logs:
            if log_entry.get('session_id'):
                session_ids.add(log_entry['session_id'])
        
        # Для каждой сессии собираем информацию
        for session_id in session_ids:
            try:
                if database:
                    # Получаем историю из БД
                    history = database.get_conversation_history(session_id, limit=100)
                else:
                    # Fallback - создаем тестовые данные
                    history = [
                        {
                            'role': 'user',
                            'content': 'Привет!',
                            'timestamp': datetime.now()
                        }
                    ]
                
                if history:
                    # Извлекаем sender_id
                    sender_id = session_id.split('_')[0] if '_' in session_id else session_id
                    
                    # Последнее сообщение
                    last_message = max(history, key=lambda x: x.get('timestamp', datetime.min))
                    
                    sessions.append({
                        'session_id': session_id,
                        'sender_id': sender_id,
                        'message_count': len(history),
                        'last_message_time': last_message.get('timestamp', datetime.now()).isoformat()
                    })
                    
            except Exception as e:
                print(f"Error processing session {session_id}: {e}")
                continue
        
        # Сортируем по времени
        sessions.sort(key=lambda x: x['last_message_time'], reverse=True)
        
        return JSONResponse(content=sessions)
        
    except Exception as e:
        print(f"Error getting sessions: {e}")
        return JSONResponse(content=[])

@app.get("/api/session/{session_id}/messages")
async def get_session_messages(session_id: str):
    """API для получения сообщений сессии с логами"""
    try:
        messages = []
        
        if database:
            # Получаем историю из БД
            history = database.get_conversation_history(session_id, limit=100)
            
            for msg in history:
                messages.append({
                    'role': msg.get('role', 'unknown'),
                    'content': msg.get('content', ''),
                    'timestamp': msg.get('timestamp', datetime.now()).isoformat()
                })
        else:
            # Fallback - тестовые данные
            messages = [
                {
                    'role': 'user',
                    'content': 'Привет! Покажи мне каталог.',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'role': 'assistant',
                    'content': 'Здравствуйте! Сейчас покажу вам наш каталог цветов.',
                    'timestamp': datetime.now().isoformat()
                }
            ]
        
        # Получаем логи для этой сессии
        session_logs = [
            log for log in debug_logs 
            if log.get('session_id') == session_id
        ]
        
        return JSONResponse(content={
            'messages': messages,
            'logs': session_logs
        })
        
    except Exception as e:
        print(f"Error getting session messages: {e}")
        return JSONResponse(content={'messages': [], 'logs': []})

@app.get("/deploy-id")
async def get_deploy_id_proxy():
    """Прокси для получения DEPLOY_ID с основного сервера"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/deploy-id")
            return JSONResponse(content=response.json())
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/deploy-id/generate")
async def generate_deploy_id_proxy():
    """Прокси для генерации нового DEPLOY_ID"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:8000/deploy-id/generate")
            return JSONResponse(content=response.json())
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    
    # Настраиваем сбор логов
    setup_debug_logging()
    
    print("🌸 Запуск AuraFlora Debug Viewer...")
    print("📱 Откройте http://localhost:8001 для просмотра диалогов")
    
    uvicorn.run(app, host="0.0.0.0", port=8001) 