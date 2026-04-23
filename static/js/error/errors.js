/**
 * Error Pages JavaScript
 * Interactive functionality for Ukrainian-themed Django error pages
 * 
 * @version 2.0
 * @author Your Project
 */

// Immediately Invoked Function Expression to avoid global scope pollution
(function() {
    'use strict';

    /**
     * Initialize all error page functionality when DOM is ready
     */
    document.addEventListener('DOMContentLoaded', function() {
        initErrorCodeAnimation();
        initButtonRippleEffect();
        initKeyboardShortcuts();
        logErrorToConsole();
        initEasterEgg();
    });

    /**
     * Animate error code number with typewriter effect
     */
    function initErrorCodeAnimation() {
        const errorCode = document.querySelector('.error-code-container h1');
        
        if (!errorCode) return;
        
        const text = errorCode.textContent;
        errorCode.textContent = '';
        
        let index = 0;
        const typingInterval = setInterval(() => {
            if (index < text.length) {
                errorCode.textContent += text[index];
                index++;
            } else {
                clearInterval(typingInterval);
            }
        }, 100);
    }

    /**
     * Add ripple effect to buttons on click
     */
    function initButtonRippleEffect() {
        const buttons = document.querySelectorAll('.btn-primary, .btn-secondary');
        
        buttons.forEach(button => {
            button.addEventListener('click', createRipple);
        });
    }

    /**
     * Create ripple effect element
     * @param {Event} event - Click event
     */
    function createRipple(event) {
        const button = event.currentTarget;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        button.appendChild(ripple);
        
        // Remove ripple after animation
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    /**
     * Initialize keyboard shortcuts for navigation
     */
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', handleKeyboardShortcut);
    }

    /**
     * Handle keyboard shortcuts
     * @param {KeyboardEvent} event - Keyboard event
     */
    function handleKeyboardShortcut(event) {
        // Ignore if user is typing in an input
        if (event.target.tagName === 'INPUT' || 
            event.target.tagName === 'TEXTAREA') {
            return;
        }

        switch(event.key.toLowerCase()) {
            case 'h': // Go to homepage
            case 'р': // Cyrillic 'h'
                event.preventDefault();
                window.location.href = '/';
                break;
                
            case 'b': // Go back
            case 'и': // Cyrillic 'b'
                event.preventDefault();
                goBack();
                break;
                
            case 'r': // Reload page
            case 'к': // Cyrillic 'r'
                event.preventDefault();
                window.location.reload();
                break;
        }
    }

    /**
     * Navigate back in browser history
     */
    function goBack() {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = '/';
        }
    }

    /**
     * Log error details to console for debugging
     */
    function logErrorToConsole() {
        const errorCode = document.querySelector('.error-code-container h1')?.textContent;
        const errorTitle = document.querySelector('h2')?.textContent;
        
        if (!errorCode) return;
        
        console.group('🚨 Error Page Information');
        console.log('%cError Code:', 'font-weight: bold; color: #0057B7;', errorCode);
        console.log('%cError Title:', 'font-weight: bold; color: #FFD700;', errorTitle);
        console.log('%cCurrent URL:', 'font-weight: bold;', window.location.href);
        console.log('%cReferrer:', 'font-weight: bold;', document.referrer || 'Direct access');
        console.log('%cUser Agent:', 'font-weight: bold;', navigator.userAgent);
        console.log('%cTimestamp:', 'font-weight: bold;', new Date().toISOString());
        console.log('%cScreen Resolution:', 'font-weight: bold;', `${window.screen.width}x${window.screen.height}`);
        console.groupEnd();
    }

    /**
     * Copy error details to clipboard
     */
    function copyErrorDetails() {
        const errorCode = document.querySelector('.error-code-container h1')?.textContent;
        const errorTitle = document.querySelector('h2')?.textContent;
        
        const details = `
Код помилки: ${errorCode}
Помилка: ${errorTitle}
URL: ${window.location.href}
Час: ${new Date().toLocaleString('uk-UA')}
Браузер: ${navigator.userAgent}
        `.trim();
        
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(details)
                .then(() => {
                    showNotification('Деталі помилки скопійовано в буфер обміну');
                })
                .catch(() => {
                    console.error('Failed to copy error details');
                    fallbackCopyText(details);
                });
        } else {
            fallbackCopyText(details);
        }
    }

    /**
     * Fallback method for copying text (older browsers)
     * @param {string} text - Text to copy
     */
    function fallbackCopyText(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            showNotification('Деталі помилки скопійовано');
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
        
        document.body.removeChild(textArea);
    }

    /**
     * Show temporary notification
     * @param {string} message - Message to display
     * @param {number} duration - Duration in milliseconds (default: 3000)
     */
    function showNotification(message, duration = 3000) {
        const notification = document.createElement('div');
        notification.className = 'error-notification animate-slide-up';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, duration);
    }

    /**
     * Initialize Easter Egg - Konami Code
     */
    function initEasterEgg() {
        let konamiCode = [];
        const konamiSequence = [
            'ArrowUp', 'ArrowUp', 
            'ArrowDown', 'ArrowDown', 
            'ArrowLeft', 'ArrowRight', 
            'ArrowLeft', 'ArrowRight', 
            'b', 'a'
        ];

        document.addEventListener('keydown', function(e) {
            konamiCode.push(e.key);
            konamiCode = konamiCode.slice(-10);
            
            if (konamiCode.join(',') === konamiSequence.join(',')) {
                activateEasterEgg();
            }
        });
    }

    /**
     * Activate Easter Egg animation
     */
    function activateEasterEgg() {
        // Add rainbow animation
        document.body.style.animation = 'rainbow 2s linear infinite';
        
        // Show notification
        showNotification('🎉 Ви знайшли секретний код! 🇺🇦', 5000);
        
        // Create confetti effect
        createConfetti();
        
        // Remove animation after 5 seconds
        setTimeout(() => {
            document.body.style.animation = '';
        }, 5000);
    }

    /**
     * Create simple confetti effect
     */
    function createConfetti() {
        const colors = ['#0057B7', '#FFD700', '#FFEB3B'];
        const confettiCount = 50;
        
        for (let i = 0; i < confettiCount; i++) {
            setTimeout(() => {
                const confetti = document.createElement('div');
                confetti.style.position = 'fixed';
                confetti.style.width = '10px';
                confetti.style.height = '10px';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.left = Math.random() * window.innerWidth + 'px';
                confetti.style.top = '-10px';
                confetti.style.opacity = '1';
                confetti.style.transform = 'rotate(' + Math.random() * 360 + 'deg)';
                confetti.style.transition = 'all 3s ease-out';
                confetti.style.zIndex = '9999';
                confetti.style.pointerEvents = 'none';
                
                document.body.appendChild(confetti);
                
                setTimeout(() => {
                    confetti.style.top = window.innerHeight + 'px';
                    confetti.style.opacity = '0';
                    confetti.style.transform = 'rotate(' + (Math.random() * 720) + 'deg)';
                }, 10);
                
                setTimeout(() => {
                    confetti.remove();
                }, 3000);
            }, i * 30);
        }
    }

    /**
     * Optional: Auto-redirect timer
     * Uncomment to enable automatic redirect after specified time
     * 
     * @param {number} seconds - Seconds until redirect
     * @param {string} url - URL to redirect to (default: '/')
     */
    /*
    function initAutoRedirect(seconds = 10, url = '/') {
        let timeLeft = seconds;
        
        const timerElement = document.createElement('p');
        timerElement.className = 'mt-4 text-sm text-gray-500 auto-redirect-timer';
        timerElement.textContent = `Автоматичне перенаправлення через ${timeLeft} секунд...`;
        
        const footer = document.querySelector('.text-center.mt-8');
        if (footer) {
            footer.appendChild(timerElement);
        }
        
        const countdown = setInterval(() => {
            timeLeft--;
            timerElement.textContent = `Автоматичне перенаправлення через ${timeLeft} секунд...`;
            
            if (timeLeft <= 0) {
                clearInterval(countdown);
                window.location.href = url;
            }
        }, 1000);
        
        // Allow user to cancel redirect
        document.addEventListener('mousemove', () => {
            clearInterval(countdown);
            if (timerElement) {
                timerElement.textContent = 'Автоматичне перенаправлення скасовано';
            }
        }, { once: true });
    }
    
    // To enable auto-redirect, uncomment:
    // initAutoRedirect(10, '/');
    */

    /**
     * Track error page view (for analytics)
     * Uncomment and configure for your analytics platform
     */
    function trackErrorPage() {
        const errorCode = document.querySelector('.error-code-container h1')?.textContent;
        
        // Google Analytics example
        if (typeof gtag !== 'undefined') {
            gtag('event', 'error_page_view', {
                'error_code': errorCode,
                'page_path': window.location.pathname
            });
        }
        
        // Yandex Metrika example
        if (typeof ym !== 'undefined') {
            ym(12345678, 'reachGoal', 'error_page', {
                error_code: errorCode
            });
        }
    }

    // Export functions for external use
    window.ErrorPageFunctions = {
        goBack: goBack,
        copyErrorDetails: copyErrorDetails,
        showNotification: showNotification,
        trackErrorPage: trackErrorPage
    };

})();

/**
 * Console Easter Egg
 * Display a message in the console for curious developers
 */
console.log(
    '%c🇺🇦 Error Page System v2.0',
    'font-size: 20px; font-weight: bold; color: #0057B7; background: #FFD700; padding: 10px;'
);
console.log(
    '%cЯкщо ви читаєте це, можливо, ви шукаєте помилки. Або просто цікаві! 😊',
    'font-size: 14px; color: #666;'
);
console.log(
    '%cКлавіатурні скорочення:\n- H: На головну\n- B: Назад\n- R: Оновити\n\nБонус: Спробуйте ввести Konami Code! ↑↑↓↓←→←→BA',
    'font-size: 12px; color: #999;'
);