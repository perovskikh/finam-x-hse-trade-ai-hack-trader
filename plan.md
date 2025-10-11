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
# Project Plan: AI Trader Assistant for Finam x HSE Hackathon (October 2025)

## 1. Analyze Requirements (CoT Step 1)
- **Objective**: Build an AI assistant that parses user queries into Finam Trade API requests (GET/POST/DELETE) with >85% accuracy on test.csv for submission.csv generation. Include visualization for pitch (30% score).
- **Key Extractions**: Parse parameters like ticker (e.g., AFLT@MISX), account_id, timeframe, order_id from queries. Use HTTP methods from train.csv examples (e.g., "Купи 1000 акций" → POST /v1/accounts/{account_id}/orders).
- **Edge Cases**: Handle "no data" (e.g., trades on demo), 404 errors (invalid ticker), empty lists (orders). Require user confirmation for POST/DELETE.
- **Metrics**: >85% accuracy (70% evaluation); Pitch visualization (Plotly: candlestick, sunburst, sparklines) for 30%.
- **Assumptions**: Use OpenRouter for LLM (e.g., Grok/GPT-5), FinamPy for API, demo account for testing. Limit: 200 req/min, JWT refresh every 15 min.

## 2. Outline Architecture (CoT Step 2)
Architecture uses modular design with adapters, core LLM processing, and interfaces. Focus on few-shot learning from train.csv for parsing accuracy.

| Module | Description | Dependencies |
|--------|-------------|--------------|
| adapters/finam_client.py | FinamPy wrapper for gRPC/REST, JWT refresh, retry on 500/503. Methods: get_quote, create_order, etc. | FinamPy, tenacity, requests |
| core/llm.py | LLM parsing with few-shot examples from train.csv. Classes: TradingIntent (parsed params), LLMProcessor (prompt generation, API mapping). | pandas, openrouter (or langchain), pydantic |
| interfaces/chat_app.py | Streamlit UI for chat, Plotly visualizations (e.g., candlestick for bars, sunburst for portfolio). Handles confirmation for POST/DELETE. | streamlit, plotly, pandas |
| scripts/generate_submission.py | Batch process test.csv to submission.csv using LLMProcessor. Validate accuracy locally on train.csv. | pandas, click |

- **Classes**:
  - `FinamClient`: Executes requests with retry and confirmation (e.g., input("[БЕЗОПАСНОСТЬ] Подтвердите: да/нет")).
  - `TradingIntent`: Pydantic model for parsed query (method, path, params, json).
  - `LLMProcessor`: Builds prompts with few-shot, calls LLM, extracts structured output (e.g., JSON mode).
- **Flow**: User query → LLM parse → Map to API → Execute (with confirmation if POST/DELETE) → Visualize response → Return to user.

## 3. Detail Code Changes (CoT Step 3)
Implement PEP8-compliant changes with diffs. Focus on API methods from Finam docs (GetPortfolios, NewOrder, etc.). Use few-shot from train.csv. Add retry, confirmation, Plotly.

### Changes in adapters/finam_client.py
```diff
+ import asyncio
+ from datetime import datetime, timedelta
+ from tenacity import retry, stop_after_attempt, wait_exponential
+ import requests
+ 
+ class FinamAPIClient:
+     def __init__(self, access_token: str, base_url: str = "https://api.finam.ru"):
+         self.access_token = access_token
+         self.base_url = base_url
+         self.session = requests.Session()
+         self.session.headers.update({"Authorization": self.access_token, "Content-Type": "application/json"})
+         self.jwt_expiry = datetime.now() + timedelta(minutes=15)
+ 
+     @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
+     async def refresh_jwt(self):
+         response = await asyncio.to_thread(self.session.post, f"{self.base_url}/v1/sessions")
+         if response.ok:
+             data = response.json()
+             self.access_token = data["access_token"]
+             self.session.headers["Authorization"] = self.access_token
+             self.jwt_expiry = datetime.now() + timedelta(minutes=15)
+ 
+     def execute_request(self, method: str, path: str, **kwargs):
+         if datetime.now() > self.jwt_expiry:
+             asyncio.run(self.refresh_jwt())
+         if method in ["POST", "DELETE"]:
+             confirm = input(f"[БЕЗОПАСНОСТЬ] Подтвердите {method} {path} (да/нет): ")
+             if confirm.lower() != "да":
+                 return {"status": "cancelled"}
+         url = f"{self.base_url}{path}"
+         resp = self.session.request(method, url, **kwargs)
+         resp.raise_for_status()
+         return resp.json() if resp.content else {"status": "success"}
+ 
+     # Add methods like get_portfolios, create_order, etc., matching Finam API
```

### Changes in core/llm.py
```diff
+ from pydantic import BaseModel
+ import openai  # or openrouter client
+ 
+ class TradingIntent(BaseModel):
+     method: str
+     path: str
+     params: dict = {}
+     json: dict = {}
+ 
+ class LLMProcessor:
+     def __init__(self, model: str = "gpt-4o"):
+         self.client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key="your_key")
+         self.few_shot = pd.read_csv("data/raw/train.csv").to_dict(orient="records")  # Load examples
+ 
+     def generate_prompt(self, query: str) -> str:
+         prompt = "Parse query to Finam API request. Few-shot examples:\n"
+         for ex in self.few_shot[:5]:
+             prompt += f"Query: {ex['query']} → {ex['method']} {ex['request']}\n"
+         prompt += f"Query: {query} →"
+         return prompt
+ 
+     def parse_query(self, query: str) -> TradingIntent:
+         response = self.client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": self.generate_prompt(query)}])
+         # Extract structured output (e.g., JSON from response)
+         return TradingIntent.parse_obj(extract_json(response.choices[0].message.content))
```

### Changes in interfaces/chat_app.py
```diff
+ import streamlit as st
+ import plotly.express as px
+ from app.adapters import FinamAPIClient
+ from app.core import LLMProcessor
+ 
+ st.title("AI Trader Assistant")
+ query = st.text_input("Enter query:")
+ if query:
+     processor = LLMProcessor()
+     intent = processor.parse_query(query)
+     client = FinamAPIClient(os.getenv("FINAM_ACCESS_TOKEN"))
+     response = client.execute_request(intent.method, intent.path, params=intent.params, json=intent.json)
+     # Visualize: e.g., if "bars" in path, px.line(response["bars"], x="time", y="close")
+     if "bars" in intent.path:
+         df = pd.DataFrame(response["bars"])
+         fig = px.candlestick(df, x="time", open="open", high="high", low="low", close="close")
+         st.plotly_chart(fig)
+     st.write(response)
```

### Changes in scripts/generate_submission.py
```diff
+ import pandas as pd
+ from app.core import LLMProcessor
+ 
+ def main():
+     test = pd.read_csv("data/raw/test.csv")
+     processor = LLMProcessor()
+     submissions = []
+     for _, row in test.iterrows():
+         intent = processor.parse_query(row["query"])
+         submissions.append({"uid": row["uid"], "type": intent.method, "request": intent.path})
+     pd.DataFrame(submissions).to_csv("data/processed/submission.csv", index=False)
+ 
+ if __name__ == "__main__":
+     main()
```

## 4. Alignment with Metrics (CoT Step 4)
- **Accuracy**: Validate on train.csv (>85% via local script). Handle edges (404 → error message, no data → "empty").
- **Visualization**: Plotly for pitch (candlestick for bars, sunburst for portfolios, sparklines for scanners).
- **Security**: Confirmation for POST/DELETE in FinamClient.
- **Testing**: Run on demo account (handle JWT, limits). Generate submission.csv for leaderboard.
- **Pitch Prep**: Demo chat_app.py with examples; ensure >85% on public test.

This plan ensures >85% accuracy and strong pitch. Total timeline: 2 days coding, 1 day testing/pitch.
