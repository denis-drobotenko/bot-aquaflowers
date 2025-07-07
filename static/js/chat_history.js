// Современный JavaScript для чата AuraFlora
console.log('🚀 Chat history JavaScript загружается...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM загружен, инициализируем интерфейс...');
    
    // Отмечаем, что внешний JS загружен
    window.chatHistoryInitialized = true;
    
    const langButtons = document.querySelectorAll('.lang-btn');
    const chatContainer = document.querySelector('.chat-container');
    const chatScrollArea = document.querySelector('.chat-scroll-area');
    
    console.log(`📱 Найдено кнопок языков: ${langButtons.length}`);
    console.log(`💬 Контейнер чата: ${chatContainer ? 'найден' : 'НЕ НАЙДЕН'}`);
    console.log(`📜 Область скролла: ${chatScrollArea ? 'найдена' : 'НЕ НАЙДЕНА'}`);
    
    // Проверяем загрузку CSS
    const styles = getComputedStyle(document.body);
    const primaryColor = styles.getPropertyValue('--primary-color');
    console.log(`🎨 CSS переменные загружены: ${primaryColor ? 'ДА' : 'НЕТ'}`);
    
    // Функция для показа индикатора загрузки
    function showLoading() {
        console.log('⏳ Показываем индикатор загрузки...');
        chatContainer.innerHTML = `
            <div class="loading-indicator">
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
    }
    
    // Функция для показа ошибки
    function showError(message) {
        console.error('❌ Ошибка:', message);
        chatContainer.innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: #ff4444;">
                <div style="font-size: 2em; margin-bottom: 10px;">⚠️</div>
                <div style="font-weight: 500; margin-bottom: 5px;">Ошибка загрузки</div>
                <div style="font-size: 0.9em; opacity: 0.8;">${message}</div>
            </div>
        `;
    }
    
    // Функция для плавной прокрутки вверх
    function scrollToTop() {
        setTimeout(() => {
            if (chatScrollArea) {
                chatScrollArea.scrollTop = 0;
                console.log('📜 Прокрутка вверх выполнена');
            }
        }, 100);
    }
    
    // Функция для анимации кнопки
    function animateButton(button) {
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = '';
        }, 150);
    }
    
    // Обработчики кнопок перевода
    langButtons.forEach((button, index) => {
        console.log(`🔘 Настраиваем кнопку ${index + 1}: ${button.getAttribute('data-lang')}`);
        
        // Добавляем обработчики для разных типов событий
        const events = ['click', 'touchend'];
        
        events.forEach(eventType => {
            button.addEventListener(eventType, function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const lang = this.getAttribute('data-lang');
                console.log(`🔄 Переключаем на язык: ${lang}`);
                
                // Анимация кнопки
                animateButton(this);
                
                // Обновляем активную кнопку с анимацией
                langButtons.forEach(btn => {
                    btn.classList.remove('active');
                    btn.style.transform = '';
                });
                
                this.classList.add('active');
                
                // Получаем sender_id и session_id из URL
                const pathParts = window.location.pathname.split('/');
                const sender_id = pathParts[3]; // /chat/history/{sender_id}/{session_id}
                const session_id = pathParts[4];
                
                console.log('🔗 URL части:', pathParts);
                console.log('👤 Sender ID:', sender_id);
                console.log('📋 Session ID:', session_id);
                
                if (!sender_id || !session_id) {
                    console.error('❌ Не удалось определить sender_id или session_id из URL');
                    showError('Не удалось определить параметры сессии');
                    return;
                }
                
                // Показываем индикатор загрузки
                showLoading();
                
                const apiUrl = `/chat/api/messages/${sender_id}/${session_id}/${lang}`;
                console.log('🌐 Загружаем:', apiUrl);
                
                // Загружаем сообщения на выбранном языке
                fetch(apiUrl, {
                    method: 'GET',
                    headers: {
                        'ngrok-skip-browser-warning': 'true',
                        'Accept': 'application/json',
                        'Cache-Control': 'no-cache'
                    }
                })
                .then(response => {
                    console.log('📡 Ответ сервера:', response.status, response.statusText);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('✅ Данные получены:', data);
                    if (data.error) {
                        showError(data.error);
                    } else {
                        // Плавно обновляем содержимое
                        chatContainer.style.opacity = '0';
                        setTimeout(() => {
                            chatContainer.innerHTML = data.messages;
                            chatContainer.style.opacity = '1';
                            scrollToTop();
                            console.log('✅ Сообщения обновлены');
                        }, 200);
                    }
                })
                .catch(error => {
                    console.error('❌ Ошибка загрузки сообщений:', error);
                    showError('Ошибка загрузки сообщений. Попробуйте еще раз.');
                });
            }, { passive: false });
        });
        
        // Улучшенная обработка hover эффектов для мобильных
        if ('ontouchstart' in window) {
            console.log('📱 Обнаружено touch устройство, добавляем touch обработчики');
            button.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.95)';
            });
            
            button.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            });
        }
    });
    
    // Автоматическая прокрутка при загрузке страницы
    scrollToTop();
    
    // Обработка изменения размера окна
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(scrollToTop, 100);
    });
    
    // Улучшенная обработка скролла
    let scrollTimeout;
    if (chatScrollArea) {
        chatScrollArea.addEventListener('scroll', function() {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                // Можно добавить логику для lazy loading или других функций
            }, 100);
        });
    }
    
    // Добавляем поддержку клавиатуры
    document.addEventListener('keydown', function(e) {
        // ESC для сброса фокуса
        if (e.key === 'Escape') {
            document.activeElement.blur();
        }
        
        // Стрелки для навигации по кнопкам языков
        if (e.target.classList.contains('lang-btn')) {
            const buttons = Array.from(langButtons);
            const currentIndex = buttons.indexOf(e.target);
            
            if (e.key === 'ArrowLeft' && currentIndex > 0) {
                buttons[currentIndex - 1].focus();
            } else if (e.key === 'ArrowRight' && currentIndex < buttons.length - 1) {
                buttons[currentIndex + 1].focus();
            }
        }
    });
    
    // Улучшенная доступность
    langButtons.forEach(button => {
        button.setAttribute('role', 'button');
        button.setAttribute('tabindex', '0');
    });
    
    console.log('🎉 Chat history interface инициализирован успешно!');
    
    // Проверяем загрузку всех ресурсов
    setTimeout(() => {
        const images = document.querySelectorAll('img');
        const stylesheets = document.querySelectorAll('link[rel="stylesheet"]');
        const scripts = document.querySelectorAll('script[src]');
        
        console.log(`📊 Статистика загрузки:`);
        console.log(`   - Изображения: ${images.length}`);
        console.log(`   - CSS файлы: ${stylesheets.length}`);
        console.log(`   - JS файлы: ${scripts.length}`);
        
        // Проверяем, загрузились ли стили
        const testElement = document.createElement('div');
        testElement.style.position = 'absolute';
        testElement.style.visibility = 'hidden';
        testElement.style.height = '0';
        testElement.style.overflow = 'hidden';
        testElement.className = 'main-chat-area';
        document.body.appendChild(testElement);
        
        const computedStyle = window.getComputedStyle(testElement);
        const hasStyles = computedStyle.display !== 'inline' || computedStyle.maxWidth !== 'none';
        
        console.log(`   - CSS стили загружены: ${hasStyles ? 'ДА' : 'НЕТ'}`);
        
        document.body.removeChild(testElement);
    }, 1000);
});