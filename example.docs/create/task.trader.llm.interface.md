# [TRADER] LLM-Interface to Finam Trade API

## Обзор проекта

Создать AI-ассистента, который преобразует запросы на естественном языке в вызовы Finam TradeAPI. Ассистент должен понимать сложные запросы трейдера и генерировать точные HTTP-запросы к API.

**Цель:** 70% - accuracy на тестовых данных (лидерборд), 30% - питч (MVP + кейсы: портфельный анализ, сканер рынка, бэктестинг).

**Метрика:** Accuracy = N_correct / N_total, где запрос правильный, если type (GET/POST/DELETE) и request (путь) совпадают с эталоном. Игнорируется account_id/order_id (заменяется плейсхолдером).

## Данные

- **train.csv** (100 примеров): вопрос → type;request (e.g., "Какая цена Сбербанка?" → GET /v1/instruments/SBER@MISX/quotes/latest).
- **test.csv** (300 вопросов): для генерации submission.csv (uid;type;request).
- **sample_submission.csv**: шаблон для отправки.

**Edge cases:** Нет trades/transactions на демо (ошибка 13; обработать как пустой список). Invalid ticker → 404 (fallback /v1/assets). Относительные даты → /v1/clock. YNDX → YDEX@TQBR.

## Архитектура

```
src/app/
├── adapters/finam_client.py  # Клиент Finam API (requests + retry)
├── core/
│   ├── llm.py              # LLM (OpenRouter: GPT-4o-mini/GPT-4o)
│   ├── config.py           # Настройки (.env)
│   └── prompt.py           # Few-shot промпты
└── interfaces/
    ├── chat_app.py         # Streamlit UI
    └── chat_cli.py         # CLI для тестов

scripts/
├── generate_submission.py  # LLM → submission.csv
├── calculate_metrics.py    # Accuracy на train/test
└── validate_submission.py  # Проверка submission

data/processed/
├── train.csv
├── test.csv
└── submission.csv         # Выходной файл
```

**Поток:** Вопрос → LLM (few-shot + CoT) → type;request → submission.csv (для LB) или API-вызов (для чата).

## Установка

```bash
git clone <repo>
cd finam-x-hse-trade-ai-hack-trader
cp .env.example .env  # Добавьте OPENROUTER_API_KEY, FINAM_ACCESS_TOKEN

# Docker (рекомендуется)
make up  # http://localhost:8501

# Локально
poetry install
poetry run streamlit run src/app/interfaces/chat_app.py
```

## Разработка

### Улучшение accuracy (>85%)
- **Few-shot:** 10-20 примеров из train.csv (баланс GET/POST/DELETE).
- **Промпт:** "Преобразуй в API-запрос: [few-shot]. Вопрос: [question]. JSON: {'type': 'GET', 'request': '/path'}".
- **Модели:** GPT-4o-mini (дешево), GPT-4o (точность). Claude-3.5-Sonnet для сложных.
- **Post-processing:** Замена {account_id} → плейсхолдер; retry 500/503 (tenacity).
- **Тестирование:** `poetry run calculate-metrics` (>80% на train).

### Продвинутые кейсы (питч)
- **Портфельный анализ:** GET /v1/accounts/{id} → sunburst (Plotly), PnL, рекомендации.
- **Сканер рынка:** GET /v1/assets → фильтр (критерии), таблица + sparklines.
- **Бэктестинг:** GET /v1/instruments/{symbol}/bars → equity curve, Sharpe ratio.
- **UI:** Streamlit (готовый) + Plotly (графики). Запись демо (OBS).

### Безопасность
- Подтверждение для POST/DELETE: "Подтвердите ордер: [детали]?".
- JWT refresh каждые 15 мин (/v1/sessions).
- Обработка ошибок: 13 (no data) → "Нет данных"; 404 → fallback.

## Запуск

```bash
# Генерация submission
poetry run generate-submission --num-examples 15

# Метрики
poetry run calculate-metrics --show-errors 10

# Валидация
poetry run validate-submission

# Чат (тест)
poetry run chat-cli
```

## Отправка

1. **Лидерборд:** Загрузите submission.csv на платформу (50 сабмитов/день).
2. **Питч (топ-20):** 5 мин: демо (MVP + 1 кейс), архитектура, планы. QR-код + видео.

**Цель:** >85% accuracy + крутой питч (визуализация, UX, визионерство).

Демо: Запустите чат, спросите "Анализ портфеля" → GET /v1/accounts → Plotly sunburst.
