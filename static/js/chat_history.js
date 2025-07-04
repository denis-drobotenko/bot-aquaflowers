// Переводы для разных языков
const translations = {
    'ru': {
        title: 'История переписки',
        sessionId: 'ID сессии',
        messageCount: 'Количество сообщений',
        user: 'Пользователь',
        phone: 'Телефон',
        backToHome: '← Вернуться на главную',
        print: '🖨️ Печать',
        toTop: '⬆️ В начало'
    },
    'en': {
        title: 'Chat History',
        sessionId: 'Session ID',
        messageCount: 'Message Count',
        user: 'User',
        phone: 'Phone',
        backToHome: '← Back to Home',
        print: '🖨️ Print',
        toTop: '⬆️ To Top'
    },
    'th': {
        title: 'ประวัติการสนทนา',
        sessionId: 'รหัสเซสชัน',
        messageCount: 'จำนวนข้อความ',
        user: 'ผู้ใช้',
        phone: 'โทรศัพท์',
        backToHome: '← กลับหน้าหลัก',
        print: '🖨️ พิมพ์',
        toTop: '⬆️ ขึ้นบน'
    }
};

// Функция перевода одного сообщения с анимацией и обработкой ошибок
async function translateSingleMessage(messageElement, targetLang) {
    try {
        const contentElement = messageElement.querySelector('.message-content');
        const originalText = contentElement.textContent || contentElement.innerText;
        
        // Показываем индикатор загрузки и текст 'Translating...'
        contentElement.innerHTML = '<div style="display: flex; flex-direction: column; gap: 4px; color: #666;"><div style="display: flex; align-items: center; gap: 8px;"><div class="loading-spinner"></div><span>Translating...</span></div></div>';
        
        const response = await fetch('/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: originalText,
                lang: targetLang
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            contentElement.style.transition = 'opacity 0.3s ease-out';
            contentElement.style.opacity = '0';
            await new Promise(resolve => setTimeout(resolve, 300));
            // Показываем только перевод
            contentElement.innerHTML = '<div>' + data.translated_text + '</div>';
            contentElement.style.opacity = '1';
            return data.translated_text;
        } else if (response.status === 429) {
            // Ошибка превышения квоты - ждем и повторяем
            console.log('Rate limit exceeded, waiting 5 seconds...');
            contentElement.innerHTML = '<div style="color: #666;">Rate limit exceeded, retrying in 5s...</div>';
            await new Promise(resolve => setTimeout(resolve, 5000));
            return await translateSingleMessage(messageElement, targetLang);
        } else {
            console.error('Translation failed:', response.status, response.statusText);
            contentElement.textContent = originalText;
            return originalText;
        }
    } catch (error) {
        console.error('Translation error:', error);
        const contentElement = messageElement.querySelector('.message-content');
        contentElement.textContent = originalText;
        return originalText;
    }
}

// Функция перевода всего диалога по одному сообщению
async function translateChat(lang) {
    try {
        console.log('Translating entire chat to:', lang, 'message by message');
        
        // Блокируем кнопки во время перевода
        const buttons = document.querySelectorAll('.lang-btn');
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.5';
        });
        
        // Получаем все сообщения
        const messages = Array.from(document.querySelectorAll('.message'));
        console.log('Found messages to translate:', messages.length);
        
        // Переводим каждое сообщение по очереди
        for (let i = 0; i < messages.length; i++) {
            const message = messages[i];
            
            // Переводим сообщение
            await translateSingleMessage(message, lang);
            
            // Увеличенная пауза между сообщениями для избежания превышения лимитов
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        // Обновляем заголовок
        document.querySelector('.header h1').textContent = translations[lang].title;
        
        console.log('Chat translation completed message by message');
        
        // Разблокируем кнопки
        buttons.forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
        });
        
    } catch (error) {
        console.error('Chat translation error:', error);
        alert('Ошибка при переводе: ' + error.message);
        
        // Разблокируем кнопки при ошибке
        const buttons = document.querySelectorAll('.lang-btn');
        buttons.forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
        });
    }
}

// Обработчики кнопок перевода
document.addEventListener('DOMContentLoaded', function() {
    // Устанавливаем активную кнопку в зависимости от параметра lang в URL
    const urlParams = new URLSearchParams(window.location.search);
    const currentLang = urlParams.get('lang') || 'ru';
    
    const langButtons = document.querySelectorAll('.lang-btn');
    langButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-lang') === currentLang) {
            btn.classList.add('active');
        }
    });
    
    langButtons.forEach(button => {
        button.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            
            // Обновляем активную кнопку
            langButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Если выбран русский язык, просто перезагружаем страницу
            if (lang === 'ru') {
                const currentUrl = new URL(window.location);
                currentUrl.searchParams.set('lang', 'ru');
                window.location.href = currentUrl.toString();
                return;
            }
            
            // Для других языков запускаем перевод по одному сообщению
            translateChat(lang);
        });
    });
    
    // Добавляем CSS для спиннера загрузки
    const style = document.createElement('style');
    style.textContent = `
        .loading-spinner {
            width: 16px;
            height: 16px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
});