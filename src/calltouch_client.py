import requests
import json
from typing import List, Dict
from config.config import Config
from src.models import CalltouchCall
import time

class CalltouchClient:
    def __init__(self):
        self.token = Config.CALLTOUCH_ACCESS_TOKEN
        self.site_id = Config.CALLTOUCH_SITE_ID
        self.url = Config.CALLTOUCH_API_URL
        self.headers = {
            "Access-Token": self.token,
            "SiteId": self.site_id,
            "Content-Type": "application/json"
        }
    
    def send_calls(self, calls: List[CalltouchCall]) -> Dict:
        """
        Отправляет звонки в Calltouch пачками
        """
        if not calls:
            return {"status": "no_calls", "message": "Нет звонков для отправки"}
        
        # Преобразуем в формат для API
        calls_data = []
        for call in calls:
            call_dict = {
                "referenceId": call.referenceId,
                "clientPhoneNumber": call.clientPhoneNumber,
                "callCenterPhoneNumber": call.callCenterPhoneNumber,
                "callStartTime": call.callStartTime,
                "duration": call.duration,
                "waitingTime": call.waitingTime,
                "status": call.status,
                "customSources": {
                    "source": "avito.ru",
                    "medium": "marketplace",
                    "campaign": "Звонки с Авито"
                }
            }
            
            if call.recordUrl:
                call_dict["recordUrl"] = call.recordUrl
            
            if call.comment:
                call_dict["comment"] = call.comment
            
            if call.addTags:
                call_dict["addTags"] = call.addTags
            
            calls_data.append(call_dict)
        
        # Отправляем пачками по 100 звонков
        results = []
        for i in range(0, len(calls_data), 100):
            batch = calls_data[i:i+100]
            payload = {"calls": batch}
            
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
