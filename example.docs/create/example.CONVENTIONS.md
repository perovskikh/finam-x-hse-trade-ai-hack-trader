# CONVENTIONS.md
# Правила проекта [TRADER] LLM-Interface to Finam Trade API

## Язык разработки
- Основной язык: Python 3.12+.
- Комментарии: На русском для ТЗ/требований, на английском для кода (PEP8).
- Документация: Markdown на русском (например, plan.md, CONTRIBUTING.md).

## Предпочтительные библиотеки
- API: FinamPy (для Finam Trade API), tenacity (для retry ошибок 500/503).
- LLM: OpenRouter.ai (модели grok-4/grok-code-fast-1).
- Визуализация: Plotly (candlestick/sunburst/sparklines для кейсов).
- UI: Streamlit (чат-интерфейс).
- Данные: Pandas (таблицы, submission.csv).
- Тестирование: Aider с make metrics для accuracy >85%.

## Архитектурные решения
- Строго следовать plan.md: Модули (adapters/core/interfaces/scripts), классы (FinamClient/TradingIntent/LLMProcessor).
- Безопасность: Обязательное подтверждение для POST/DELETE с шаблоном "[БЕЗОПАСНОСТЬ] Подтвердите...".
- Обработка ошибок: Retry 500/503, обновление JWT каждые 15 мин, "no data" для демо.
- Контекст: Использовать docs/create/* (API-гайд, ТЗ кейсов).
- Тестирование: На test.csv/demo-счёте (YDEX@TQBR, AAPL@XNYS), цель >85% accuracy.
- Стиль кода: PEP8, inline-комментарии с обоснованием (почему метод, как ошибка обрабатывается).

# Стандарты разработки

- Читаемость: Лучше ясный и многословный код, чем умный, но запутанный.
- Покрытие тестами: Явно документировать каждую функцию, у которой нет теста.
- Качество тестов: Избегать использования моков в тестах.

## Другие правила
- Нет отклонений от plan.md без обсуждения.
