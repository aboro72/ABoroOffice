/**
 * ABoro-IT Pure Chat Widget - Iframe-freie Version
 * =================================================
 * 
 * 100% iframe-freie Implementierung für maximale Browser-Kompatibilität
 * Funktioniert in Firefox, Chrome, Safari, Edge ohne Cross-Origin-Probleme
 */

(function() {
    'use strict';
    
    // Prevent multiple initializations
    if (window.AboroPureChatWidget) return;
    
    // Configuration
    const config = window.AboroChatConfig || {
        chatHost: 'https://help.aboro-it.net',
        widgetColor: '#667eea',
        position: 'bottom-right',
        autoOpen: false,
        language: 'de'
    };
    
    class PureChatWidget {
        constructor() {
            this.isOpen = false;
            this.sessionId = null;
            this.container = null;
            this.button = null;
            this.messagesArea = null;
            this.messageInput = null;
            this.pollInterval = null;
            this.processedMessages = new Set();
            
            this.init();
        }
        
        init() {
            this.createButton();
            this.createContainer();
            this.sessionId = this.generateSessionId();
            
            // Auto-open if configured
            if (config.autoOpen) {
                setTimeout(() => this.open(), 2000);
            }
        }
        
        createButton() {
            this.button = document.createElement('div');
            this.button.innerHTML = '💬';
            this.setButtonStyles();
            this.button.addEventListener('click', () => this.toggle());
            document.body.appendChild(this.button);
        }
        
        setButtonStyles() {
            const position = config.position === 'bottom-left' ? 'left: 20px;' : 'right: 20px;';
            
            this.button.style.cssText = `
                position: fixed;
                bottom: 20px;
                ${position}
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
        
        createContainer() {
            const position = config.position === 'bottom-left' ? 'left: 20px;' : 'right: 20px;';
            
            this.container = document.createElement('div');
            this.container.style.cssText = `
                position: fixed;
                bottom: 90px;
                ${position}
                z-index: 9999;
                width: 350px;
                height: 500px;
                max-width: 90vw;
                max-height: 90vh;
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.2);
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                border: 1px solid #e0e0e0;
                display: none;
                flex-direction: column;
            `;
            
            // Create chat interface
            this.createChatInterface();
            document.body.appendChild(this.container);
        }
        
        createChatInterface() {
            // Chat Header
            const header = document.createElement('div');
            header.style.cssText = `
                background: ${config.widgetColor};
                color: white;
                padding: 15px;
                font-weight: 600;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-shrink: 0;
            `;
            
            const headerContent = document.createElement('div');
            headerContent.innerHTML = `
                <div style="font-size: 16px;">Live Support</div>
                <div style="font-size: 12px; opacity: 0.9;">Powered by ABoro-IT</div>
            `;
            
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '×';
            closeBtn.style.cssText = `
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            `;
            closeBtn.addEventListener('click', () => this.close());
            closeBtn.addEventListener('mouseenter', () => {
                closeBtn.style.background = 'rgba(255,255,255,0.2)';
            });
            closeBtn.addEventListener('mouseleave', () => {
                closeBtn.style.background = 'transparent';
            });
            
            header.appendChild(headerContent);
            header.appendChild(closeBtn);
            
            // Messages Area
            this.messagesArea = document.createElement('div');
            this.messagesArea.style.cssText = `
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                background: #f8f9fa;
            `;
            
            // Input Area
            const inputArea = document.createElement('div');
            inputArea.style.cssText = `
                padding: 15px;
                border-top: 1px solid #eee;
                background: white;
                flex-shrink: 0;
                display: flex;
                gap: 10px;
            `;
            
            this.messageInput = document.createElement('input');
            this.messageInput.type = 'text';
            this.messageInput.placeholder = 'Nachricht eingeben...';
            this.messageInput.style.cssText = `
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 20px;
                outline: none;
                font-size: 14px;
            `;
            
            const sendButton = document.createElement('button');
            sendButton.innerHTML = '📤';
            sendButton.style.cssText = `
                width: 40px;
                height: 40px;
                background: ${config.widgetColor};
                color: white;
                border: none;
                border-radius: 50%;
                cursor: pointer;
                font-size: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.2s;
            `;
            
            // Event listeners
            sendButton.addEventListener('click', () => this.sendMessage());
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
            
            sendButton.addEventListener('mouseenter', () => {
                sendButton.style.transform = 'scale(1.1)';
            });
            sendButton.addEventListener('mouseleave', () => {
                sendButton.style.transform = 'scale(1)';
            });
            
            inputArea.appendChild(this.messageInput);
            inputArea.appendChild(sendButton);
            
            this.container.appendChild(header);
            this.container.appendChild(this.messagesArea);
            this.container.appendChild(inputArea);
            
            // Initialize chat
            this.initializeChat();
        }
        
        initializeChat() {
            this.addMessage('System', 'Verbinde mit Support...', false, true);
            
            this.startChatSession().then(() => {
                this.addMessage('System', 'Chat bereit! Wie können wir Ihnen helfen?', false, true);
                this.messageInput.focus();
                this.startMessagePolling();
            }).catch((error) => {
                this.addMessage('System', 'Verbindungsfehler. Bitte versuchen Sie es später erneut.', false, true);
                console.error('Chat initialization error:', error);
            });
        }
        
        generateSessionId() {
            return 'pure_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        }
        
        async startChatSession() {
            try {
                const response = await fetch(`${config.chatHost}/chat/api/start/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    mode: 'cors',
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        name: 'Website Besucher',
                        email: 'besucher@' + window.location.hostname,
                        message: 'Chat gestartet von ' + window.location.href,
                        page_url: window.location.href
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                if (data.success) {
                    this.sessionId = data.session_id;
                    return true;
                } else {
                    throw new Error(data.error || 'Chat start failed');
                }
            } catch (error) {
                console.error('Start chat session error:', error);
                throw error;
            }
        }
        
        escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }

        addMessage(sender, message, isFromUser = false, isSystem = false) {
            const messageDiv = document.createElement('div');
            messageDiv.style.cssText = `
                margin-bottom: 12px;
                display: flex;
                ${isFromUser ? 'justify-content: flex-end;' : 'justify-content: flex-start;'}
            `;

            // First escape HTML, then convert \n to <br> for proper line breaks in display
            const escapedMessage = this.escapeHtml(message);
            const displayMessage = escapedMessage.replace(/\\n/g, '<br>');

            if (isSystem) {
                messageDiv.innerHTML = `
                    <div style="
                        background: #e9ecef;
                        color: #6c757d;
                        padding: 8px 12px;
                        border-radius: 15px;
                        font-size: 12px;
                        text-align: center;
                        width: 100%;
                        font-style: italic;
                    ">${displayMessage}</div>
                `;
            } else {
                const messageBubble = document.createElement('div');
                messageBubble.style.cssText = `
                    max-width: 80%;
                    padding: 10px 15px;
                    border-radius: 18px;
                    font-size: 14px;
                    word-wrap: break-word;
                    white-space: pre-wrap;
                    ${isFromUser ?
                        `background: ${config.widgetColor}; color: white; margin-left: 20%;` :
                        'background: white; border: 1px solid #ddd; margin-right: 20%; color: #333;'
                    }
                `;
                messageBubble.innerHTML = displayMessage;
                messageDiv.appendChild(messageBubble);
            }

            this.messagesArea.appendChild(messageDiv);
            this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
        }
        
        async sendMessage() {
            const message = this.messageInput.value.trim();
            if (!message || !this.sessionId) return;
            
            // Show message immediately
            this.addMessage('Sie', message, true);
            this.messageInput.value = '';
            
            try {
                const response = await fetch(`${config.chatHost}/chat/api/send/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    mode: 'cors',
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        message: message
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                if (!data.success) {
                    this.addMessage('System', 'Nachricht konnte nicht gesendet werden', false, true);
                }
            } catch (error) {
                console.error('Send message error:', error);
                this.addMessage('System', 'Verbindungsfehler beim Senden', false, true);
            }
        }
        
        startMessagePolling() {
            if (this.pollInterval) return;
            
            this.pollInterval = setInterval(async () => {
                try {
                    const response = await fetch(`${config.chatHost}/chat/api/messages/${this.sessionId}/`, {
                        mode: 'cors'
                    });
                    
                    if (!response.ok) return;
                    
                    const data = await response.json();
                    if (data.success && data.messages) {
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
        
        toggle() {
            this.isOpen ? this.close() : this.open();
        }
        
        open() {
            this.container.style.display = 'flex';
            this.button.style.display = 'none';
            this.isOpen = true;
            
            // Animation
            this.container.style.opacity = '0';
            this.container.style.transform = 'scale(0.8)';
            
            requestAnimationFrame(() => {
                this.container.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                this.container.style.opacity = '1';
                this.container.style.transform = 'scale(1)';
                
                if (this.messageInput) {
                    this.messageInput.focus();
                }
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
        
        destroy() {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
            }
            if (this.button) this.button.remove();
            if (this.container) this.container.remove();
            window.AboroPureChatWidget = null;
        }
    }
    
    // Initialize when DOM is ready
    function initWidget() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                window.AboroPureChatWidget = new PureChatWidget();
            });
        } else {
            window.AboroPureChatWidget = new PureChatWidget();
        }
    }
    
    // Auto-initialize
    initWidget();
    
    // Global API
    window.AboroChat = {
        open: () => window.AboroPureChatWidget?.open(),
        close: () => window.AboroPureChatWidget?.close(),
        toggle: () => window.AboroPureChatWidget?.toggle(),
        destroy: () => window.AboroPureChatWidget?.destroy()
    };
    
})();