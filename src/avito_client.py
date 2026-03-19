import requests
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from src.models import AvitoCall, AvitoChat
from config.config import Config
import time
import base64
import re

class AvitoAPIClient:
    """
    Клиент для работы с официальным API Avito
    Использует CallTracking API для получения звонков и Messenger API для чатов
    Документация: https://api.avito.ru/docs/
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
            timeout=60
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
        Использует CallTracking API: /calltracking/v1/getCalls/
        """
        try:
            # Форматируем время в RFC3339 формат
            date_from = since_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            date_to = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            
            print(f"📞 Запрашиваем звонки с {date_from} по {date_to}")
            
            # Подготавливаем запрос
            payload = {
                "dateTimeFrom": date_from,
                "dateTimeTo": date_to,
                "limit": 100,
                "offset": 0
            }
            
            # Получаем звонки
            response = self._make_request(
                "POST", 
                "/calltracking/v1/getCalls/",
                data=payload
            )
            
            calls = []
            
            # Обрабатываем ответ
            if "calls" in response:
                for item in response["calls"]:
                    try:
                        # Парсим время звонка
                        call_time = datetime.fromisoformat(item["callTime"].replace("Z", "+00:00"))
                        
                        print(f"  📞 Обработка звонка {item.get('callId')}: buyer={item.get('buyerPhone')}, duration={item.get('talkDuration')}")
                        
                        # Преобразуем в нашу модель
                        call = AvitoCall(
                            id=str(item["callId"]),
                            client_phone=item.get("buyerPhone", ""),
                            your_phone=item.get("virtualPhone", ""),
                            call_time=call_time,
                            duration=item.get("talkDuration", 0),
                            waitingTime=item.get("waitingDuration", 0),
                            status="successful" if item.get("talkDuration", 0) > 0 else "unsuccessful",
                            ad_id=str(item.get("itemId", "")) if item.get("itemId") else None,
                            ad_title="",  # Название объявления нужно получать отдельно
                            record_url=f"https://api.avito.ru/calltracking/v1/getRecordByCallId/?callId={item['callId']}" if item.get("callId") else None
                        )
                        calls.append(call)
                        print(f"    ✅ Добавлен звонок {call.id}")
                        
                    except Exception as e:
                        print(f"    ⚠️ Ошибка при обработке звонка {item.get('callId')}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
            
            # Если есть ошибка в ответе
            if "error" in response and response["error"]:
                print(f"⚠️ Ошибка от API: {response['error']}")
            
            print(f"📊 Получено звонков: {len(calls)}")
            return calls
            
        except Exception as e:
            print(f"❌ Ошибка при получении звонков: {e}")
            return []
    
    def get_call_details(self, call_id: int) -> Optional[Dict]:
        """
        Получает детальную информацию о звонке
        """
        try:
            payload = {"callId": call_id}
            response = self._make_request(
                "POST",
                "/calltracking/v1/getCallById/",
                data=payload
            )
            return response.get("call")
        except Exception as e:
            print(f"❌ Ошибка при получении деталей звонка {call_id}: {e}")
            return None
    
    def get_chats_since(self, since_time: datetime) -> List[AvitoChat]:
        """
        Получает чаты из Avito с указанного времени
        Использует Messenger API v2: /messenger/v2/accounts/{user_id}/chats
        """
        try:
            if not self.user_id:
                print("❌ ОШИБКА: AVITO_USER_ID не указан в конфигурации!")
                print("   Добавьте AVITO_USER_ID в файл .env")
                return []
                
            print(f"💬 Запрашиваем чаты для пользователя {self.user_id} с {since_time}")
            
            # Получаем список чатов через V2 API
            params = {
                "limit": 100,
                "offset": 0
            }
            
            response = self._make_request(
                "GET", 
                f"/messenger/v2/accounts/{self.user_id}/chats",
                params=params
            )
            
            chats = []
            threads_list = response.get("chats", [])
            print(f"💬 Найдено чатов: {len(threads_list)}")
            
            for thread in threads_list:
                try:
                    # Получаем время последнего обновления чата
                    # Avito возвращает Unix timestamp (число секунд)
                    if thread.get("updated"):
                        # Если это число (timestamp)
                        if isinstance(thread["updated"], (int, float)) or str(thread["updated"]).isdigit():
                            updated_time = datetime.fromtimestamp(int(thread["updated"]))
                        else:
                            # Если это строка ISO формата
                            updated_time = datetime.fromisoformat(str(thread["updated"]).replace("Z", "+00:00"))
                    elif thread.get("created"):
                        if isinstance(thread["created"], (int, float)) or str(thread["created"]).isdigit():
                            updated_time = datetime.fromtimestamp(int(thread["created"]))
                        else:
                            updated_time = datetime.fromisoformat(str(thread["created"]).replace("Z", "+00:00"))
                    else:
                        # Если нет времени, пропускаем
                        continue
                    
                    # Проверяем, что чат обновлялся после последней синхронизации
                    if updated_time <= since_time:
                        continue
                    
                    chat_id = thread["id"]
                    
                    # Получаем все сообщения чата
                    messages = self._get_chat_messages(chat_id)
                    
                    # Извлекаем информацию о пользователях
                    users = thread.get("users", [])
                    client_info = next((u for u in users if u.get("id") != int(self.user_id)), {})
                    client_name = client_info.get("name", "Неизвестно")
                    
                    # Получаем информацию об объявлении из контекста
                    context = thread.get("context", {})
                    ad_info = {}
                    if context.get("type") == "item":
                        ad_info = context.get("value", {})
                    
                    ad_id = str(ad_info.get("id", "")) if ad_info.get("id") else ""
                    ad_title = ad_info.get("title", "")
                    
                    # Если нет названия объявления, пробуем получить через API items
                    if ad_id and not ad_title:
                        try:
                            item_info = self._make_request("GET", f"/core/v1/items/{ad_id}")
                            ad_title = item_info.get("title", "")
                        except:
                            pass
                    
                    # Пытаемся найти номер телефона в сообщениях
                    client_phone = None
                    first_message = ""
                    
                    for msg in messages:
                        if not first_message:
                            first_message = msg.get("text", "")
                        
                        # Ищем телефон в сообщениях от клиента
                        if msg.get("direction") == "in":
                            text = msg.get("text", "")
                            phones = re.findall(r"\+?7[0-9]{10}|8[0-9]{10}", text)
                            if phones and not client_phone:
                                client_phone = phones[0]
                    
                    chat = AvitoChat(
                        chat_id=chat_id,
                        client_name=client_name,
                        client_phone=client_phone,
                        messages=messages,
                        ad_id=ad_id,
                        ad_title=ad_title,
                        created_time=updated_time,
                        first_message=first_message,
                        message_count=len(messages)
                    )
                    chats.append(chat)
                    print(f"  ✅ Чат {chat_id}: {len(messages)} сообщений, клиент: {client_name}, время: {updated_time}")
                    
                except Exception as e:
                    print(f"  ⚠️ Ошибка при обработке чата {thread.get('id')}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            return chats
            
        except Exception as e:
            print(f"❌ Ошибка при получении чатов: {e}")
            return []
    
    def _get_chat_messages(self, chat_id: str, limit: int = 100) -> List[dict]:
        """
        Получает все сообщения чата через V3 API
        """
        try:
            messages = []
            offset = 0
            
            while True:
                params = {
                    "limit": min(100, limit),
                    "offset": offset
                }
                
                response = self._make_request(
                    "GET",
                    f"/messenger/v3/accounts/{self.user_id}/chats/{chat_id}/messages/",
                    params=params
                )
                
                batch = response if isinstance(response, list) else response.get("messages", [])
                messages.extend(batch)
                
                if len(batch) < 100:
                    break
                    
                offset += 100
                
            # Преобразуем в удобный формат
            formatted_messages = []
            for msg in messages:
                content = msg.get("content", {})
                text = ""
                if "text" in content:
                    text = content["text"]
                elif "image" in content:
                    text = "[Изображение]"
                
                # Определяем направление сообщения
                direction = "in"
                if msg.get("author_id") == int(self.user_id):
                    direction = "out"
                
                formatted_messages.append({
                    "id": msg["id"],
                    "text": text,
                    "time": msg.get("created", ""),
                    "direction": direction,
                    "author_id": msg.get("author_id"),
                    "is_read": msg.get("is_read", False)
                })
            
            return formatted_messages
            
        except Exception as e:
            print(f"⚠️ Ошибка при получении сообщений чата {chat_id}: {e}")
            return []

# Для обратной совместимости
AvitoClient = AvitoAPIClient
