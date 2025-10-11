from typing import Any

import requests

from .config import get_settings


def call_llm(messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int | None = None) -> dict[str, Any]:
    """Простой вызов LLM без tools"""
    s = get_settings()
    payload: dict[str, Any] = {
        "model": s.openrouter_model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    r = requests.post(
        f"{s.openrouter_base}/chat/completions",
        headers={
            "Authorization": f"Bearer {s.openrouter_api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def create_prompt(question: str, examples: list[dict[str, str]]) -> str:
    """Создать промпт для LLM с few-shot примерами"""
    prompt = """Ты - эксперт по Finam TradeAPI. Твоя задача - преобразовать вопрос на русском языке в HTTP запрос к API.

API Documentation:
- GET /v1/exchanges - список бирж
- GET /v1/assets - поиск инструментов
- GET /v1/assets/{symbol} - информация об инструменте
- GET /v1/assets/{symbol}/params - параметры инструмента для счета
- GET /v1/assets/{symbol}/schedule - расписание торгов
- GET /v1/assets/{symbol}/options - опционы на базовый актив
- GET /v1/instruments/{symbol}/quotes/latest - последняя котировка
- GET /v1/instruments/{symbol}/orderbook - биржевой стакан
- GET /v1/instruments/{symbol}/trades/latest - лента сделок
- GET /v1/instruments/{symbol}/bars - исторические свечи
  (параметры: timeframe, interval.start_time, interval.end_time)
- GET /v1/accounts/{account_id} - информация о счете
- GET /v1/accounts/{account_id}/orders - список ордеров
- GET /v1/accounts/{account_id}/orders/{order_id} - информация об ордере
- GET /v1/accounts/{account_id}/trades - история сделок
- GET /v1/accounts/{account_id}/transactions - транзакции по счету
- POST /v1/sessions - создание новой сессии
- POST /v1/sessions/details - детали текущей сессии
- POST /v1/accounts/{account_id}/orders - создание ордера
- DELETE /v1/accounts/{account_id}/orders/{order_id} - отмена ордера

Timeframes: TIME_FRAME_M1, TIME_FRAME_M5, TIME_FRAME_M15, TIME_FRAME_M30,
TIME_FRAME_H1, TIME_FRAME_H4, TIME_FRAME_D, TIME_FRAME_W, TIME_FRAME_MN

Примеры:

"""

    for ex in examples:
        prompt += f'Вопрос: "{ex["question"]}"\n'
        prompt += f'Ответ: {{"type": "{ex["type"]}", "request": "{ex["request"]}"}}\n\n'

    prompt += f'Вопрос: "{question}"\n'
    prompt += 'Ответ в формате JSON: {"type": "HTTP_METHOD", "request": "/path/to/endpoint"}'

    return prompt


def parse_llm_response(response: str) -> tuple[str, str]:
    """Парсинг ответа LLM в (type, request)"""
    response = response.strip()
    import json  # Для structured output
    try:
        parsed = json.loads(response)
        return parsed.get("type", "GET"), parsed.get("request", "/v1/assets")
    except json.JSONDecodeError:
        pass  # Fallback to original parsing

    # Ищем HTTP метод в начале или перед путем
    methods = ["GET", "POST", "DELETE", "PUT", "PATCH"]
    method = "GET"  # по умолчанию
    request = response

    # Пытаемся найти метод и путь
    import re
    pattern = r'\b(GET|POST|DELETE|PUT|PATCH)\s*/'
    match = re.search(pattern, response, re.IGNORECASE)
    if match:
        method = match.group(1).upper()
        # Извлекаем путь после метода
        start = match.end()
        request = response[start:].strip()
    else:
        # Fallback: ищем путь
        path_match = re.search(r'/\S+', response)
        if path_match:
            request = path_match.group(0)

    # Убираем лишние символы
    request = request.strip()
    if not request.startswith("/"):
        request = f"/{request}"

    # Fallback на безопасный вариант
    if not request.startswith("/v1/"):
        request = "/v1/assets"

    return method, request
from typing import Any

import requests

from .config import get_settings


def call_llm(messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int | None = None) -> dict[str, Any]:
    """Простой вызов LLM без tools"""
    s = get_settings()
    payload: dict[str, Any] = {
        "model": s.openrouter_model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    r = requests.post(
        f"{s.openrouter_base}/chat/completions",
        headers={
            "Authorization": f"Bearer {s.openrouter_api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def create_prompt(question: str, examples: list[dict[str, str]]) -> str:
    """Создать промпт для LLM с few-shot примерами"""
    prompt = """Ты - эксперт по Finam TradeAPI. Твоя задача - преобразовать вопрос на русском языке в HTTP запрос к API.

API Documentation:
- GET /v1/exchanges - список бирж
- GET /v1/assets - поиск инструментов
- GET /v1/assets/{symbol} - информация об инструменте
- GET /v1/assets/{symbol}/params - параметры инструмента для счета
- GET /v1/assets/{symbol}/schedule - расписание торгов
- GET /v1/assets/{symbol}/options - опционы на базовый актив
- GET /v1/instruments/{symbol}/quotes/latest - последняя котировка
- GET /v1/instruments/{symbol}/orderbook - биржевой стакан
- GET /v1/instruments/{symbol}/trades/latest - лента сделок
- GET /v1/instruments/{symbol}/bars - исторические свечи
  (параметры: timeframe, interval.start_time, interval.end_time)
- GET /v1/accounts/{account_id} - информация о счете
- GET /v1/accounts/{account_id}/orders - список ордеров
- GET /v1/accounts/{account_id}/orders/{order_id} - информация об ордере
- GET /v1/accounts/{account_id}/trades - история сделок
- GET /v1/accounts/{account_id}/transactions - транзакции по счету
- POST /v1/sessions - создание новой сессии
- POST /v1/sessions/details - детали текущей сессии
- POST /v1/accounts/{account_id}/orders - создание ордера
- DELETE /v1/accounts/{account_id}/orders/{order_id} - отмена ордера

Timeframes: TIME_FRAME_M1, TIME_FRAME_M5, TIME_FRAME_M15, TIME_FRAME_M30,
TIME_FRAME_H1, TIME_FRAME_H4, TIME_FRAME_D, TIME_FRAME_W, TIME_FRAME_MN

Примеры:

"""

    for ex in examples:
        prompt += f'Вопрос: "{ex["question"]}"\n'
        prompt += f'Ответ: {{"type": "{ex["type"]}", "request": "{ex["request"]}"}}\n\n'

    prompt += f'Вопрос: "{question}"\n'
    prompt += 'Ответ в формате JSON: {"type": "HTTP_METHOD", "request": "/path/to/endpoint"}'

    return prompt


def parse_llm_response(response: str) -> tuple[str, str]:
    """Парсинг ответа LLM в (type, request)"""
    response = response.strip()
    import json  # Для structured output
    try:
        parsed = json.loads(response)
        return parsed.get("type", "GET"), parsed.get("request", "/v1/assets")
    except json.JSONDecodeError:
        pass  # Fallback to original parsing

    # Ищем HTTP метод в начале или перед путем
    methods = ["GET", "POST", "DELETE", "PUT", "PATCH"]
    method = "GET"  # по умолчанию
    request = response

    # Пытаемся найти метод и путь
    import re
    pattern = r'\b(GET|POST|DELETE|PUT|PATCH)\s*/'
    match = re.search(pattern, response, re.IGNORECASE)
    if match:
        method = match.group(1).upper()
        # Извлекаем путь после метода
        start = match.end()
        request = response[start:].strip()
    else:
        # Fallback: ищем путь
        path_match = re.search(r'/\S+', response)
        if path_match:
            request = path_match.group(0)

    # Убираем лишние символы
    request = request.strip()
    if not request.startswith("/"):
        request = f"/{request}"

    # Fallback на безопасный вариант
    if not request.startswith("/v1/"):
        request = "/v1/assets"

    return method, request
