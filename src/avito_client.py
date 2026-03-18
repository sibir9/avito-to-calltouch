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
        Использует API: /messenger/v1/threads
        """
        try:
            print(f"💬 Запрашиваем чаты с {since_time}")
            
            # Получаем список чатов
            params = {
                "limit": 100,
                "offset": 0
            }
            
            response = self._make_request("GET", "/messenger/v1/threads", params=params)
            
            chats = []
            threads_list = response.get("threads", [])
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
                    client_phone = None
                    
                    for msg in chat_detail.get("messages", []):
                        text = msg.get("text", {}).get("markdown", "")
                        direction = "incoming" if msg.get("direction") == "in" else "outgoing"
                        
                        messages.append({
                            "text": text,
                            "time": msg["created"],
                            "direction": direction,
                            "author": msg.get("author", {}).get("name", "Неизвестно")
                        })
                        
                        # Пытаемся найти номер телефона в сообщениях клиента
                        if direction == "incoming" and not client_phone:
                            phones = re.findall(r"\+?7[0-9]{10}|8[0-9]{10}", text)
                            if phones:
                                client_phone = phones[0]
                    
                    # Получаем информацию об объявлении
                    ad_info = thread.get("context", {}).get("ad", {})
                    ad_id = str(ad_info.get("id", "")) if ad_info.get("id") else ""
                    ad_title = ad_info.get("title", "")
                    
                    # Если нет названия объявления, пробуем получить через API items
                    if ad_id and not ad_title:
                        try:
                            item_info = self._make_request("GET", f"/core/v1/items/{ad_id}")
                            ad_title = item_info.get("title", "")
                        except:
                            pass
                    
                    # Получаем первое сообщение для комментария
                    first_message = messages[0]["text"] if messages else ""
                    
                    chat = AvitoChat(
                        chat_id=str(thread["id"]),
                        client_name=thread.get("users", [{}])[0].get("name", "Неизвестно"),
                        client_phone=client_phone,
                        messages=messages,
                        ad_id=ad_id,
                        ad_title=ad_title,
                        created_time=last_msg_time,
                        first_message=first_message,
                        message_count=len(messages)
                    )
                    chats.append(chat)
                    print(f"  ✅ Чат {thread['id']}: {len(messages)} сообщений, клиент: {chat.client_name}")
                    
                except Exception as e:
                    print(f"  ⚠️ Ошибка при обработке чата {thread.get('id')}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            return chats
            
        except Exception as e:
            print(f"❌ Ошибка при получении чатов: {e}")
            return []

# Для обратной совместимости
AvitoClient = AvitoAPIClient
