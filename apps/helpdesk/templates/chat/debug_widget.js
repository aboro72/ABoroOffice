/**
 * ABoro-IT Chat Widget - Debug Version
 * ====================================
 * 
 * Debug version with extensive logging to diagnose Firefox issues
 */

(function() {
    'use strict';
    
    console.log('🔧 ABoro Debug Widget Loading...');
    console.log('🌐 Current URL:', window.location.href);
    console.log('📋 User Agent:', navigator.userAgent);
    console.log('🔍 Is Firefox:', navigator.userAgent.indexOf('Firefox') > -1);
    
    // Prevent multiple initializations
    if (window.AboroDebugChatWidget) {
        console.log('❌ Widget already initialized');
        return;
    }
    
    // Configuration with debugging
    const config = window.AboroChatConfig || {
        chatHost: 'https://help.aboro-it.net',
        widgetColor: '#667eea',
        position: 'bottom-right',
        autoOpen: false,
        language: 'de'
    };
    
    console.log('⚙️ Widget Config:', config);
    
    class DebugChatWidget {
        constructor() {
            console.log('🚀 Initializing Debug Chat Widget...');
            this.isOpen = false;
            this.sessionId = null;
            this.container = null;
            this.button = null;
            this.debugLog = [];
            
            this.init();
        }
        
        log(message, type = 'info') {
            const timestamp = new Date().toISOString();
            const logEntry = `[${timestamp}] ${type.toUpperCase()}: ${message}`;
            this.debugLog.push(logEntry);
            console.log(`🔧 ${logEntry}`);
        }
        
        init() {
            this.log('Creating button and container');
            this.createDebugButton();
            this.testCORS();
        }
        
        createDebugButton() {
            this.button = document.createElement('div');
            this.button.innerHTML = '🔧';
            this.button.title = 'ABoro Debug Chat Widget';
            this.setButtonStyles();
            this.button.addEventListener('click', () => this.showDebugInfo());
            document.body.appendChild(this.button);
            this.log('Debug button created');
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
                background: #ff6b6b;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: white;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                transition: all 0.3s ease;
                font-family: monospace;
                border: 2px solid #fff;
            `;
        }
        
        async testCORS() {
            this.log('Testing CORS connectivity with Firefox fixes');
            
            try {
                // Test 1: Simple GET request to widget data
                this.log('Test 1: Fetching widget data...');
                const response1 = await fetch(`${config.chatHost}/chat/widget-data/`, {
                    method: 'GET',
                    mode: 'cors',
                    credentials: 'omit', // Firefox-freundlich
                    headers: {
                        'Accept': 'application/json',
                    }
                });
                
                this.log(`Test 1 Result: Status ${response1.status}`, response1.ok ? 'success' : 'error');
                this.log(`Test 1 Headers: ${JSON.stringify([...response1.headers.entries()])}`);
                
                // Test 2: OPTIONS preflight request
                this.log('Test 2: Testing OPTIONS preflight...');
                const response2 = await fetch(`${config.chatHost}/chat/api/start/`, {
                    method: 'OPTIONS',
                    mode: 'cors',
                    credentials: 'omit',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                });
                
                this.log(`Test 2 Result: Status ${response2.status}`, response2.ok ? 'success' : 'error');
                this.log(`Test 2 Headers: ${JSON.stringify([...response2.headers.entries()])}`);
                
                // Test 3: Actual API call
                this.log('Test 3: Testing actual API call...');
                this.sessionId = 'debug_' + Math.random().toString(36).substr(2, 9);
                
                const response3 = await fetch(`${config.chatHost}/chat/api/start/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    mode: 'cors',
                    credentials: 'omit', // Firefox-freundlich
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        name: 'Debug Test Firefox',
                        email: 'debug@' + window.location.hostname,
                        message: 'Debug test from Firefox: ' + window.location.href,
                        page_url: window.location.href
                    })
                });
                
                this.log(`Test 3 Result: Status ${response3.status}`, response3.ok ? 'success' : 'error');
                this.log(`Test 3 Headers: ${JSON.stringify([...response3.headers.entries()])}`);
                
                if (response3.ok) {
                    const data = await response3.json();
                    this.log(`API Response: ${JSON.stringify(data)}`, 'success');
                    
                    // Test 4: Message polling
                    this.log('Test 4: Testing message polling...');
                    const response4 = await fetch(`${config.chatHost}/chat/api/messages/${this.sessionId}/`, {
                        method: 'GET',
                        mode: 'cors',
                        credentials: 'omit',
                        headers: {
                            'Accept': 'application/json'
                        }
                    });
                    
                    this.log(`Test 4 Result: Status ${response4.status}`, response4.ok ? 'success' : 'error');
                    
                    if (response4.ok) {
                        const messages = await response4.json();
                        this.log(`Messages: ${JSON.stringify(messages)}`, 'success');
                    }
                    
                } else {
                    const errorText = await response3.text();
                    this.log(`API Error: ${response3.statusText} - ${errorText}`, 'error');
                }
                
            } catch (error) {
                this.log(`CORS Test Error: ${error.message}`, 'error');
                this.log(`Error Stack: ${error.stack}`, 'error');
                this.log(`Error Name: ${error.name}`, 'error');
                this.log(`Error Constructor: ${error.constructor.name}`, 'error');
            }
        }
        
        showDebugInfo() {
            // Create debug modal
            if (document.getElementById('aboro-debug-modal')) {
                document.getElementById('aboro-debug-modal').remove();
            }
            
            const modal = document.createElement('div');
            modal.id = 'aboro-debug-modal';
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                z-index: 99999;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: monospace;
            `;
            
            const content = document.createElement('div');
            content.style.cssText = `
                background: white;
                padding: 30px;
                border-radius: 10px;
                max-width: 80%;
                max-height: 80%;
                overflow: auto;
                color: black;
            `;
            
            const logs = this.debugLog.join('\\n');
            content.innerHTML = `
                <h2>🔧 ABoro Chat Widget Debug Info</h2>
                <h3>Environment:</h3>
                <p><strong>URL:</strong> ${window.location.href}</p>
                <p><strong>Host:</strong> ${config.chatHost}</p>
                <p><strong>Browser:</strong> ${navigator.userAgent}</p>
                <p><strong>Is Firefox:</strong> ${navigator.userAgent.indexOf('Firefox') > -1 ? 'Yes' : 'No'}</p>
                
                <h3>Configuration:</h3>
                <pre>${JSON.stringify(config, null, 2)}</pre>
                
                <h3>Debug Log:</h3>
                <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; max-height: 300px; overflow: auto;">${logs}</pre>
                
                <button onclick="this.parentElement.parentElement.remove()" style="
                    background: #ff6b6b;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    margin-top: 15px;
                ">Close Debug</button>
                
                <button onclick="navigator.clipboard.writeText(document.querySelector('#aboro-debug-modal pre:last-of-type').textContent)" style="
                    background: #4ecdc4;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    margin-top: 15px;
                    margin-left: 10px;
                ">Copy Log</button>
            `;
            
            modal.appendChild(content);
            document.body.appendChild(modal);
            
            // Close on click outside
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });
        }
        
        destroy() {
            if (this.button) this.button.remove();
            this.log('Widget destroyed');
        }
    }
    
    // Initialize when DOM is ready
    function initWidget() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                window.AboroDebugChatWidget = new DebugChatWidget();
            });
        } else {
            window.AboroDebugChatWidget = new DebugChatWidget();
        }
    }
    
    // Auto-initialize
    initWidget();
    
    console.log('🔧 Debug Widget Setup Complete');
    
})();