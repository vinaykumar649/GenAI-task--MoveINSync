import os

class Config:
    MODE = 'pure_genai'
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    CORS_ENABLED = os.getenv('CORS_ENABLED', 'True') == 'True'
    
    API_BASE64_DELIMITER = 'base64,'
    
    DEFAULT_RESPONSE = "I'm not sure how to help with that."
    
    SPEECH_TO_TEXT_ERROR = 'Speech recognition not implemented in pure GenAI mode'
    TEXT_TO_SPEECH_ERROR = 'TTS not implemented in pure GenAI mode'
    
    HEALTH_STATUS = 'healthy'
    
    STARTUP_MESSAGES = [
        "=" * 60,
        f">> Movi Backend Server - {MODE.upper()} Mode",
        "=" * 60,
        "[OK] No OpenAI API required",
        "[OK] Rule-based intelligent agent",
        "[OK] Context-aware responses",
        "[OK] Database-driven (no hardcoding)",
        "\nAvailable endpoints:",
        "  POST /chat - Main Movi chat interface",
        "  GET  /health - Health check",
        "  GET  /api/vehicles - Get all vehicles",
        "  GET  /api/drivers - Get all drivers",
        "  GET  /api/trips - Get all trips",
        "  GET  /api/stops - Get all stops",
        "  GET  /api/paths - Get all paths",
        "  GET  /api/routes - Get all routes",
        "  GET  /api/deployments - Get all deployments",
        "=" * 60
    ]
    
    ENDPOINTS = {
        'CHAT': '/chat',
        'SPEECH_TO_TEXT': '/speech-to-text',
        'TEXT_TO_SPEECH': '/text-to-speech',
        'HEALTH': '/health',
        'VEHICLES': '/api/vehicles',
        'DRIVERS': '/api/drivers',
        'TRIPS': '/api/trips',
        'STOPS': '/api/stops',
        'PATHS': '/api/paths',
        'ROUTES': '/api/routes',
        'DEPLOYMENTS': '/api/deployments'
    }

config = Config()
