#!/usr/bin/env python
"""
Тест Messenger API Avito
"""
import requests
import json
from datetime import datetime
from config.config import Config
import base64

def test_messenger_api():
    """Тестируем разные варианты запросов к Messenger API"""
    
    print("🔍 ТЕСТ MESSENGER API AVITO")
    print("="*60)
    
    # Получаем токен
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
    
    if response.status_code != 200:
        print(f"❌ Ошибка токена: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    print(f"✅ Токен получен")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    user_id = Config.AVITO_USER_ID
    print(f"👤 User ID: {user_id}")
    
    # Тест 1: Базовый запрос без параметров
    print("\n📌 ТЕСТ 1: Запрос без параметров")
    url = f"https://api.avito.ru/messenger/v2/accounts/{user_id}/chats"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Чатов: {len(data.get('chats', []))}")
        else:
            print(f"   Ответ: {response.text[:200]}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Тест 2: С минимальными параметрами
    print("\n📌 ТЕСТ 2: С параметрами limit=1")
    params = {"limit": 1}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Чатов: {len(data.get('chats', []))}")
        else:
            print(f"   Ответ: {response.text[:200]}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Тест 3: С chat_types
    print("\n📌 ТЕСТ 3: С chat_types=u2i")
    params = {
        "limit": 1,
        "chat_types": "u2i"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Чатов: {len(data.get('chats', []))}")
        else:
            print(f"   Ответ: {response.text[:200]}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Тест 4: Проверка прав доступа
    print("\n📌 ТЕСТ 4: Проверка информации о пользователе")
    url_info = f"https://api.avito.ru/core/v1/accounts/self"
    try:
        response = requests.get(url_info, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Аккаунт: {data.get('name')}")
            print(f"   Email: {data.get('email')}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Тест 5: Альтернативный endpoint
    print("\n📌 ТЕСТ 5: Альтернативный endpoint /messenger/v1/threads")
    url_alt = f"https://api.avito.ru/messenger/v1/threads"
    try:
        response = requests.get(url_alt, headers=headers, params={"limit": 1}, timeout=10)
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Успешно!")
        else:
            print(f"   Ответ: {response.text[:200]}")
    except Exception as e:
        print(f"   Ошибка: {e}")

if __name__ == "__main__":
    test_messenger_api()
