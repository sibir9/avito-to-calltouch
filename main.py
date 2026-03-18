#!/usr/bin/env python3


import logging
from datetime import datetime
from src.avito_client import AvitoClient
from src.calltouch_client import CalltouchClient
from src.utils import StateManager, format_phone
from src.models import CalltouchCall
from config.config import Config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("="*50)
    logger.info("Запуск синхронизации Avito -> Calltouch")
    
    try:
        # Инициализация
        state_manager = StateManager(Config.STATE_FILE)
        avito = AvitoClient()
        calltouch = CalltouchClient()
        
        # Получаем время последней синхронизации
        
        last_sync = datetime(2026, 2, 1)  # берем с 1 февраля
        #last_sync = state_manager.get_last_sync()
        #if not last_sync:
            # Если синхронизации не было, берем последние 24 часа
            #last_sync = datetime.now().replace(hour=0, minute=0, second=0)
            #logger.info(f"Первая синхронизация, берем данные с {last_sync}")
        #else:
            #logger.info(f"Последняя синхронизация: {last_sync}")
        
        # Получаем новые звонки из Avito
        logger.info("Получаем звонки из Avito...")
        avito_calls = avito.get_calls_since(last_sync)
        logger.info(f"Найдено {len(avito_calls)} новых звонков")
        
        if not avito_calls:
            logger.info("Новых звонков нет")
            state_manager.set_last_sync(datetime.now())
            return
        
        # Преобразуем в формат Calltouch
        calltouch_calls = []
        for call in avito_calls:
            try:
                calltouch_call = CalltouchCall(
                    referenceId=call.id,
                    clientPhoneNumber=format_phone(call.client_phone),
                    callCenterPhoneNumber=format_phone(call.your_phone),
                    callStartTime=call.call_time.strftime("%Y-%m-%d %H:%M:%S"),
                    duration=call.duration,
                    waitingTime=0,  # Avito не передает время ожидания
                    status=call.status,
                    comment={"text": f"Объявление: {call.ad_title}"} if call.ad_title else None,
                    addTags=[{"tag": "Avito"}, {"tag": "Звонок с площадки"}],
                    customSources={
                        "source": "avito.ru",
                        "medium": "organic",
                        "campaign": call.ad_title or "Avito",
                        "content": call.ad_id or ""
                    }
                )
                calltouch_calls.append(calltouch_call)
            except Exception as e:
                logger.error(f"Ошибка при обработке звонка {call.id}: {e}")
        
        # Отправляем в Calltouch
        logger.info(f"Отправляем {len(calltouch_calls)} звонков в Calltouch...")
        result = calltouch.send_calls(calltouch_calls)
        
        logger.info(f"Результат отправки: {result}")
        
        # Обновляем время синхронизации
        state_manager.set_last_sync(datetime.now())
        logger.info("Синхронизация завершена успешно")
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
