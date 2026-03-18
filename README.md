# Avito to Calltouch Sync

Автоматическая синхронизация звонков из Avito в Calltouch.

## 📋 Возможности

- Импорт звонков из Avito в Calltouch
- Автоматический запуск каждый час через GitHub Actions
- Тегирование звонков ("Avito", "Звонок с площадки")
- Сохранение состояния синхронизации
- Логирование всех операций

## 🚀 Быстрый старт

1. **Форкните этот репозиторий**

2. **Получите API ключи Calltouch:**
   - Зайдите в личный кабинет Calltouch
   - Настройки → API
   - Скопируйте API ключ и Site ID

3. **Добавьте секреты в GitHub:**
   - Перейдите в Settings → Secrets and variables → Actions
   - Добавьте:
     - `CALLTOUCH_ACCESS_TOKEN` - ваш API ключ
     - `CALLTOUCH_SITE_ID` - ваш Site ID

4. **Настройте получение данных из Avito:**
   - Отредактируйте `src/avito_client.py`
   - Добавьте реальное API Avito или парсинг

5. **Включите GitHub Actions:**
   - Перейдите в Actions → Enable

## 🔧 Настройка Avito API

Для реальной работы вам нужно:

1. **Получить доступ к API Avito:**
   - https://www.avito.ru/professionals/api/
   - Создайте приложение
   - Получите Client ID и Client Secret

2. **Используйте эндпоинты Avito:**
   - `/api/1/calls` - для звонков
   - `/api/1/chats` - для чатов

## 📊 Мониторинг

- Логи синхронизации сохраняются в `logs/sync.log`
- В GitHub Actions можно скачать артефакты с логами
- Статус последней синхронизации в `data/last_sync.json`

## 🔒 Безопасность

- Все ключи хранятся в GitHub Secrets
- Никаких паролей в коде
- Только чтение данных из Avito
- Только запись в Calltouch

## 📝 Лицензия

MIT
