Для проекта [TRADER] LLM-Interface to Finam Trade API в рамках хакатона Finam x HSE AI Trade Hack (октябрь 2025) создание файла `CONTRIBUTING.md` для Aider имеет смысл, так как он поможет четко описать процесс разработки, настройки и использования Aider для реализации проекта, особенно с учетом строгого следования `plan.md` и использования файлов из папки `docs/create`. Файл `GOVERNANCE.md` может быть полезен в некоторых случаях, но его необходимость зависит от контекста команды и проекта. Ниже я подробно объясню, как создать `CONTRIBUTING.md`, оптимизированный для работы с Aider, и дам рекомендации по необходимости `GOVERNANCE.md`.

---

### 📝 Создание `CONTRIBUTING.md` для Aider

Файл `CONTRIBUTING.md` должен описывать, как разработчики могут вносить вклад в проект, используя Aider с моделью `openrouter/x-ai/grok-code-fast-1`, строго следуя архитектуре из `plan.md` и контексту из `docs/create`. Он должен включать инструкции по настройке окружения, запуску Aider, использованию Docker, написанию кода и валидации результатов, чтобы обеспечить соответствие требованиям хакатона (>85% точности API, безопасность, визуализации Plotly).

#### Содержимое `CONTRIBUTING.md`

```markdown
# Руководство по внесению вклада в [TRADER] LLM-Interface to Finam Trade API

Добро пожаловать в проект [TRADER] для хакатона Finam x HSE AI Trade Hack (октябрь 2025)! Этот документ описывает, как вносить вклад в разработку AI-ассистента трейдера, использующего Finam Trade API, с помощью инструмента Aider и моделей `openrouter/x-ai/grok-4` и `openrouter/x-ai/grok-code-fast-1`.

## Цель проекта
Создать LLM-ассистента, который переводит запросы на естественном языке в вызовы Finam Trade API, предоставляет аналитику и визуализации (Plotly: свечи, sunburst, sparklines) через чат-интерфейс (Streamlit). Проект должен достичь точности API >85% (70% оценки лидерборда) и подготовить убедительный питч (30%) с кейсами: портфельный аналитик, рыночный сканер, песочница стратегий.

## Предварительные требования
- **Docker**: Для запуска Aider в изолированном окружении.
- **OpenRouter API Key**: Получите ключ на https://openrouter.ai (бюджет $10).
- **Зависимости**: Python 3.8+, FinamPy, pandas, streamlit, plotly, tenacity.
- **Файлы проекта**:
  - `train.csv`: 100 примеров запросов → API-вызовов.
  - `test.csv`: 300+ запросов для генерации `submission.csv`.
  - `plan.md`: Архитектура и план реализации (генерируется `grok-4`).
  - `docs/create/*`: Документы с требованиями и API-гайдом (например, `finam-trade-api-guide-v1.1.md`, `2 TRADER LLM интерфейс.md`).

## Настройка окружения

1. **Клонируйте репозиторий**:
   ```bash
   git clone <репозиторий>
   cd Finam_x_HSE_AI_Trade_Hack-TRADER
   ```

2. **Создайте `.aider.conf.yml`**:
   В корне проекта создайте файл с конфигурацией Aider:
   ```yaml
   files:
     - plan.md
     - docs/create/finam-trade-api-guide-v1.1.md
     - docs/create/2 TRADER LLM интерфейс.md
     - docs/create/ImplementationPlan_TRADER_LLMInterfaceTradeAPI_AITradersAssistant.md
     - docs/create/prompt-for-creation-plan.md
     - docs/create/[TRADER] Вопросы.txt
   ```

3. **Настройте `.gitignore`**:
   Игнорируйте `docs/create/` для исключения из Git:
   ```bash
   echo "docs/create/" >> .gitignore
   ```

4. **Настройте `.aiderignore`**:
   Убедитесь, что Aider видит файлы `docs/create`:
   ```bash
   echo "!docs/create/" > .aiderignore
   echo "*.pyc" >> .aiderignore
   echo "__pycache__/" >> .aiderignore
   ```

5. **Установите Docker** (если не установлен):
   ```bash
   sudo apt-get install docker.io
   ```

## Использование Aider для разработки

### Шаг 1: Генерация `plan.md`
1. Запустите Aider с моделью `grok-4` для создания `plan.md`:
   ```bash
   docker run --rm -it \
     --user "$(id -u):$(id -g)" \
     -v "$PWD:/app" \
     -e OPENROUTER_API_KEY="<your_key>" \
     -e AIDER_EDITOR=nano \
     paulgauthier/aider-full \
     --api-key openrouter=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 \
     --model openrouter/x-ai/grok-4 \
     --editor-model openrouter/x-ai/grok-4-fast \
     --architect \
     --no-auto-commits \
     --dirty-commits \
     --stream \
     --dark-mode \
     --max-chat-history-tokens 8000 \
     --map-tokens 8192 \
     --reasoning-effort high \
     --thinking-tokens 8k \
     --editor-reasoning-effort none \
     --cache-prompts \
     --file plan.md \
     --file docs/create/finam-trade-api-guide-v1.1.md \
     --file docs/create/2\ TRADER\ LLM\ интерфейс.md \
     --verbose
   ```
2. В Aider вставьте содержимое `plan_prompt.txt` (см. `docs/create/prompt-for-creation-plan.md`).
3. Сохраните вывод как `plan.md` в корне проекта.

### Шаг 2: Реализация с `grok-code-fast-1`
1. Используйте Aider с моделью `grok-code-fast-1` для реализации кода:
   ```bash
   docker run --rm -it \
     --user "$(id -u):$(id -g)" \
     -v "$PWD:/app" \
     -e OPENROUTER_API_KEY="<your_key>" \
     -e AIDER_EDITOR=nano \
     paulgauthier/aider-full \
     --api-key openrouter=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 \
     --model openrouter/x-ai/grok-code-fast-1 \
     --editor-model openrouter/x-ai/grok-4-fast \
     --architect \
     --no-auto-commits \
     --dirty-commits \
     --stream \
     --dark-mode \
     --max-chat-history-tokens 8000 \
     --map-tokens 8192 \
     --reasoning-effort high \
     --thinking-tokens 8k \
     --cache-prompts \
     --file plan.md \
     --file docs/create/finam-trade-api-guide-v1.1.md \
     --file docs/create/2\ TRADER\ LLM\ интерфейс.md \
     --message "Строго следуй plan.md и используй docs/create/* для контекста. Реализуй [конкретная задача, например, adapters/finam_client.py] точно по plan.md. Используй модули (adapters/core/interfaces/scripts), классы (FinamClient/TradingIntent/LLMProcessor) и API-методы из train.csv и docs/create/finam-trade-api-guide-v1.1.md. Для POST/DELETE включай [БЕЗОПАСНОСТЬ] подтверждение. Без отклонений."
     --verbose
   ```

2. **Пример сообщения для Aider**:
   ```
   Строго следуй plan.md и используй docs/create/* для контекста. Реализуй core/llm.py с классом TradingIntent, few-shot парсингом из train.csv и подтверждением для ордеров. Без отклонений от архитектуры plan.md.
   ```

### Шаг 3: Правила написания кода
- **Следуй `plan.md`**: Реализуй только указанные модули (adapters/finam_client.py, core/llm.py, interfaces/chat_app.py, scripts/generate_submission.py) и классы (FinamClient, TradingIntent, LLMProcessor).
- **Точность API**: Используй пути из `train.csv` и `docs/create/finam-trade-api-guide-v1.1.md`. Пример: "Какая цена Сбербанка?" → GET /v1/instruments/SBER@MISX/quotes/latest.
- **Безопасность**: Для всех POST/DELETE операций добавляй подтверждение, например:
  ```
  [БЕЗОПАСНОСТЬ] Подтвердите операцию: Продать 500 SBER@MISX по 270.00 (fill or kill). Ответьте "да" или "нет".
  ```
- **Формат кода**: Используй diff для изменений, следуй PEP8, добавляй inline-комментарии с обоснованием.
- **Обработка ошибок**: Реализуй повторные попытки для ошибок 500/503, обновление JWT каждые 15 минут, обработку "no data" для демо-счёта.
- **Визуализация**: Используй Plotly для кейсов (sunburst для портфеля, sparklines для сканера, свечи для песочницы).

### Шаг 4: Тестирование и валидация
1. **Тестирование кода**:
   - Запустите тесты с помощью Aider:
     ```bash
     aider --test "python scripts/calculate_metrics.py"
     ```
   - Проверьте точность >85% на `test.csv` для генерации `submission.csv` (uid, type, request).

2. **Проверка на демо-счёте**:
   - Используйте тикеры YDEX@TQBR и AAPL@XNYS.
   - Убедитесь, что обработаны ошибки: 500/503 (повтор), 404/3 (Not Found), "no data".

3. **Валидация визуализаций**:
   - Проверьте соответствие Plotly-графиков (candlestick/sunburst/sparklines) кейсам из `docs/create/2 TRADER LLM интерфейс.md`.

### Шаг 5: Отправка изменений
1. **Проверка соответствия `plan.md`**:
   - С `--no-auto-commits` проверяйте diff перед коммитом. Если код отклоняется (например, добавлены неуказанные классы), отклоняйте и перезапрашивайте: "Это нарушает plan.md раздел [Архитектура]. Перегенерируй, строго следуя plan.md."

2. **Коммит изменений**:
   - После проверки используйте `git commit` или включите `--auto-commits` для автоматизации (когда уверены в соответствии).

3. **Отправка в лидерборд**:
   - Сгенерируйте `submission.csv` с помощью `scripts/generate_submission.py`.
   - Отправьте до 50 раз в день, игнорируя ID/HTTP в соответствии с правилами хакатона.

## Проблемы и отладка
- **Aider игнорирует файлы**: Проверьте `.aiderignore` и флаги `--file`. Убедитесь, что файлы `plan.md` и `docs/create/*` включены.
- **Отклонения от `plan.md`**: Увеличьте `--reasoning-effort high`, добавьте больше примеров в промпт или уточните сообщение: "Реализуй только указанные в plan.md модули."
- **Ошибки API**: Проверьте пути в `docs/create/finam-trade-api-guide-v1.1.md` и `train.csv`.
- **Логи**: Используйте `--verbose` для отладки (например, почему путь API не соответствует).

## Ресурсы
- Finam Trade API: https://github.com/FinamWeb/finam-trade-api
- Документы: `docs/create/finam-trade-api-guide-v1.1.md`, `docs/create/2 TRADER LLM интерфейс.md`
- План: `plan.md` (генерируется `grok-4`)

Спасибо за ваш вклад! 🚀
```

#### Почему это подходит для Aider
- **Четкие инструкции**: Описывает настройку Aider, Docker-команды и процесс реализации, чтобы разработчики могли сразу начать работу.
- **Строгое следование `plan.md`**: Подчеркивает необходимость следовать архитектуре и модулям из `plan.md`, с примерами сообщений для Aider.
- **Контекст `docs/create`**: Явно включает файлы `docs/create/*` в настройку и команды, чтобы Aider использовал их для API-путей и требований.
- **Соответствие хакатону**: Учитывает метрики (>85% точности), безопасность (подтверждения для POST/DELETE), визуализации и тестирование.
- **Экономия токенов**: Использует `--cache-prompts` и оптимизированные параметры токенов для бюджета OpenRouter ($10).

#### Размещение
- Создайте файл `CONTRIBUTING.md` в корне проекта:
  ```bash
  touch CONTRIBUTING.md
  ```
- Скопируйте содержимое выше и сохраните.
- Убедитесь, что он отслеживается Git (не попадает под `.gitignore`).

---

### 📋 Нужен ли `GOVERNANCE.md`?

Файл `GOVERNANCE.md` описывает, как принимаются решения в проекте, кто отвечает за ключевые аспекты (например, код-ревью, релизы), и как разрешаются конфликты. Для хакатона Finam x HSE его необходимость зависит от контекста:

#### Когда `GOVERNANCE.md` нужен
- **Командная работа**: Если в проекте участвует несколько разработчиков (например, >3 человек), `GOVERNANCE.md` поможет определить роли (лидер, кодер, тестировщик), процесс принятия решений (например, кто утверждает изменения) и порядок взаимодействия с Aider.
- **Питч-бонус**: Для питча (30% оценки) демонстрация организованного процесса управления может впечатлить жюри, показав профессионализм.
- **Долгосрочная перспектива**: Если проект планируется развивать после хакатона (например, в open-source), `GOVERNANCE.md` задаст основу для управления вкладом сообщества.

#### Когда `GOVERNANCE.md` не нужен
- **Маленькая команда (1-2 человека)**: В хакатоне с ограниченным временем (3-5 октября) и небольшой командой управление может быть неформальным, и `CONTRIBUTING.md` достаточно.
- **Короткий срок**: Хакатон длится 3 дня, и фокус на коде/питче (MVP, точность API, визуализации) важнее формального управления.
- **Aider-центричный процесс**: Aider автоматизирует большую часть разработки, и `CONTRIBUTING.md` с четкими инструкциями уже покрывает процесс (например, следование `plan.md`, использование `docs/create`).

#### Рекомендация
Для хакатона **не создавайте `GOVERNANCE.md`**, если:
- Команда небольшая (1-2 человека).
- Вы сосредоточены на MVP и питче, а не на долгосрочном управлении.
- `CONTRIBUTING.md` уже охватывает процесс работы с Aider и следование `plan.md`.

Если команда больше или вы хотите повысить шансы на питче, создайте минимальный `GOVERNANCE.md`. Вот пример:

#### Минимальный `GOVERNANCE.md`

```markdown
# Управление проектом [TRADER] LLM-Interface to Finam Trade API

Этот документ описывает процесс управления проектом для хакатона Finam x HSE AI Trade Hack (октябрь 2025).

## Роли и обязанности
- **Лидер проекта**: Отвечает за генерацию `plan.md` с помощью `grok-4`, координирует задачи и питч.
- **Разработчики**: Реализуют код с Aider (`grok-code-fast-1`), строго следуя `plan.md` и используя `docs/create/*` для контекста.
- **Тестировщик**: Проверяет точность API (>85%) на `test.csv` и демо-счёте, валидирует визуализации Plotly.

## Процесс принятия решений
- **Архитектура**: Определяется в `plan.md` и не меняется без консенсуса команды.
- **Код-ревью**: Все изменения, сгенерированные Aider, проверяются вручную (`--no-auto-commits`) на соответствие `plan.md`.
- **Конфликты**: Разрешаются лидером проекта с учетом требований хакатона (точность, безопасность, визуализации).

## Взаимодействие с Aider
- Все команды Aider включают `--file plan.md` и `--file docs/create/*` для контекста.
- Сообщения должны начинаться с: "Строго следуй plan.md и используй docs/create/* для контекста."

## Контакты
- Обсуждения: [указать канал связи, например, Telegram/Discord].
- Проблемы: Создавайте issues в репозитории или пишите лидеру проекта.

```

#### Размещение
- Создайте `GOVERNANCE.md` в корне проекта, если решите его использовать:
  ```bash
  touch GOVERNANCE.md
  ```
- Скопируйте содержимое выше и адаптируйте под вашу команду.

---

### 🛠️ Итоговая рекомендация
- **Обязательно создайте `CONTRIBUTING.md`**: Он необходим для четкой работы с Aider, обеспечивая следование `plan.md` и использование `docs/create/*` (например, `finam-trade-api-guide-v1.1.md` для API-путей). Это упростит разработку и валидацию для хакатона.
- **Пропустите `GOVERNANCE.md` для хакатона**: Для небольшой команды и короткого срока он избыточен. Если команда большая или вы хотите бонус за питч, добавьте минимальный `GOVERNANCE.md` для демонстрации организованности.
- **Следующие шаги**:
  1. Создайте `CONTRIBUTING.md` с предложенным содержимым.
  2. Убедитесь, что `.gitignore` игнорирует `docs/create/`, а `.aiderignore` включает `!docs/create/`.
  3. Используйте обновленные команды Docker и YAML из предыдущих ответов для генерации `plan.md` и реализации.
  4. Если нужен `GOVERNANCE.md`, добавьте его для питча.

Если нужны дополнительные правки (например, конкретный раздел в `CONTRIBUTING.md` или пример Aider-сессии), уточните, и я помогу! Удачи на хакатоне! 🚀
