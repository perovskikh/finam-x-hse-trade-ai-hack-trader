### Суммированный План и Описание Реализации: [TRADER] LLM-Интерфейс к Trade API — AI-Ассистент Трейдера

На основе анализа двух ответов (#1 и #2), я объединил их в единый, оптимизированный план, с акцентом на упущенные детали, такие как структура проекта (детализирована из #1 и интегрирована с #2). Ответ #1 фокусируется на архитектуре, промптах, моделях данных и примерах кода для LLM/кейсов, а #2 — на технологиях, рисках, этапах и практических рекомендациях. Суммаризация устраняет дубли, усиливает фокус на структуре проекта, безопасности и визуализации. План ориентирован на хакатон Finam x HSE AI Trade Hack (завершен 5 октября 2025; топ-20 по лидерборду на питче). Поиск результатов хакатона (на 5 октября 2025) не выявил официальных победителей — возможно, они еще не объявлены (проверено через web и X поиск; официальный сайт Finam имеет только описание события). Общий бюджет: 36–50 часов (2–3 дня на MVP, 1–2 дня на кейсы/тесты).

#### Идея и Описание Проекта
**Идея**: Создать интеллектуального AI-ассистента, который переводит естественные языковые запросы в вызовы Finam Trade API, анализирует данные и предоставляет ответы с визуализацией. Ассистент упрощает трейдинг: анализ портфеля, рыночные сканы, бэктестинг, ордера с подтверждением. Единственный источник данных — Finam API (gRPC/REST). MVP: Перевод запросов в API-вызовы (>85% accuracy). Кейсы добавляют глубину для питча. Соответствует метрике: 70% — лидерборд (точность запросов), 30% — питч (кейсы/UX/безопасность).

**Целевая аудитория**: Трейдеры/инвесторы без программирования.

**Ключевые особенности**:
- **Интерфейс**: Чат (Streamlit/CLI) для диалога.
- **LLM**: OpenRouter.ai
- **API**: FinamPy (GetAccounts/GetPortfolios/GetBars/GetAssets/NewOrder и др.); обработка ошибок (retry 500/503, "no data" для trades).
- **Визуализация**: Plotly (sunburst/sparklines/candlestick), Pandas (таблицы).
- **Безопасность**: Подтверждение для NewOrder/NewStop; "лесенка" (GetOrders → CancelOrder).
- **Ограничения**: Демо-счета (условные ордера, AAPL@XNYS); тикеры (YNDX → YDEX@TQBR); даты (GetTime); лимит 200 req/min.

**Технологический стек** (базовый репозиторий: https://github.com/Orange-Hack/finam-x-hse-trade-ai-hack-trader):
- Python 3.12+ (Poetry); grpcio; tenacity; Plotly/Pandas/Matplotlib; SQLite.
- **Структура проекта** (расширена из #1 и #2 для полноты; используйте как основу для GitHub):
  ```
  project/
  ├── src/app/               # Основная логика приложения
  │   ├── adapters/          # Finam API-клиент (gRPC/REST обертки, retry)
  │   ├── core/              # LLM-интеграция (промпты, парсинг, модели данных), конфиги (.env)
  │   └── interfaces/        # UI (Streamlit чат, CLI; Markdown для визуализаций)
  ├── scripts/               # Утилиты для хакатона
  │   ├── generate_submission.py  # Генерация submission.csv (для лидерборда)
  │   ├── validate_submission.py  # Валидация CSV
  │   └── calculate_metrics.py    # Подсчет accuracy
  ├── data/processed/        # Данные для обучения/тестов
  │   ├── train.csv          # 100 размеченных запросов (few-shot)
  │   └── test.csv           # 300+ тестовых запросов (для метрики)
  ├── docs/                  # Документация (task.md, evaluation.md)
  ├── .env.example           # Шаблон ключей (OPENROUTER_API_KEY, FINAM_ACCESS_TOKEN)
  ├── Dockerfile             # Для Docker-развертывания
  ├── README.md              # Инструкции по запуску/использованию
  └── DEVELOPMENT.md         # Архитектура, планы развития
  ```
  - **Дополнения**: Добавьте папку tests/ для unit-тестов (LLM-парсинг, API-вызовы); logs/ для отладки ошибок.

**Ожидаемые результаты**: Accuracy >85% (лидерборд); 1–2 кейса для питча; GitHub с инструкциями/видео.

#### Поэтапный План Реализации
Этапы комбинированы: #1 (архитектура/код) + #2 (риски/сроки). Используйте бейзлайн (`git clone`, `poetry install`, `make up`).

##### Этап 1: Настройка Окружения и Инфраструктуры
- **Задачи**: Настроить JWT (Auth сервис, обновление каждые 15 мин); базовый gRPC-клиент; структура проекта (как выше); .env (OPENROUTER_API_KEY, FINAM_ACCESS_TOKEN); демо-счет (ЛК Finam, SMS); зависимости (`poetry install`, добавить tenacity/plotly/pandas/sqlite3).
- **Ключевые API-методы**: Auth (JWT); GetAccounts/GetPortfolios; GetBars/GetLastQuote; GetAssets/GetAssetParams.
- **Пример кода** (adapters/finam_client.py):
  ```python
  import grpc
  from tenacity import retry, wait_exponential
  @retry(wait=wait_exponential(multiplier=1, min=4, max=10))
  def create_channel():
      return grpc.secure_channel('api.finam.ru:443', grpc.ssl_channel_credentials())
  ```
- **Риски/решения**: 500/503 — retry; token expired — авто-регенация; демо-задержки — доп. SIM.
- **Выход**: Рабочий чат с API-доступом.

##### Этап 2: LLM-Логика и Парсинг
- **Архитектура обработки**: 1. Парсинг намерения (тип: портфель/данные/торговля); 2. Извлечение параметров (тикер/период/цена); 3. Генерация API-запроса; 4. Анализ ответа (саммари).
- **Задачи**: Промпты в core/llm.py (few-shot на train.csv); парсинг (YDEX@TQBR, TIME_FRAME_MN3); анализ (LLM-саммари); безопасность (подтверждение для NewOrder).
- **Пример промпта/модели** (core/llm.py):
  ```python
  class TradingIntent:
      method: str           # "GetPortfolios"
      params: Dict[str, Any] # {"account_id": "demo"}
      confirmation_required: bool = False
      visualization_type: str = None  # "chart", "table"
  prompt = """
  Ты - AI-ассистент трейдера. Преобразуй запрос в вызов Finam API.
  Методы: GetPortfolios(account_id), GetBars(symbol, timeframe, from, to), GetAssets()...
  Запрос: "Покажи позиции по Сбербанку"
  Ответ: {"method": "GetPortfolios", "params": {"account_id": "demo"}}
  """
  def confirm_dangerous_actions(intent, params):
      if intent.method in ["NewOrder", "NewStop", "CancelOrder"]:
          return f"Подтвердите: {intent.method} с {params}"
      return None
  ```
- **Риски/решения**: Неточность — chain-of-thought; бюджет — тесты на mini.
- **Выход**: Корректные запросы для submission.csv (`make generate`, accuracy >0.87 via `make metrics`).

##### Этап 3: Интеграция API и MVP-Сценарии
- **Задачи**: Адаптировать adapters (gRPC stubs из proto); FinamPy для методов; базовые сценарии (#1: портфель/котировки/поиск/история); обработка (даты via GetTime, ошибки trades); асинхронность (asyncio для stream).
- **Обязательные сценарии**:
  1. "Что в портфеле?" → GetPortfolios.
  2. "Цена SBER?" → GetLastQuote("SBER@TQBR").
  3. "Акции Газпрома" → GetAssets (фильтр).
  4. "График SBER за неделю" → GetBars (D1).
- **Риски/решения**: Демо — симуляция (AAPL@XNYS); тикеры — проверка GetAssets.
- **Выход**: Запрос → API → ответ в чате.

##### Этап 4: Визуализация и UI
- **Задачи**: В interfaces: Markdown для таблиц/графиков; типы (#1: sunburst/свечи/таблицы/sparklines/кривые); UX (отзывчивость, темы).
- **Пример кода** (interfaces/chat_app.py):
  ```python
  import plotly.graph_objects as go
  def create_sunburst_chart(sectors):
      return go.Figure(go.Sunburst(...)).to_html()
  def create_performance_chart(history):
      return go.Figure(go.Scatter(...)).to_html()
  ```
- **Риски/решения**: Неинтерактивность — Plotly embed; базовый UI +баллы (20%).
- **Выход**: Чат с визуализацией.

##### Этап 5: Продвинутые Кейсы и Безопасность
- **Кейс 1: Портфельный Аналитик**:
  ```python
  def analyze_portfolio(account_id):
      portfolio = GetPortfolios(account_id)
      assets = GetAssets()
      sectors = group_by_sector(portfolio.positions, assets)
      fig_sunburst = create_sunburst_chart(sectors)
      fig_performance = create_performance_chart(portfolio.history)
      summary = llm_analyze(portfolio, sectors)  # "Доходность +15%..."
      return summary, [fig_sunburst, fig_performance]
  ```
- **Кейс 2: Рыночный Сканер**: Фильтры (сектор/динамика/объемы) → GetAssets/GetBars → Таблица с sparklines.
- **Кейс 3: Песочница Стратегий**: Бэктест (GetBars) → Метрики (Sharpe/просадка) → Графики входов/кривая доходности.
- **Безопасность**: Интегрировать confirm_dangerous_actions.
- **Риски/решения**: Демо-позиции — симуляция; тесты на AAPL@XNYS.
- **Выход**: Кейсы в чате, видео для питча (+30% за глубину).

##### Этап 6: Тестирование, Submission и Питч
- **Задачи**: Тесты на test.csv/демо; submission CSV (50/день); GitHub (README/DEVELOPMENT.md); питч (5 мин: идея/демо/архитектура/планы; QR/скринкаст).
- **Метрики**: Лидерборд (70%: accuracy); Питч (30%: кейсы/техника/AI/безопасность).
- **Риски/решения**: Низкий LB — оптимизировать промпты; сбой — видео.
- **Выход**: Топ-20, сильный питч.

#### Технические Детали
- **Обработка ошибок**: Retry (exponential backoff); кэширование GetAssets; тикеры (SBER@TQBR).
- **Рекомендации для победы**: Фокус на accuracy (70%); 1+ кейс; подтверждения (+10%); UI (Streamlit); демо-сценарий.
- **Критические моменты**: Только Finam API; JWT-обновление; демо-ограничения; лимит 200 req/min.

Этот план полон, с акцентом на структуру проекта, и готов к реализации/питчу. Развитие: Voice-mode, X-интеграция.
