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

def setup_logging():
    """Настройка логирования"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/sync.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)
