"""
LLAMA3-Konfiguration für Django HelpDesk
Diese Datei kann in settings.py importiert werden
"""

# ==================================================
# LLAMA3 LOCAL AI CONFIGURATION
# ==================================================

# Aktiviere LLAMA3 lokale KI
USE_LLAMA3 = True

# LLAMA3-Modell (z.B. llama3.2-uncensored-3b, llama3:8b, llama3:3b)
# Empfehlung für Jetson Orin NX 16GB: kompaktere 3B-Varianten, z.B. llama3.2-uncensored-3b
LLAMA3_MODEL = 'llama3.2-uncensored-3b'

# Bevorzugter AI-Provider (llama3, claude, openai)
AI_PREFERRED_PROVIDER = 'llama3'

# ==================================================
# CLOUD API KEYS (Optional, als Fallback)
# ==================================================

# Claude API Key (optional, für Fallback)
# CLAUDE_API_KEY = 'dein-claude-api-key'

# OpenAI API Key (optional, für Fallback)
# OPENAI_API_KEY = 'dein-openai-api-key'

# ==================================================
# PERFORMANCE-EINSTELLUNGEN
# ==================================================

# Ollama Server URL (default: localhost)
OLLAMA_HOST = 'http://127.0.0.1:11434'

# Timeout für LLAMA3-Anfragen (in Sekunden)
LLAMA3_TIMEOUT = 30

# Max Tokens für Antworten
LLAMA3_MAX_TOKENS = 512

# Temperature (0.0-1.0)
# Niedrig (0.1-0.3): Deterministischer, schneller
# Hoch (0.7-0.9): Kreativer, variabler
LLAMA3_TEMPERATURE = 0.3

# ==================================================
# FEATURE-FLAGS
# ==================================================

# Automatische Ticket-Kategorisierung aktivieren
LLAMA3_AUTO_CATEGORIZE_TICKETS = True

# Automatische Prioritäts-Vorschläge aktivieren
LLAMA3_AUTO_SUGGEST_PRIORITY = True

# Chat-Auto-Response aktivieren
LLAMA3_CHAT_AUTO_RESPONSE = True

# Minimum Konfidenz für Auto-Kategorisierung (0.0-1.0)
LLAMA3_MIN_CONFIDENCE = 0.7

# ==================================================
# LOGGING
# ==================================================

# Logging für LLAMA3 aktivieren
LLAMA3_LOGGING_ENABLED = True

# Log-Level für LLAMA3 (DEBUG, INFO, WARNING, ERROR)
LLAMA3_LOG_LEVEL = 'INFO'

# ==================================================
# MULTI-PROVIDER KONFIGURATION
# ==================================================
"""
WICHTIG: Alle drei AI-Provider (LLAMA3, Claude, OpenAI) bleiben verfügbar!

Du kannst den bevorzugten Provider wählen:
    AI_PREFERRED_PROVIDER = 'llama3'  # Standard: Lokale KI
    AI_PREFERRED_PROVIDER = 'claude'  # Claude API
    AI_PREFERRED_PROVIDER = 'openai'  # OpenAI/ChatGPT API

LLAMA3 komplett deaktivieren:
    USE_LLAMA3 = False

Bei Fehlern fallback automatisch auf andere Provider:
    LLAMA3 (lokal) → Claude → OpenAI → Rule-based

Alle Provider funktionieren parallel - du entscheidest welcher bevorzugt wird!
"""

# ==================================================
# NUTZUNGS-ANLEITUNG
# ==================================================
"""
Um diese Einstellungen zu aktivieren, füge folgendes in settings.py ein:

# LLAMA3 Integration
try:
    from .settings_llama3 import *
    logger.info("LLAMA3 configuration loaded successfully")
except ImportError:
    logger.warning("LLAMA3 configuration not found")
    USE_LLAMA3 = False
"""
