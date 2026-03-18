#!/usr/bin/env python
"""
Тест получения звонков за разные периоды
"""
from datetime import datetime, timedelta
from src.avito_client import AvitoClient
from src.utils import StateManager
import time

def test_calls_for_period(days_back=30):
    """Тест звонков за указанный период"""
    
    print(f"📞 Тест получения звонков за последние {days_back} дней")
    print("="*60)
    
    # Инициализируем клиент
    client = AvitoClient()
    
    # Пробуем разные периоды
    periods = [
        (days_back, "за все время"),
        (7, "за последнюю неделю"),
        (3, "за последние 3 дня"),
        (1, "за последние сутки"),
    ]
    
    for days, description in periods:
        print(f"\n🕐 Период: {description}")
        
        since_time = datetime.now() - timedelta(days=days)
        print(f"   С: {since_time}")
        
        try:
            calls = client.get_calls_since(since_time)
            print(f"   📊 Найдено звонков: {len(calls)}")
            
            if calls:
                # Покажем первые 3 звонка
                for i, call in enumerate(calls[:3]):
                    print(f"   {i+1}. ID: {call.id}, Время: {call.call_time}, Длит: {call.duration}с")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # Небольшая пауза между запросами
        time.sleep(1)

def test_with_specific_dates():
    """Тест с конкретными датами"""
    print("\n📅 Тест с конкретными датами")
    print("="*60)
    
    client = AvitoClient()
    
    # Пробуем разные комбинации дат
    test_dates = [
        (datetime.now() - timedelta(days=1), "вчера"),
        (datetime.now() - timedelta(days=7), "неделю назад"),
        (datetime.now() - timedelta(days=30), "месяц назад"),
        (datetime(2026, 3, 1), "с 1 марта 2026"),
        (datetime(2026, 2, 1), "с 1 февраля 2026"),
    ]
    
    for since_time, description in test_dates:
        print(f"\n🕐 Тест: {description}")
        print(f"   С: {since_time}")
        
        try:
            calls = client.get_calls_since(since_time)
            print(f"   📊 Найдено звонков: {len(calls)}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

def test_pagination():
    """Тест пагинации (получение всех звонков)"""
    print("\n📑 Тест пагинации")
    print("="*60)
    
    client = AvitoClient()
    
    # Получаем звонки за последние 90 дней с пагинацией
    since_time = datetime.now() - timedelta(days=90)
    
    all_calls = []
    offset = 0
    limit = 100
    
    while True:
        print(f"\n📦 Запрос с offset={offset}, limit={limit}")
        
        try:
            # Создаем запрос вручную для пагинации
            token = client._get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "dateTimeFrom": since_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "dateTimeTo": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "limit": limit,
                "offset": offset
            }
            
            response = requests.post(
                "https://api.avito.ru/calltracking/v1/getCalls/",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                calls = data.get("calls", [])
                all_calls.extend(calls)
                
                print(f"   Получено: {len(calls)} звонков")
                print(f"   Всего собрано: {len(all_calls)}")
                
                if len(calls) < limit:
                    print("✅ Все звонки получены")
                    break
                    
                offset += limit
            else:
                print(f"❌ Ошибка: {response.status_code}")
                print(response.text)
                break
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            break
    
    print(f"\n📊 ИТОГО: {len(all_calls)} звонков за 90 дней")

if __name__ == "__main__":
    import requests
    
    print("🔍 Детальное тестирование API звонков Avito")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # test_calls_for_period(90)  # за 90 дней
    test_with_specific_dates()
    # test_pagination()
