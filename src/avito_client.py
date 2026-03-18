import requests
from datetime import datetime, timedelta
from typing import List, Optional
from src.models import AvitoCall, AvitoChat
from config.config import Config
import json

class AvitoClient:
    """
    Упрощенный клиент для Avito
    В реальности вам нужно будет реализовать получение данных
    через API Avito или парсинг
    """
    
    def __init__(self):
        # Здесь будут настройки для API Avito
        pass
    
    def get_calls_since(self, since_time: datetime) -> List[AvitoCall]:
        """
        Получает звонки из Avito с указанного времени
        ЭТО ДЕМО-ВЕРСИЯ - замените на реальное API
        """
        # TODO: Реализовать реальное получение звонков из Avito
        # Сейчас просто демо-данные
        demo_calls = []
        
        # Пример демо-звонка
        if datetime.now() - since_time < timedelta(hours=1):
            demo_calls.append(
                AvitoCall(
                    id=f"avito_call_{datetime.now().timestamp()}",
                    client_phone="71234567890",
                    your_phone="74951234567",
                    call_time=datetime.now(),
                    duration=120,
                    status="successful",
                    ad_id="123456",
                    ad_title="Продам квартиру"
                )
            )
        
        return demo_calls
    
    def get_chats_since(self, since_time: datetime) -> List[AvitoChat]:
        """
        Получает чаты из Avito с указанного времени
        ЭТО ДЕМО-ВЕРСИЯ - замените на реальное API
        """
        # TODO: Реализовать реальное получение чатов из Avito
        return []

### Файл `src/utils.py`
```python
import json
import os
from datetime import datetime
from typing import Optional

class StateManager:
    """Управляет состоянием последней синхронизации"""
    
    def __init__(self, state_file: str):
        self.state_file = state_file
        self._ensure_state_file()
    
    def _ensure_state_file(self):
        """Создает файл состояния, если его нет"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        if not os.path.exists(self.state_file):
            with open(self.state_file, 'w') as f:
                json.dump({"last_sync": None}, f)
    
    def get_last_sync(self) -> Optional[datetime]:
        """Возвращает время последней синхронизации"""
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                if data.get("last_sync"):
                    return datetime.fromisoformat(data["last_sync"])
        except:
            pass
        return None
    
    def set_last_sync(self, sync_time: datetime):
        """Сохраняет время синхронизации"""
        with open(self.state_file, 'w') as f:
            json.dump({"last_sync": sync_time.isoformat()}, f)

def format_phone(phone: str) -> str:
    """Приводит номер к формату 7xxxxxxxxxx"""
    # Убираем все кроме цифр
    digits = ''.join(filter(str.isdigit, phone))
    
    # Приводим к формату 7...
    if len(digits) == 10:
        return f"7{digits}"
    elif len(digits) == 11 and digits.startswith('8'):
        return f"7{digits[1:]}"
    elif len(digits) == 11 and digits.startswith('7'):
        return digits
    else:
        raise ValueError(f"Неверный формат номера: {phone}")
