import requests
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from src.models import AvitoCall, AvitoChat
from config.config import Config
import time
import base64

class AvitoAPIClient:
    """
    Клиент для работы с официальным API Avito
    Документация: https://api.avito.ru/docs
    """
    
    def __init__(self):
        self.client_id = Config.AVITO_CLIENT_ID
        self.client_secret = Config.AVITO_CLIENT_SECRET
        self.user_id = Config.AVITO_USER_ID
        self.access_token = None
        self.token_expires = None
        
    def _get_access_token(self) -> str:
        """
        Получает access token для API Avito
        Токен действителен 6 часов
        """
        if self.access_token and self.token_expires > datetime.now():
            return self.access_token
            
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id
        }
        
        response = requests.post(
            "https://api.avito.ru/token",
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            # Токен действителен 6 часов (21600 секунд)
            self.token_expires = datetime.now() + timedelta(seconds=token_data["expires_in"] - 60)
            return self.access_token
        else:
            raise Exception(f"Ошибка получения токена Avito: {response.text}")
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Универсальный метод для запросов к API Avito
        """
        token = self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.avito.ru{endpoint}"
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # Превышен лимит запросов
            time.sleep(60)
            return self._make_request(method, endpoint, params, data)
        else:
            raise Exception(f"Ошибка API Avito: {response.status_code} - {response.text}")
    
    def get_calls_since(self, since_time: datetime) -> List[AvitoCall]:
        """
        Получает звонки из Avito с указанного времени
        Использует API: /api/1/calls/
        """
        try:
            # Форматируем дату для API
            date_from = since_time.strftime("%Y-%m-%d")
            
            # Получаем список звонков
            params = {
                "date_from": date_from,
                "page": 1,
                "per_page": 100
            }
            
            response = self._make_request("GET", "/api/1/calls/", params=params)
            
            calls = []
            for item in response.get("calls", []):
                # Парсим время звонка
                call_time = datetime.fromisoformat(item["call_time"].replace("Z", "+00:00"))
                
                # Проверяем, что звонок новее since_time
                if call_time <= since_time:
                    continue
                
                call = AvitoCall(
                    id=str(item["id"]),
                    client_phone=item["caller_number"],
                    your_phone=item["called_number"],
                    call_time=call_time,
                    duration=item["duration"],
                    status="successful" if item["is_successful"] else "unsuccessful",
                    ad_id=str(item.get("ad_id", "")),
                    ad_title=item.get("ad_title", ""),
                    record_url=item.get("record_url")
                )
                calls.append(call)
            
            return calls
            
        except Exception as e:
            print(f"Ошибка при получении звонков: {e}")
            return []
    
    def get_chats_since(self, since_time: datetime) -> List[AvitoChat]:
        """
        Получает чаты из Avito с указанного времени
        Использует API: /messenger/v1/threads
        """
        try:
            # Получаем список чатов
            params = {
                "limit": 100,
                "offset": 0
            }
            
            response = self._make_request("GET", "/messenger/v1/threads", params=params)
            
            chats = []
            for thread in response.get("threads", []):
                # Получаем время последнего сообщения
                last_msg_time = datetime.fromisoformat(
                    thread["last_message"]["created"].replace("Z", "+00:00")
                )
                
                if last_msg_time <= since_time:
                    continue
                
                # Получаем детали чата
                chat_detail = self._make_request(
                    "GET", 
                    f"/messenger/v1/threads/{thread['id']}"
                )
                
                # Извлекаем сообщения
                messages = []
                for msg in chat_detail.get("messages", []):
                    messages.append({
                        "text": msg.get("text", {}).get("markdown", ""),
                        "time": msg["created"],
                        "direction": "incoming" if msg["direction"] == "in" else "outgoing",
                        "author": msg.get("author", {}).get("name", "Неизвестно")
                    })
                
                # Пробуем получить номер телефона (если клиент его оставил)
                client_phone = None
                for msg in messages:
                    if "8" in msg["text"] or "+7" in msg["text"]:
                        # Простой поиск номера в тексте
                        import re
                        phones = re.findall(r"\+?7[0-9]{10}|8[0-9]{10}", msg["text"])
                        if phones:
                            client_phone = phones[0]
                            break
                
                chat = AvitoChat(
                    chat_id=str(thread["id"]),
                    client_name=thread.get("users", [{}])[0].get("name", "Неизвестно"),
                    client_phone=client_phone,
                    messages=messages,
                    ad_id=str(thread.get("context", {}).get("ad", {}).get("id", "")),
                    ad_title=thread.get("context", {}).get("ad", {}).get("title", ""),
                    created_time=last_msg_time
                )
                chats.append(chat)
            
            return chats
            
        except Exception as e:
            print(f"Ошибка при получении чатов: {e}")
            return []

# Для обратной совместимости
AvitoClient = AvitoAPIClient
