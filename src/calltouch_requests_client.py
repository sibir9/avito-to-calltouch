import requests
import json
from typing import List, Dict
from config.config import Config
from src.models import CalltouchRequest
import time

class CalltouchRequestsClient:
    """
    Клиент для отправки заявок в Calltouch через API
    Документация: https://api.calltouch.ru/lead-service/v1/api/request/create
    """
    
    def __init__(self):
        self.token = Config.CALLTOUCH_ACCESS_TOKEN
        self.site_id = Config.CALLTOUCH_SITE_ID
        # ПРАВИЛЬНЫЙ URL для создания заявок
        self.url = "https://api.calltouch.ru/lead-service/v1/api/request/create"
        self.headers = {
            "Access-Token": self.token,
            "SiteId": self.site_id,
            "Content-Type": "application/json"
        }
        print(f"🔧 CalltouchRequestsClient инициализирован")
        print(f"   URL: {self.url}")
        print(f"   SiteId: {self.site_id}")
    
    def send_requests(self, requests_data: List[CalltouchRequest]) -> Dict:
        """
        Отправляет заявки в Calltouch пачками
        """
        if not requests_data:
            return {"status": "no_requests", "message": "Нет заявок для отправки"}
        
        print(f"📤 Подготовлено заявок: {len(requests_data)}")
        
        # Преобразуем в формат для API согласно документации
        requests_list = []
        for req in requests_data:
            req_dict = {
                "requestNumber": req.requestId,  # Важно: используется requestNumber, а не requestId
                "phoneNumber": req.phone if req.phone else "",
                "fio": req.userName if req.userName else "",
                "comment": {
                    "text": req.comment
                },
                "addTags": [
                    {"tag": "Avito"},
                    {"tag": "Чат"}
                ]
            }
            
            # Добавляем источник
            if req.source:
                if "customSources" not in req_dict:
                    req_dict["customSources"] = {}
                req_dict["customSources"]["source"] = req.source
                req_dict["customSources"]["medium"] = req.medium
                if req.campaign:
                    req_dict["customSources"]["campaign"] = req.campaign
                if req.content:
                    req_dict["customSources"]["content"] = req.content
            
            # Добавляем пользовательские поля
            if req.customFields:
                req_dict["customFields"] = req.customFields
            
            requests_list.append(req_dict)
        
        # Отправляем пачками по 100 заявок
        results = []
        for i in range(0, len(requests_list), 100):
            batch = requests_list[i:i+100]
            payload = {"requests": batch}
            
            print(f"\n📦 Отправка пачки {i//100 + 1} из {(len(requests_list)-1)//100 + 1}")
            print(f"   Кол-во заявок: {len(batch)}")
            
            try:
                response = requests.post(
                    self.url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                print(f"   Статус ответа: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Успешно: {json.dumps(result, indent=2, ensure_ascii=False)[:200]}")
                    results.append({
                        "batch": i//100 + 1,
                        "success": True,
                        "response": result
                    })
                else:
                    error_text = response.text
                    print(f"   ❌ Ошибка: {error_text}")
                    results.append({
                        "batch": i//100 + 1,
                        "success": False,
                        "error": error_text
                    })
                
                # Не превышаем лимит 5 запросов в секунду
                time.sleep(0.2)
                
            except Exception as e:
                print(f"   ❌ Исключение: {e}")
                results.append({
                    "batch": i//100 + 1,
                    "success": False,
                    "error": str(e)
                })
        
        return {"status": "completed", "results": results}
