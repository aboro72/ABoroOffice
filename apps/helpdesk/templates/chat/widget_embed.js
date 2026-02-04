/**
 * ABoro-IT Chat Widget - External Embedding Script
 * =================================================
 * 
 * Robustes Chat Widget für externe Websites mit CORS-Support
 * Verwendet PostMessage API für sichere Kommunikation
 */

(function() {
    'use strict';
    
    // Configuration - kann von extern überschrieben werden
    window.AboroChatConfig = window.AboroChatConfig || {
        chatHost: 'https://help.aboro-it.net',
        widgetColor: '#667eea',
        position: 'bottom-right',
        autoOpen: false,
        language: 'de'
    };
    
    const config = window.AboroChatConfig;
    const chatHost = config.chatHost;
    
    // Prevent multiple initializations
    if (window.AboroChatWidget) return;
    
    // Chat Widget Class
    class AboroChatWidget {
        constructor() {
            this.isOpen = false;
            this.isInitialized = false;
            this.sessionId = null;
            this.container = null;
            this.button = null;
            this.chatInterface = null;
            this.messagesArea = null;
            this.messageInput = null;
            this.pollInterval = null;
            this.processedMessages = new Set();
            
            this.init();
        }
        
        init() {
            this.createWidget();
            this.setupMessageListener();
            this.loadWidgetData();
            
            if (config.autoOpen) {
                setTimeout(() => this.open(), 2000);
            }
            
            this.isInitialized = true;
        }
        
        createWidget() {
            // Chat Button
            this.button = document.createElement('div');
            this.button.id = 'aboro-chat-button';
            this.button.innerHTML = '💬';
            this.setButtonStyles();
            this.button.addEventListener('click', () => this.toggle());
            
            // Chat Container
            this.container = document.createElement('div');
            this.container.id = 'aboro-chat-container';
            this.setContainerStyles();
            this.container.style.display = 'none';
            
            // Close Button
            const closeBtn = document.createElement('div');
            closeBtn.id = 'aboro-chat-close';
            closeBtn.innerHTML = '×';
            closeBtn.style.cssText = `
                position: absolute;
                top: 10px;
                right: 15px;
                color: white;
                font-size: 20px;
                cursor: pointer;
                z-index: 10001;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: background 0.2s;
            `;
            closeBtn.addEventListener('click', () => this.close());
            closeBtn.addEventListener('mouseenter', () => {
                closeBtn.style.background = 'rgba(255,255,255,0.2)';
            });
            closeBtn.addEventListener('mouseleave', () => {
                closeBtn.style.background = 'transparent';
            });
            
            this.container.appendChild(closeBtn);
            
            // Add to page
            document.body.appendChild(this.button);
            document.body.appendChild(this.container);
        }
        
        setButtonStyles() {
            const position = config.position;
            const positionStyles = this.getPositionStyles(position);
            
            this.button.style.cssText = `
                position: fixed;
                ${positionStyles.button}
                z-index: 10000;
                width: 60px;
                height: 60px;
                background: ${config.widgetColor};
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: white;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                transition: all 0.3s ease;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            `;
            
            // Hover effects
            this.button.addEventListener('mouseenter', () => {
                this.button.style.transform = 'scale(1.1)';
                this.button.style.boxShadow = '0 6px 25px rgba(0,0,0,0.25)';
            });
            
            this.button.addEventListener('mouseleave', () => {
                this.button.style.transform = 'scale(1)';
                this.button.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)';
            });
        }
        
        setContainerStyles() {
            const position = config.position;
            const positionStyles = this.getPositionStyles(position);
            
            this.container.style.cssText = `
                position: fixed;
                ${positionStyles.container}
                z-index: 9999;
                width: 400px;
                height: 600px;
                max-width: 90vw;
                max-height: 90vh;
                background: white;
                border-radius: 10px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.2);
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                border: 1px solid #e0e0e0;
            `;
        }
        
        getPositionStyles(position) {
            const styles = {
                'bottom-right': {
                    button: 'bottom: 20px; right: 20px;',
                    container: 'bottom: 90px; right: 20px;'
                },
                'bottom-left': {
                    button: 'bottom: 20px; left: 20px;',
                    container: 'bottom: 90px; left: 20px;'
                }
            };
            
            return styles[position] || styles['bottom-right'];
        }
        
        loadWidgetData() {
            // Load widget configuration from server
            fetch(`${chatHost}/chat/widget-data/`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    this.sessionId = data.widget_data.session_id;
                    
                    // Update widget color if provided
                    if (data.widget_data.widget_color) {
                        config.widgetColor = data.widget_data.widget_color;
                        this.button.style.background = config.widgetColor;
                    }
                }
            })
            .catch(error => {
                console.warn('Aboro Chat: Widget data load failed:', error.message);
                // Widget kann trotzdem funktionieren, nur ohne Server-Config
            });
        }
        
        setupMessageListener() {
            window.addEventListener('message', (event) => {
                // Sicherheitscheck: nur Nachrichten von chat host akzeptieren
                if (event.origin !== new URL(chatHost).origin) return;
                
                const { type, data } = event.data || {};
                
                switch (type) {
                    case 'chat_ready':
                        this.onChatReady();
                        break;
                    case 'chat_resize':
                        this.onChatResize(data);
                        break;
                    case 'chat_close':
                        this.close();
                        break;
                    case 'chat_new_message':
                        this.onNewMessage(data);
                        break;
                }
            });
        }
        
        createChatInterface() {
            if (this.chatInterface) return;
            
            // Erstelle eine direkte Chat-Oberfläche ohne iframe
            this.chatInterface = document.createElement('div');
            this.chatInterface.style.cssText = `
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                background: white;
            `;
            
            // Chat Header
            const header = document.createElement('div');
            header.style.cssText = `
                background: ${config.widgetColor};
                color: white;
                padding: 15px;
                font-weight: 600;
                text-align: center;
                flex-shrink: 0;
            `;
            header.textContent = 'Live Support';
            
            // Chat Messages Area
            this.messagesArea = document.createElement('div');
            this.messagesArea.style.cssText = `
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                background: #f8f9fa;
            `;
            
            // Chat Input Area
            const inputArea = document.createElement('div');
            inputArea.style.cssText = `
                padding: 15px;
                border-top: 1px solid #eee;
                background: white;
                flex-shrink: 0;
            `;
            
            // Message Input
            this.messageInput = document.createElement('input');
            this.messageInput.type = 'text';
            this.messageInput.placeholder = 'Nachricht eingeben...';
            this.messageInput.style.cssText = `
                width: calc(100% - 60px);
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 20px;
                outline: none;
                font-size: 14px;
            `;
            
            // Send Button
            const sendButton = document.createElement('button');
            sendButton.innerHTML = '📤';
            sendButton.style.cssText = `
                width: 50px;
                height: 40px;
                background: ${config.widgetColor};
                color: white;
                border: none;
                border-radius: 20px;
                margin-left: 10px;
                cursor: pointer;
                font-size: 16px;
            `;
            
            // Event Listeners
            sendButton.addEventListener('click', () => this.sendMessage());
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
            
            // Zusammenbauen
            inputArea.appendChild(this.messageInput);
            inputArea.appendChild(sendButton);
            
            this.chatInterface.appendChild(header);
            this.chatInterface.appendChild(this.messagesArea);
            this.chatInterface.appendChild(inputArea);
            
            this.container.appendChild(this.chatInterface);
            
            // Initialisiere Chat
            this.initializeChat();
        }
        
        initializeChat() {
            // Lade Chat-Daten ohne iframe
            this.addMessage('System', 'Verbinde mit Support...', false);
            
            // Starte Chat Session
            this.startChatSession().then(() => {
                this.addMessage('System', 'Chat bereit! Wie können wir Ihnen helfen?', false);
                this.messageInput.focus();
            }).catch(() => {
                this.addMessage('System', 'Verbindungsfehler. Bitte versuchen Sie es später erneut.', false);
            });
        }
        
        async startChatSession() {
            // Generiere Session-ID falls nicht vorhanden
            if (!this.sessionId) {
                this.sessionId = this.generateSessionId();
            }
            
            const response = await fetch(`${chatHost}/chat/api/start/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'include',
                mode: 'cors',
                body: JSON.stringify({
                    session_id: this.sessionId,
                    name: 'Website Besucher',
                    email: 'besucher@' + window.location.hostname,
                    message: 'Chat gestartet von ' + window.location.href,
                    page_url: window.location.href
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.sessionId = data.session_id;
                this.startMessagePolling();
                return true;
            }
            throw new Error(data.error || 'Chat start failed');
        }
        
        generateSessionId() {
            return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        }
        
        addMessage(sender, message, isFromUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.style.cssText = `
                margin-bottom: 10px;
                display: flex;
                ${isFromUser ? 'justify-content: flex-end;' : 'justify-content: flex-start;'}
            `;
            
            const messageBubble = document.createElement('div');
            messageBubble.style.cssText = `
                max-width: 80%;
                padding: 10px 15px;
                border-radius: 18px;
                font-size: 14px;
                ${isFromUser ? 
                    `background: ${config.widgetColor}; color: white; margin-left: 20%;` : 
                    'background: white; border: 1px solid #ddd; margin-right: 20%;'
                }
            `;
            messageBubble.textContent = message;
            
            messageDiv.appendChild(messageBubble);
            this.messagesArea.appendChild(messageDiv);
            this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
        }
        
        async sendMessage() {
            const message = this.messageInput.value.trim();
            if (!message || !this.sessionId) return;
            
            // Zeige Nachricht sofort
            this.addMessage('Sie', message, true);
            this.messageInput.value = '';
            
            try {
                const response = await fetch(`${chatHost}/chat/api/send/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    credentials: 'include',
                    mode: 'cors',
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        message: message
                    })
                });
                
                const data = await response.json();
                if (!data.success) {
                    this.addMessage('System', 'Fehler beim Senden der Nachricht', false);
                }
            } catch (error) {
                this.addMessage('System', 'Netzwerkfehler beim Senden', false);
            }
        }
        
        startMessagePolling() {
            if (this.pollInterval) return;
            
            this.pollInterval = setInterval(async () => {
                try {
                    const response = await fetch(`${chatHost}/chat/api/messages/${this.sessionId}/`, {
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                        },
                        credentials: 'include',
                        mode: 'cors'
                    });
                    const data = await response.json();
                    
                    if (data.success && data.messages) {
                        // Zeige nur neue Nachrichten
                        data.messages.forEach(msg => {
                            if (!this.processedMessages.has(msg.timestamp)) {
                                if (!msg.is_from_visitor) {
                                    this.addMessage(msg.sender_name || 'Support', msg.message, false);
                                }
                                this.processedMessages.add(msg.timestamp);
                            }
                        });
                    }
                } catch (error) {
                    console.error('Polling error:', error);
                }
            }, 3000);
        }
        
        // Iframe-Unterstützung entfernt - nur noch iframe-freie Lösung für maximale Kompatibilität
        
        toggle() {
            this.isOpen ? this.close() : this.open();
        }
        
        open() {
            // IMMER iframe-freie Lösung verwenden (Firefox-Kompatibilität)
            if (!this.chatInterface) {
                this.createChatInterface();
            }
            
            this.container.style.display = 'block';
            this.button.style.display = 'none';
            this.isOpen = true;
            
            // Animation
            this.container.style.opacity = '0';
            this.container.style.transform = 'scale(0.8)';
            
            requestAnimationFrame(() => {
                this.container.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                this.container.style.opacity = '1';
                this.container.style.transform = 'scale(1)';
            });
        }
        
        close() {
            this.container.style.opacity = '0';
            this.container.style.transform = 'scale(0.8)';
            
            setTimeout(() => {
                this.container.style.display = 'none';
                this.button.style.display = 'flex';
                this.isOpen = false;
            }, 300);
        }
        
        onChatReady() {
            // Chat iframe ist bereit
            console.log('Aboro Chat: Ready');
        }
        
        onChatResize(data) {
            // Dynamische Größenanpassung des Widgets
            if (data.width) this.container.style.width = data.width + 'px';
            if (data.height) this.container.style.height = data.height + 'px';
        }
        
        onNewMessage(data) {
            // Neue Nachricht erhalten - könnte für Notifications verwendet werden
            if (!this.isOpen && 'Notification' in window && Notification.permission === 'granted') {
                new Notification('Neue Chat-Nachricht', {
                    body: data.message || 'Sie haben eine neue Nachricht erhalten',
                    icon: `${chatHost}/static/images/logo.png`
                });
            }
        }
        
        // Public API
        destroy() {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
            }
            if (this.button) this.button.remove();
            if (this.container) this.container.remove();
            window.removeEventListener('message', this.setupMessageListener);
            window.AboroChatWidget = null;
        }
    }
    
    // Initialize widget when DOM is ready
    function initWidget() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                window.AboroChatWidget = new AboroChatWidget();
            });
        } else {
            window.AboroChatWidget = new AboroChatWidget();
        }
    }
    
    // Auto-initialize
    initWidget();
    
    // Global API
    window.AboroChat = {
        open: () => window.AboroChatWidget?.open(),
        close: () => window.AboroChatWidget?.close(),
        toggle: () => window.AboroChatWidget?.toggle(),
        destroy: () => window.AboroChatWidget?.destroy()
    };
    
})();