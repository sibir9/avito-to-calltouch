import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    # Calltouch
    CALLTOUCH_ACCESS_TOKEN = os.getenv('CALLTOUCH_ACCESS_TOKEN')
    CALLTOUCH_SITE_ID = os.getenv('CALLTOUCH_SITE_ID')
    CALLTOUCH_API_URL = "https://api.calltouch.ru/lead-service/v1/api/call/import"
    
    # Avito
    AVITO_CLIENT_ID = os.getenv('AVITO_CLIENT_ID')
    AVITO_CLIENT_SECRET = os.getenv('AVITO_CLIENT_SECRET')
    AVITO_USER_ID = os.getenv('AVITO_USER_ID')
    
    # Настройки
    CHECK_INTERVAL_HOURS = int(os.getenv('CHECK_INTERVAL_HOURS', 1))
    STATE_FILE = "data/last_sync.json"
