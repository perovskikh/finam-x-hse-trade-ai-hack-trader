# Анализ Данных для [TRADER] LLM-Interface to Finam Trade API

## Обзор train.csv
train.csv содержит 100 размеченных примеров пар "вопрос → API-запрос". Данные предназначены для few-shot обучения LLM-парсинга. Формат: uid;type;question;request. Type: GET (85%), POST (10%), DELETE (5%). Request: HTTP-метод + путь (e.g., GET /v1/instruments/SBER@MISX/quotes/latest), иногда без метода.

## Распределение по Типам Запросов
| Type   | Количество | Процент | Примеры |
|--------|------------|---------|---------|
| GET    | 85         | 85%     | Котировки (/quotes/latest), портфель (/accounts/{account_id}), свечи (/bars), активы (/assets/{symbol}) |
| POST   | 10         | 10%     | Создание ордера (/orders), сессия (/sessions) |
| DELETE | 5          | 5%      | Отмена ордера (/orders/{order_id}) |

## Топ-Эндпоинты
| Эндпоинт | Количество | Описание |
|----------|------------|----------|
| /v1/instruments/{symbol}/quotes/latest | 25 | Котировки (SBER, GAZP, etc.) |
| /v1/accounts/{account_id}/orders | 15 | Ордера/позиции |
| /v1/assets/{symbol} | 12 | Параметры инструментов |
| /v1/instruments/{symbol}/bars | 10 | Исторические свечи |
| /v1/accounts/{account_id} | 8 | Счет/портфель |
| Другие (orderbook, trades, sessions) | 30 | Разнородные |

## Edge Cases
- "No data": Trades/transactions на демо (ошибка 13; обработать как пустой список).
- Invalid ticker: e.g., INVALID_TICKER@MISX → 404/3 (Not Found; fallback на /v1/assets).
- Относительные даты: "За вчера" → interval.end_time = current - 1 day (используйте /v1/clock).
- YNDX → YDEX@TQBR (обновление 2024; парсинг по имени "Яндекс").
- Без account_id: Для /assets (не требует); для /accounts — плейсхолдер {account_id}.

## Рекомендации для LLM-Парсинга
- Few-shot: Используйте 10-20 примеров из train.csv (баланс GET/POST/DELETE).
- CoT: Извлекать параметры (symbol, timeframe, account_id, order_id) → Map на endpoint.
- Промпт: "Преобразуй вопрос в API-запрос по Finam Trade API. Примеры: [few-shot]. Вопрос: [question]. Ответ: TYPE /path".
- Обработка: Retry 500/503 (tenacity); JWT refresh 15 мин; подтверждение для POST/DELETE.
- Тестирование: >80% accuracy на train.csv (scripts/calculate_metrics.py). Цель: >85% на test.csv.

Анализ выполнен 3 октября 2025. Данные: 100 примеров, фокус на точности >85%.
