#!/usr/bin/env python
"""
Тестовый скрипт для проверки API Avito
"""
import requests
import base64
from datetime import datetime
from config.config import Config

def test_token():
    """Тест получения токена"""
    print("\n🔑 1. Тест получения токена")
    
    auth = base64.b64encode(
        f"{Config.AVITO_CLIENT_ID}:{Config.AVITO_CLIENT_SECRET}".encode()
    ).decode()
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "client_credentials",
        "client_id": Config.AVITO_CLIENT_ID
    }
    
    response = requests.post(
        "https://api.avito.ru/token",
        headers=headers,
        data=data
    )
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Токен получен")
        print(f"   expires_in: {token_data['expires_in']} сек (24 часа)")
        print(f"   token_type: {token_data['token_type']}")
        return token_data['access_token']
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)
        return None

def test_endpoints(token):
    """Тест доступных endpoints"""
    print("\n📡 2. Тест endpoints")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        ("/core/v1/accounts/self", "Информация об аккаунте"),
        ("/core/v1/items", "Список объявлений"),
        ("/messenger/v1/threads", "Список чатов"),
    ]
    
    for endpoint, description in endpoints:
        print(f"\n{description}: {endpoint}")
        try:
            response = requests.get(
                f"https://api.avito.ru{endpoint}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Статус: 200 OK")
                print(f"   Ключи ответа: {list(data.keys())}")
                
                # Сохраним пример ответа в файл
                with open(f"avito_{endpoint.replace('/', '_')}.json", "w") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"   Ответ сохранен в avito_{endpoint.replace('/', '_')}.json")
                
            elif response.status_code == 403:
                print(f"❌ 403 Forbidden - нет прав доступа")
                print(f"   Нужен соответствующий scope")
            else:
                print(f"⚠️ {response.status_code}")
                print(response.text[:200])
                
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")

def test_stats(token):
    """Тест получения статистики"""
    print("\n📊 3. Тест статистики")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Сначала получим список объявлений
    response = requests.get(
        "https://api.avito.ru/core/v1/items",
        headers=headers,
        params={"limit": 5}
    )
    
    if response.status_code == 200:
        items = response.json()
        items_list = items.get("items", []) or items.get("resources", [])
        
        print(f"Найдено объявлений: {len(items_list)}")
        
        for item in items_list[:3]:  # Тестируем первые 3
            item_id = item.get("id")
            print(f"\nОбъявление {item_id}: {item.get('title', 'Без названия')[:50]}")
            
            # Пробуем разные варианты статистики
            stats_endpoints = [
                f"/core/v1/stats/items/{item_id}",
                f"/stats/v1/items/{item_id}",
            ]
            
            for stats_endpoint in stats_endpoints:
                print(f"  Тест: {stats_endpoint}")
                stats_response = requests.get(
                    f"https://api.avito.ru{stats_endpoint}",
                    headers=headers,
                    params={
                        "date_from": datetime.now().strftime("%Y-%m-01"),
                        "date_to": datetime.now().strftime("%Y-%m-%d")
                    },
                    timeout=10
                )
                
                if stats_response.status_code == 200:
                    print(f"    ✅ Успешно!")
                    stats_data = stats_response.json()
                    print(f"    Ключи: {list(stats_data.keys())}")
                    break
                else:
                    print(f"    ❌ {stats_response.status_code}")
    else:
        print("❌ Не удалось получить список объявлений")

if __name__ == "__main__":
    import json
    
    print("🚀 Тестирование API Avito")
    print("="*50)
    
    token = test_token()
    if token:
        test_endpoints(token)
        test_stats(token)
    else:
        print("❌ Не удалось получить токен. Проверьте client_id и client_secret")
