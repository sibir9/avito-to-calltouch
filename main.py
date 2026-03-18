#!/usr/bin/env python3

import logging
from datetime import datetime
from src.avito_client import AvitoClient
from src.calltouch_client import CalltouchClient
from src.calltouch_requests_client import CalltouchRequestsClient
from src.utils import StateManager, format_phone
from src.models import CalltouchCall, CalltouchRequest
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

def process_calls(state_manager, avito, calltouch):
    """Обработка звонков"""
    logger.info("="*50)
    logger.info("Обработка звонков")
    
    # Получаем время последней синхронизации звонков
    last_sync = state_manager.get_last_sync()
    if not last_sync:
        last_sync = datetime.now().replace(hour=0, minute=0, second=0)
        logger.info(f"Первая синхронизация звонков, берем данные с {last_sync}")
    else:
        logger.info(f"Последняя синхронизация звонков: {last_sync}")
    
    # Получаем новые звонки из Avito
    logger.info("Получаем звонки из Avito...")
    avito_calls = avito.get_calls_since(last_sync)
    logger.info(f"Найдено {len(avito_calls)} новых звонков")
    
    if avito_calls:
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
                    waitingTime=0,
                    status=call.status,
                    comment={"text": f"Объявление: {call.ad_title}"} if call.ad_title else None,
                    addTags=[{"tag": "Avito"}, {"tag": "Звонок с площадки"}],
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
        logger.info(f"Отправляем {len(calltouch_calls)} звонков в Calltouch...")
        result = calltouch.send_calls(calltouch_calls)
        logger.info(f"Результат отправки звонков: {result}")
    
    # Обновляем время синхронизации звонков
    state_manager.set_last_sync(datetime.now())
    return len(avito_calls)

def process_chats(chats_state_manager, avito, requests_client):
    """Обработка чатов"""
    logger.info("="*50)
    logger.info("Обработка чатов")
    
    # Получаем время последней синхронизации чатов
    last_sync = chats_state_manager.get_last_sync()
    if not last_sync:
        last_sync = datetime.now().replace(hour=0, minute=0, second=0)
        logger.info(f"Первая синхронизация чатов, берем данные с {last_sync}")
    else:
        logger.info(f"Последняя синхронизация чатов: {last_sync}")
    
    # Получаем новые чаты из Avito
    logger.info("Получаем чаты из Avito...")
    avito_chats = avito.get_chats_since(last_sync)
    logger.info(f"Найдено {len(avito_chats)} новых чатов")
    
    if avito_chats:
        # Преобразуем в формат заявок Calltouch
        calltouch_requests = []
        for chat in avito_chats:
            try:
                # Создаем теги для чата
                tags = [{"tag": "Avito"}, {"tag": "Чат"}]
                if chat.client_phone:
                    tags.append({"tag": "Есть телефон"})
                
                # Создаем заявку
                request_data = CalltouchRequest(
                    requestId=chat.chat_id,
                    phone=format_phone(chat.client_phone) if chat.client_phone else None,
                    userName=chat.client_name,
                    comment=f"Чат с Avito\nОбъявление: {chat.ad_title}\nСообщений: {chat.message_count}\nПервое сообщение: {chat.first_message}",
                    source="avito.ru",
                    medium="marketplace",
                    campaign=chat.ad_title or "Avito",
                    content=chat.ad_id,
                    customFields=[
                        {"field": "chat_id", "value": chat.chat_id},
                        {"field": "message_count", "value": str(chat.message_count)},
                        {"field": "ad_title", "value": chat.ad_title or ""}
                    ]
                )
                calltouch_requests.append(request_data)
                logger.info(f"  ✅ Подготовлен чат {chat.chat_id}")
                
            except Exception as e:
                logger.error(f"Ошибка при обработке чата {chat.chat_id}: {e}")
        
        # Отправляем в Calltouch
        logger.info(f"Отправляем {len(calltouch_requests)} чатов в Calltouch...")
        result = requests_client.send_requests(calltouch_requests)
        logger.info(f"Результат отправки чатов: {result}")
    
    # Обновляем время синхронизации чатов
    chats_state_manager.set_last_sync(datetime.now())
    return len(avito_chats)

def main():
    logger.info("="*60)
    logger.info("ЗАПУСК ПОЛНОЙ СИНХРОНИЗАЦИИ Avito -> Calltouch")
    logger.info("="*60)
    
    try:
        # Инициализация
        calls_state_manager = StateManager(Config.STATE_FILE)  # для звонков
        chats_state_manager = StateManager("data/last_chats_sync.json")  # для чатов
        avito = AvitoClient()
        calltouch_calls = CalltouchClient()
        calltouch_requests = CalltouchRequestsClient()
        
        # Обрабатываем звонки
        calls_count = process_calls(calls_state_manager, avito, calltouch_calls)
        
        # Обрабатываем чаты
        chats_count = process_chats(chats_state_manager, avito, calltouch_requests)
        
        # Итог
        logger.info("="*60)
        logger.info(f"ИТОГИ СИНХРОНИЗАЦИИ:")
        logger.info(f"  📞 Звонков: {calls_count}")
        logger.info(f"  💬 Чатов: {chats_count}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
