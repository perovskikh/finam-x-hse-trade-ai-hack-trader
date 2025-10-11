# План Проекта [TRADER] LLM-Interface to Finam Trade API (Финальная Версия)

## Обзор
**Цель**: Создать AI-ассистент трейдера, преобразующий запросы на естественном языке в вызовы Finam Trade API, с аналитикой и визуализацией (Plotly). Хакатон Finam x HSE (3-5 октября 2025).  
**Оценка**: 70% лидерборд (accuracy >85% на скрытых тестах), 30% питч (MVP + кейсы: портфельный аналитик, сканер рынка, песочница стратегий).  
**Данные**: train.csv (100 примеров), test.csv (300+ для submission.csv).  
**Ограничения**: Finam Trade API единственный источник; демо-счет (нет trades/transactions, условные ордера); JWT refresh 15 мин; retry 500/503; безопасность (подтверждение POST/DELETE).  
**Сроки**: 3-4 октября — кодинг; 5 октября — питч (топ-20 по LB).

## Архитектура
**Структура проекта** (Исправлено: Убраны дубликаты, добавлены скрипты для метрик):
- `adapters/`: finam_client.py (FinamPy, async gRPC/REST, JWT/retry).
- `core/`: llm.py (TradingIntent для парсинга, LLMProcessor для OpenRouter).
- `interfaces/`: chat_app.py (Streamlit чат, Plotly визуализация).
- `scripts/`: generate_submission.py (submission.csv), calculate_metrics.py (accuracy).
- `data/processed/`: train.csv, test.csv, submission.csv.

**Ключевые классы**:
- `FinamClient`: Обертка API (GetPortfolios, GetBars, NewOrder; retry tenacity).
- `TradingIntent`: Few-shot парсинг запросов (train.csv; извлечение тикер/account_id).
- `LLMProcessor`: Интеграция с grok-4/grok-code-fast-1 (OpenRouter; CoT для API-вызовов)

**Зависимости**:
| Библиотека | Назначение |
|------------|------------|
| FinamPy | Finam Trade API |
| tenacity | Retry ошибок |
| pandas | Обработка CSV |
| streamlit | Чат UI |
| plotly | Визуализация (candlestick/sunburst) |
| openrouter | LLM (grok-4) |

**API-методы (MVP)**:
- AccountsService: GET /v1/accounts/{account_id} (портфель)
- MarketDataService: GET /v1/instruments/{symbol}/bars (свечи).
- AssetsService: GET /v1/assets/{symbol} (параметры).
- Orders: POST /v1/accounts/{account_id}/orders (ордера, с подтверждением).

## План Реализации
**Этап 1: Анализ данных (3 октября, утро)**:
- Изучить train.csv/test.csv (примеры: "Покажи портфель" → GET /v1/portfolios).
- Обработать edge cases (YDEX@TQBR вместо YNDX; "no data" для trades).
- Настроить Aider (.aider.conf.yml; модели grok-4 для плана, grok-code-fast-1 для кода)

**Этап 2: Архитектура и MVP (3-4 октября, день)**:
- Реализовать FinamClient (async вызовы, JWT refresh, retry 500/503).
- LLMProcessor: Few-shot промпт (train.csv; CoT для извлечения параметров).
- Chat_app: Streamlit чат; парсинг → API → анализ → визуализация.
- Безопасность: Шаблон "[БЕЗОПАСНОСТЬ] Подтвердите..." для ордеров.
- Generate_submission: LLM → uid/type/request (accuracy >85%).

**Этап 3: Кейсы и визуализация (4 октября, вечер)**:
- Портфельный аналитик: GetPortfolios → sunburst (Plotly) + ребалансировка
- Сканер рынка: GetAssets + GetBars → таблица со sparklines.
- Песочница: GetBars → бэктест (график сделок + кривая доходности).
- Тестирование: calculate_metrics.py на test.csv; демо (AAPL@XNYS).

**Этап 4: Валидация и питч (5 октября)**:
- Submission.csv: >85% accuracy (игнор account_id/order_id).
- Питч: QR/видео демо (MVP + 1 кейс); архитектура; планы (расширение на реальные счета).

## Риски и Митigation
- **Риск**: Ошибки демо (нет trades) — Мит: Симулировать "no data"; фокус на условных ордерах
- **Риск**: Лимиты API ($10 OpenRouter) — Мит: Тестировать на grok-code-fast-1; кэширование.
- **Риск**: Неточность LLM — Мит: Few-shot из train.csv; CoT в промпте.
- **Риск**: Платформа LB — Мит: Локальные тесты (calculate_metrics.py); 50 сабмитов/день.

**Подтверждение**: План готов к реализации с Aider (grok-code-fast-1; --file plan.md).
# План Проекта [TRADER] LLM-Interface to Finam Trade API

## Обзор
**Цель**: Создать AI-ассистент трейдера, преобразующий запросы на естественном языке в вызовы Finam Trade API, с аналитикой и визуализацией (Plotly). Хакатон Finam x HSE (3-5 октября 2025).  
**Оценка**: 70% лидерборд (accuracy >85% на скрытых тестах), 30% питч (MVP + кейсы: портфельный аналитик, сканер рынка, песочница стратегий).  
**Данные**: train.csv (100 примеров), test.csv (300+ для submission.csv).  
**Ограничения**: Finam Trade API единственный источник; демо-счет (нет trades/transactions, условные ордера); JWT refresh 15 мин; retry 500/503; безопасность (подтверждение POST/DELETE).  
**Сроки**: 3-4 октября — кодинг; 5 октября — питч (топ-20 по LB).

## Архитектура
**Структура проекта**:
- `adapters/`: finam_client.py (FinamPy, async gRPC/REST, JWT/retry).
- `core/`: llm.py (TradingIntent для парсинга, LLMProcessor для OpenRouter).
- `interfaces/`: chat_app.py (Streamlit чат, Plotly визуализация).
- `scripts/`: generate_submission.py (submission.csv), calculate_metrics.py (accuracy).
- `data/processed/`: train.csv, test.csv, submission.csv.

**Ключевые классы**:
- `FinamClient`: Обертка API (GetPortfolios, GetBars, NewOrder; retry tenacity).
- `TradingIntent`: Few-shot парсинг запросов (train.csv; извлечение тикер/account_id).
- `LLMProcessor`: Интеграция с grok-4/grok-code-fast-1 (OpenRouter; CoT для API-вызовов).

**Зависимости**:
| Библиотека | Назначение |
|------------|------------|
| FinamPy | Finam Trade API |
| tenacity | Retry ошибок |
| pandas | Обработка CSV |
| streamlit | Чат UI |
| plotly | Визуализация (candlestick/sunburst) |
| openrouter | LLM (grok-4) |

**API-методы (MVP)**:
- AccountsService: GET /v1/accounts/{account_id} (портфель).
- MarketDataService: GET /v1/instruments/{symbol}/bars (свечи).
- AssetsService: GET /v1/assets/{symbol} (параметры).
- Orders: POST /v1/accounts/{account_id}/orders (ордера, с подтверждением).

## План Реализации
**Этап 1: Анализ данных (3 октября, утро)**:
- Изучить train.csv/test.csv (примеры: "Покажи портфель" → GET /v1/portfolios).
- Обработать edge cases (YDEX@TQBR вместо YNDX; "no data" для trades).
- Настроить Aider (.aider.conf.yml; модели grok-4 для плана, grok-code-fast-1 для кода).

**Этап 2: Архитектура и MVP (3-4 октября, день)**:
- Реализовать FinamClient (async вызовы, JWT refresh, retry 500/503).
- LLMProcessor: Few-shot промпт (train.csv; CoT для извлечения параметров).
- Chat_app: Streamlit чат; парсинг → API → анализ → визуализация.
- Безопасность: Шаблон "[БЕЗОПАСНОСТЬ] Подтвердите..." для ордеров.
- Generate_submission: LLM → uid/type/request (accuracy >85%).

**Этап 3: Кейсы и визуализация (4 октября, вечер)**:
- Портфельный аналитик: GetPortfolios → sunburst (Plotly) + ребалансировка.
- Сканер рынка: GetAssets + GetBars → таблица со sparklines.
- Песочница: GetBars → бэктест (график сделок + кривая доходности).
- Тестирование: calculate_metrics.py на test.csv; демо (AAPL@XNYS).

**Этап 4: Валидация и питч (5 октября)**:
- Submission.csv: >85% accuracy (игнор account_id/order_id).
- Питч: QR/видео демо (MVP + 1 кейс); архитектура; планы (расширение на реальные счета).

## Риски и Митigation
- **Риск**: Ошибки демо (нет trades) — Мит: Симулировать "no data"; фокус на условных ордерах.
- **Риск**: Лимиты API ($10 OpenRouter) — Мит: Тестировать на grok-code-fast-1; кэширование.
- **Риск**: Неточность LLM — Мит: Few-shot из train.csv; CoT в промпте.
- **Риск**: Платформа LB — Мит: Локальные тесты (calculate_metrics.py); 50 сабмитов/день.

**Подтверждение**: План готов к реализации с Aider (grok-code-fast-1; --file plan.md).
### Очерк Архитектуры Проекта [TRADER] LLM-Interface to Finam Trade API

| Модуль/Компонент | Описание | Зависимости | Обоснование |
|------------------|----------|-------------|-------------|
| `adapters/finam_client.py` | Клиент для Finam Trade API (gRPC/REST, JWT refresh, retry 500/503) | FinamPy, tenacity, requests | Обеспечивает доступ к API (GetPortfolios, GetBars, NewOrder); async для производительности; безопасность (подтверждение POST/DELETE). |
| `core/llm.py` | Парсинг запросов (TradingIntent), few-shot промпт из train.csv, LLMProcessor для OpenRouter | pandas, openrouter | Преобразует естественный язык в API-вызовы; CoT для извлечения параметров (тикер, account_id); точность >85% accuracy. |
| `interfaces/chat_app.py` | Streamlit чат-интерфейс с Plotly визуализацией (candlestick/sunburst/sparklines) | streamlit, plotly | Диалоговый UI; анализ + визуализация для кейсов (портфель/сканер/бэктест); подтверждение ордеров. |
| `scripts/generate_submission.py` | Генерация submission.csv из test.csv (LLM → uid/type/request) | pandas, openrouter | Для лидерборда; batch-processing с few-shot; метрика accuracy. |
| `scripts/calculate_metrics.py` | Подсчет accuracy (нормализация, игнор account_id/order_id) | pandas | Валидация на train.csv; >85% для submission.csv. |
| `data/processed/train.csv` | Примеры запросов (question → type/request) | - | Few-shot для LLM; 100 примеров для обучения. |
| `data/processed/test.csv` | Тестовые запросы (uid/question) | - | Для генерации submission.csv; 300+ вопросов. |
| `data/processed/submission.csv` | Результат (uid/type/request) | - | Финальный файл для оценки (70% лидерборд). |

**Ключевые Классы**:
- `FinamClient`: Обертка API с retry/JWT.
- `TradingIntent`: Извлечение параметров из текста.
- `LLMProcessor`: Интеграция с grok-4/grok-code-fast-1

**Зависимости (Основные)**:
- FinamPy: API-клиент.
- tenacity: Retry ошибок.
- pandas: Обработка CSV.
- streamlit: UI.
- plotly: Визуализация.
- openrouter: LLM (лимиты $10).

**Обоснование Архитектуры**: Следует plan.md; MVP фокус на API-точности и кейсах; безопасность (подтверждение); оптимизация (async, кэш); тестирование на demo-счете (YDEX@TQBR, AAPL@XNYS).
# План Проекта [TRADER] LLM-Interface to Finam Trade API

## Обзор
**Цель**: Создать AI-ассистент трейдера, преобразующий запросы на естественном языке в вызовы Finam Trade API, с аналитикой и визуализацией (Plotly). Хакатон Finam x HSE (3-5 октября 2025).  
**Оценка**: 70% лидерборд (accuracy >85% на скрытых тестах), 30% питч (MVP + кейсы: портфельный аналитик, сканер рынка, песочница стратегий).  
**Данные**: train.csv (100 примеров), test.csv (300+ для submission.csv).  
**Ограничения**: Finam Trade API единственный источник; демо-счет (нет trades/transactions, условные ордера); JWT refresh 15 мин; retry 500/503; безопасность (подтверждение POST/DELETE).  
**Сроки**: 3-4 октября — кодинг; 5 октября — питч (топ-20 по LB).

## Архитектура
**Структура проекта**:
- `adapters/`: finam_client.py (FinamPy, async gRPC/REST, JWT/retry).
- `core/`: llm.py (TradingIntent для парсинга, LLMProcessor для OpenRouter).
- `interfaces/`: chat_app.py (Streamlit чат, Plotly визуализация).
- `scripts/`: generate_submission.py (submission.csv), calculate_metrics.py (accuracy).
- `data/processed/`: train.csv, test.csv, submission.csv.

**Ключевые классы**:
- `FinamClient`: Обертка API (GetPortfolios, GetBars, NewOrder; retry tenacity).
- `TradingIntent`: Few-shot парсинг запросов (train.csv; извлечение тикер/account_id).
- `LLMProcessor`: Интеграция с grok-4/grok-code-fast-1 (OpenRouter; CoT для API-вызовов).

**Зависимости**:
| Библиотека | Назначение |
|------------|------------|
| FinamPy | Finam Trade API |
| tenacity | Retry ошибок |
| pandas | Обработка CSV |
| streamlit | Чат UI |
| plotly | Визуализация (candlestick/sunburst) |
| openrouter | LLM (grok-4) |

**API-методы (MVP)**:
- AccountsService: GET /v1/accounts/{account_id} (портфель).
- MarketDataService: GET /v1/instruments/{symbol}/bars (свечи).
- AssetsService: GET /v1/assets/{symbol} (параметры).
- Orders: POST /v1/accounts/{account_id}/orders (ордера, с подтверждением).

## План Реализации
**Этап 1: Анализ данных (3 октября, утро)**:
- Изучить train.csv/test.csv (примеры: "Покажи портфель" → GET /v1/portfolios).
- Обработать edge cases (YDEX@TQBR вместо YNDX; "no data" для trades).
- Настроить Aider (.aider.conf.yml; модели grok-4 для плана, grok-code-fast-1 для кода).

**Этап 2: Архитектура и MVP (3-4 октября, день)**:
- Реализовать FinamClient (async вызовы, JWT refresh, retry 500/503).
- LLMProcessor: Few-shot промпт (train.csv; CoT для извлечения параметров).
- Chat_app: Streamlit чат; парсинг → API → анализ → визуализация.
- Безопасность: Шаблон "[БЕЗОПАСНОСТЬ] Подтвердите..." для ордеров.
- Generate_submission: LLM → uid/type/request (accuracy >85%).

**Этап 3: Кейсы и визуализация (4 октября, вечер)**:
- Портфельный аналитик: GetPortfolios → sunburst (Plotly) + ребалансировка.
- Сканер рынка: GetAssets + GetBars → таблица со sparklines.
- Песочница: GetBars → бэктест (график сделок + кривая доходности).
- Тестирование: calculate_metrics.py на test.csv; демо (AAPL@XNYS).

**Этап 4: Валидация и питч (5 октября)**:
- Submission.csv: >85% accuracy (игнор account_id/order_id).
- Питч: QR/видео демо (MVP + 1 кейс); архитектура; планы (расширение на реальные счета).

## Риски и Митigation
- **Риск**: Ошибки демо (нет trades) — Мит: Симулировать "no data"; фокус на условных ордерах.
- **Риск**: Лимиты API ($10 OpenRouter) — Мит: Тестировать на grok-code-fast-1; кэширование.
- **Риск**: Неточность LLM — Мит: Few-shot из train.csv; CoT в промпте.
- **Риск**: Платформа LB — Мит: Локальные тесты (calculate_metrics.py); 50 сабмитов/день.

**Подтверждение**: План готов к реализации с Aider (grok-code-fast-1; --file plan.md).
