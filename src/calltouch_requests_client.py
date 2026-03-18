import requests
import json
from typing import List, Dict
from config.config import Config
from src.models import CalltouchRequest
import time

class CalltouchRequestsClient:
    """
    Клиент для отправки заявок в Calltouch через API
    Документация: https://api.calltouch.ru/lead-service/v1/api/request/import
    """
    
    def __init__(self):
        self.token = Config.CALLTOUCH_ACCESS_TOKEN
        self.site_id = Config.CALLTOUCH_SITE_ID
        self.url = "https://api.calltouch.ru/lead-service/v1/api/request/import"
        self.headers = {
            "Access-Token": self.token,
            "SiteId": self.site_id,
            "Content-Type": "application/json"
        }
    
    def send_requests(self, requests_data: List[CalltouchRequest]) -> Dict:
        """
        Отправляет заявки в Calltouch пачками
        """
        if not requests_data:
            return {"status": "no_requests", "message": "Нет заявок для отправки"}
        
        # Преобразуем в формат для API
        requests_list = []
        for req in requests_data:
            req_dict = {
                "requestId": req.requestId,
                "phone": req.phone,
                "userName": req.userName,
                "comment": req.comment,
                "source": req.source,
                "medium": req.medium,
                "campaign": req.campaign,
                "content": req.content
            }
            
            if req.customFields:
                req_dict["customFields"] = req.customFields
            
            requests_list.append(req_dict)
        
        # Отправляем пачками по 100 заявок
        results = []
        for i in range(0, len(requests_list), 100):
            batch = requests_list[i:i+100]
            payload = {"requests": batch}
            
            try:
                response = requests.post(
                    self.url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "batch": i//100 + 1,
                        "success": True,
                        "logId": result.get("data", {}).get("logId")
                    })
                else:
                    results.append({
                        "batch": i//100 + 1,
                        "success": False,
                        "error": response.text
                    })
                
                # Не превышаем лимит 5 запросов в секунду
                time.sleep(0.2)
                
            except Exception as e:
                results.append({
                    "batch": i//100 + 1,
                    "success": False,
                    "error": str(e)
                })
        
        return {"status": "completed", "results": results}
