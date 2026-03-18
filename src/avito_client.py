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
        Токен действителен 24 часа (86400 секунд)
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
            # Токен действителен 24 часа (86400 секунд)
            self.token_expires = datetime.now() + timedelta(seconds=token_data["expires_in"] - 60)
            print(f"✅ Получен новый токен, действителен до: {self.token_expires}")
            return self.access_token
        else:
            raise Exception(f"Ошибка получения токена Avito: {response.status_code} - {response.text}")
    
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
        
        print(f"Запрос к: {url}")
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # Превышен лимит запросов
            print("⚠️ Превышен лимит запросов, ждем 60 секунд...")
            time.sleep(60)
            return self._make_request(method, endpoint, params, data)
        elif response.status_code == 401:
            print("❌ Ошибка авторизации, пробуем обновить токен...")
            self.access_token = None
            self.token_expires = None
            return self._make_request(method, endpoint, params, data)
        else:
            raise Exception(f"Ошибка API Avito: {response.status_code} - {response.text}")
    
    def get_calls_since(self, since_time: datetime) -> List[AvitoCall]:
        """
        Получает звонки из Avito с указанного времени
        Использует API статистики: /core/v1/stats/items/
        """
        try:
            # Сначала получим информацию о пользователе
            user_info = self._make_request("GET", "/core/v1/accounts/self")
            print(f"👤 Аккаунт: {user_info.get('name', 'Неизвестно')}")
            
            # Получим список объявлений
            items = self._make_request("GET", "/core/v1/items", params={"limit": 100})
            
            calls = []
            
            # Форматируем даты для запроса статистики
            date_from = since_time.strftime("%Y-%m-%d")
            date_to = datetime.now().strftime("%Y-%m-%d")
            
            # Получаем статистику по каждому объявлению
            items_list = items.get("items", []) or items.get("resources", [])
            print(f"📦 Найдено объявлений: {len(items_list)}")
            
            for item in items_list:
                item_id = item.get("id")
                if not item_id:
                    continue
                    
                # Получаем статистику по объявлению
                try:
                    stats = self._make_request(
                        "GET", 
                        f"/core/v1/stats/items/{item_id}",
                        params={
                            "date_from": date_from,
                            "date_to": date_to
                        }
                    )
                    
                    # В статистике ищем данные о звонках
                    # Структура может отличаться, нужно посмотреть реальный ответ
                    print(f"📊 Статистика для объявления {item_id}: {list(stats.keys())}")
                    
                    # TODO: Обработать статистику согласно реальной структуре ответа
                    
                except Exception as e:
                    print(f"⚠️ Ошибка при получении статистики для {item_id}: {e}")
                    continue
            
            return calls
            
        except Exception as e:
            print(f"❌ Ошибка при получении звонков: {e}")
            return []
    
    def get_chats_since(self, since_time: datetime) -> List[AvitoChat]:
        """
        Получает чаты из Avito с указанного времени
        Использует API: /messenger/v1/threads
        """
        try:
            # Проверяем доступ к мессенджеру
            threads = self._make_request("GET", "/messenger/v1/threads", params={"limit": 100})
            
            chats = []
            threads_list = threads.get("threads", [])
            print(f"💬 Найдено чатов: {len(threads_list)}")
            
            for thread in threads_list:
                try:
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
                            "direction": "incoming" if msg.get("direction") == "in" else "outgoing",
                            "author": msg.get("author", {}).get("name", "Неизвестно")
                        })
                    
                    # Пробуем получить номер телефона (если клиент его оставил)
                    client_phone = None
                    import re
                    for msg in messages:
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
                    
                except Exception as e:
                    print(f"⚠️ Ошибка при обработке чата {thread.get('id')}: {e}")
                    continue
            
            return chats
            
        except Exception as e:
            print(f"❌ Ошибка при получении чатов: {e}")
            return []

# Для обратной совместимости
AvitoClient = AvitoAPIClient
