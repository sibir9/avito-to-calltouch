#!/usr/bin/env python3
"""
Скрипт для дозагрузки исторических звонков за указанный период
"""
import logging
from datetime import datetime, timedelta
from src.avito_client import AvitoClient
from src.calltouch_client import CalltouchClient
from src.utils import format_phone
from src.models import CalltouchCall

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def backfill_calls(start_date, end_date):
    """
    Загружает звонки за период с start_date по end_date
    """
    logger.info(f"🚀 Запуск исторической загрузки звонков с {start_date} по {end_date}")
    
    avito = AvitoClient()
    calltouch = CalltouchClient()
    
    current_date = start_date
    total_calls = 0
    
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        
        logger.info(f"📅 Загружаем звонки за {current_date.strftime('%Y-%m-%d')}")
        
        # Получаем звонки за конкретный день
        avito_calls = avito.get_calls_since(current_date)
        
        # Фильтруем только звонки за этот день
        day_calls = [
            call for call in avito_calls 
            if current_date.date() <= call.call_time.date() < next_date.date()
        ]
        
        if day_calls:
            logger.info(f"  Найдено {len(day_calls)} звонков")
            
            # Преобразуем и отправляем
            calltouch_calls = []
            for call in day_calls:
                try:
                    calltouch_call = CalltouchCall(
                        referenceId=f"{call.id}_{current_date.strftime('%Y%m%d')}",
                        clientPhoneNumber=format_phone(call.client_phone),
                        callCenterPhoneNumber=format_phone(call.your_phone),
                        callStartTime=call.call_time.strftime("%Y-%m-%d %H:%M:%S"),
                        duration=call.duration,
                        waitingTime=0,
                        status=call.status,
                        addTags=[{"tag": "Avito"}, {"tag": "Звонок с площадки"}, {"tag": "Исторический"}],
                        customSources={
                            "source": "avito.ru",
                            "medium": "marketplace",
                            "campaign": call.ad_title or "Avito",
                            "content": call.ad_id or ""
                        }
                    )
                    calltouch_calls.append(calltouch_call)
                except Exception as e:
                    logger.error(f"Ошибка при обработке звонка {call.id}: {e}")
            
            # Отправляем в Calltouch
            result = calltouch.send_calls(calltouch_calls)
            logger.info(f"  Результат: {result}")
            total_calls += len(day_calls)
        else:
            logger.info(f"  Звонков не найдено")
        
        current_date = next_date
    
    logger.info(f"✅ Историческая загрузка завершена. Всего загружено: {total_calls} звонков")

if __name__ == "__main__":
    # Укажи нужный период
    start = datetime(2026, 3, 18)  # с 18 марта
    end = datetime(2026, 3, 19)    # по 19 марта
    
    backfill_calls(start, end)
