/**
 * Лог-вьювер для JSON Lines файлов
 */

// Глобальные переменные
let allLogs = [];
let filteredLogs = [];
let currentFilters = {
    search: '',
    module: '',
    event: '',
    timeFrom: '',
    timeTo: ''
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    loadLogs();
    setupEventListeners();
});

// Настройка обработчиков событий
function setupEventListeners() {
    // Поиск при вводе
    document.getElementById('searchInput').addEventListener('input', function(e) {
        currentFilters.search = e.target.value;
        filterLogs();
    });

    // Фильтр по модулю
    document.getElementById('moduleFilter').addEventListener('change', function(e) {
        currentFilters.module = e.target.value;
        filterLogs();
    });

    // Фильтр по событию
    document.getElementById('eventFilter').addEventListener('change', function(e) {
        currentFilters.event = e.target.value;
        filterLogs();
    });

    // Фильтры по времени
    document.getElementById('timeFrom').addEventListener('change', function(e) {
        currentFilters.timeFrom = e.target.value;
        filterLogs();
    });

    document.getElementById('timeTo').addEventListener('change', function(e) {
        currentFilters.timeTo = e.target.value;
        filterLogs();
    });
}

// Загрузка логов из API
async function loadLogs() {
    try {
        const response = await fetch('/api/logs');
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        allLogs = data.logs || [];
        updateModuleFilter();
        filterLogs();
        
    } catch (error) {
        showError('Ошибка загрузки логов: ' + error.message);
    }
}

// Обновление фильтра модулей
function updateModuleFilter() {
    const moduleFilter = document.getElementById('moduleFilter');
    const modules = [...new Set(allLogs.map(log => log.module).filter(Boolean))];
    
    // Сохраняем текущее значение
    const currentValue = moduleFilter.value;
    
    // Очищаем и добавляем опции
    moduleFilter.innerHTML = '<option value="">Все модули</option>';
    modules.sort().forEach(module => {
        const option = document.createElement('option');
        option.value = module;
        option.textContent = module;
        moduleFilter.appendChild(option);
    });
    
    // Восстанавливаем значение
    moduleFilter.value = currentValue;
}

// Фильтрация логов
function filterLogs() {
    filteredLogs = allLogs.filter(log => {
        // Фильтр по поиску
        if (currentFilters.search) {
            const searchLower = currentFilters.search.toLowerCase();
            const logText = JSON.stringify(log).toLowerCase();
            if (!logText.includes(searchLower)) {
                return false;
            }
        }
        
        // Фильтр по модулю
        if (currentFilters.module && log.module !== currentFilters.module) {
            return false;
        }
        
        // Фильтр по событию
        if (currentFilters.event && log.event !== currentFilters.event) {
            return false;
        }
        
        // Фильтр по времени
        if (currentFilters.timeFrom || currentFilters.timeTo) {
            const logTime = new Date(log.timestamp);
            
            if (currentFilters.timeFrom) {
                const fromTime = new Date(currentFilters.timeFrom);
                if (logTime < fromTime) {
                    return false;
                }
            }
            
            if (currentFilters.timeTo) {
                const toTime = new Date(currentFilters.timeTo);
                if (logTime > toTime) {
                    return false;
                }
            }
        }
        
        return true;
    });
    
    renderLogs();
}

// Отрисовка логов
function renderLogs() {
    const container = document.getElementById('logsContainer');
    
    if (filteredLogs.length === 0) {
        container.innerHTML = '<div class="no-logs">Логи не найдены</div>';
        return;
    }
    
    // Сортируем по времени (новые сверху)
    const sortedLogs = [...filteredLogs].sort((a, b) => {
        return new Date(b.timestamp) - new Date(a.timestamp);
    });
    
    container.innerHTML = sortedLogs.map(log => createLogEntry(log)).join('');
    
    // Добавляем обработчики для раскрытия деталей
    document.querySelectorAll('.log-entry').forEach(entry => {
        entry.addEventListener('click', function() {
            this.classList.toggle('expanded');
        });
    });
}

// Создание элемента лога
function createLogEntry(log) {
    const timestamp = formatLogTimestamp(log.timestamp);
    const executionTime = log.execution_time_ms ? `${log.execution_time_ms}ms` : '';
    
    let detailsHtml = '';
    
    // Параметры
    if (log.parameters && Object.keys(log.parameters).length > 0) {
        detailsHtml += `
            <div class="log-section">
                <div class="log-section-title">Параметры</div>
                <div class="log-section-content log-parameters">${JSON.stringify(log.parameters, null, 2)}</div>
            </div>
        `;
    }
    
    // Результат
    if (log.result !== undefined) {
        detailsHtml += `
            <div class="log-section">
                <div class="log-section-title">Результат</div>
                <div class="log-section-content log-result">${JSON.stringify(log.result, null, 2)}</div>
            </div>
        `;
    }
    
    // Ошибка
    if (log.error_type || log.error_message) {
        detailsHtml += `
            <div class="log-section">
                <div class="log-section-title">Ошибка</div>
                <div class="log-section-content log-error">
                    Тип: ${log.error_type || 'Неизвестно'}\nСообщение: ${log.error_message || 'Нет сообщения'}
                </div>
            </div>
        `;
    }
    
    return `
        <div class="log-entry" data-event="${log.event}">
            <div class="log-header">
                <div class="log-meta">
                    <span class="log-timestamp">${timestamp}</span>
                    <span class="log-module">${log.module || 'unknown'}</span>
                    <span class="log-function">${log.function || 'unknown'}</span>
                    <span class="log-event ${log.event}">${getEventDisplayName(log.event)}</span>
                </div>
                ${executionTime ? `<span class="log-execution-time">${executionTime}</span>` : ''}
            </div>
            ${detailsHtml ? `<div class="log-details">${detailsHtml}</div>` : ''}
        </div>
    `;
}

// Получение отображаемого имени события
function getEventDisplayName(event) {
    const names = {
        'function_start': 'Начало',
        'function_end': 'Завершение',
        'function_error': 'Ошибка'
    };
    return names[event] || event;
}



// Функции управления
function searchLogs() {
    const searchInput = document.getElementById('searchInput');
    currentFilters.search = searchInput.value;
    filterLogs();
}

function clearFilters() {
    currentFilters = {
        search: '',
        module: '',
        event: '',
        timeFrom: '',
        timeTo: ''
    };
    
    document.getElementById('searchInput').value = '';
    document.getElementById('moduleFilter').value = '';
    document.getElementById('eventFilter').value = '';
    document.getElementById('timeFrom').value = '';
    document.getElementById('timeTo').value = '';
    
    filterLogs();
}

function refreshLogs() {
    // Показываем индикатор загрузки
    const container = document.getElementById('logsContainer');
    container.innerHTML = '<div class="loading">Обновление логов...</div>';
    
    // Загружаем логи
    loadLogs().then(() => {
        // Показываем уведомление об успешном обновлении
        showNotification('Логи обновлены', 'success');
    }).catch((error) => {
        showNotification('Ошибка обновления логов', 'error');
    });
}

// Установить временной диапазон в минутах
function setTimeRange(minutes) {
    const now = new Date();
    const fromTime = new Date(now.getTime() - (minutes * 60 * 1000));
    
    document.getElementById('timeFrom').value = fromTime.toISOString().slice(0, 16);
    document.getElementById('timeTo').value = now.toISOString().slice(0, 16);
    
    currentFilters.timeFrom = document.getElementById('timeFrom').value;
    currentFilters.timeTo = document.getElementById('timeTo').value;
    
    filterLogs();
}

// Быстрые фильтры времени в минутах
function setLastMinutes(minutes) {
    setTimeRange(minutes);
}

// Показать ошибку
function showError(message) {
    const container = document.getElementById('logsContainer');
    container.innerHTML = `<div class="no-logs" style="color: #dc3545;">${message}</div>`;
}

// Форматирование времени без года
function formatLogTimestamp(ts) {
    if (!ts) return '';
    const d = new Date(ts);
    // Формат: дд.мм чч:мм:сс
    const pad = n => n.toString().padStart(2, '0');
    return `${pad(d.getDate())}.${pad(d.getMonth()+1)} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function copyLogsToClipboard() {
    if (!filteredLogs.length) {
        alert('Нет логов для копирования!');
        return;
    }
    const text = filteredLogs.map(log => JSON.stringify(log)).join('\n');
    navigator.clipboard.writeText(text).then(() => {
        alert('Логи скопированы в буфер обмена!');
    }, () => {
        alert('Не удалось скопировать логи');
    });
}

// Функция для показа уведомлений
function showNotification(message, type = 'info') {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Добавляем стили
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        color: white;
        font-weight: bold;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    
    // Цвета для разных типов уведомлений
    if (type === 'success') {
        notification.style.backgroundColor = '#28a745';
    } else if (type === 'error') {
        notification.style.backgroundColor = '#dc3545';
    } else {
        notification.style.backgroundColor = '#17a2b8';
    }
    
    // Добавляем на страницу
    document.body.appendChild(notification);
    
    // Удаляем через 3 секунды
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
} 