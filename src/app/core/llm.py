from typing import Any, List, Dict, Optional
import re
import json
import requests
from dataclasses import dataclass

from src.app.core.config import get_settings


@dataclass
class TradingIntent:
    """Класс для представления торгового намерения"""
    method: str
    path: str
    parameters: Dict[str, Any]
    confirmation_required: bool = False


class LLMProcessor:
    """
    Процессор LLM для парсинга запросов и вызова OpenRouter
    """
    def __init__(self):
        self.settings = get_settings()
        self.client = requests.Session()
        self.client.headers.update({
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
        })

    def create_few_shot_prompt(self, question: str, examples: List[Dict[str, str]], max_examples: int = 10) -> str:
        """
        Создать few-shot промпт для извлечения торгового намерения
        """
        # Выбираем разнообразные примеры из train.csv
        get_examples = [ex for ex in examples if ex["type"] == "GET"][:max_examples//2]
        other_examples = [ex for ex in examples if ex["type"] != "GET"][:max_examples//2]
        
        prompt = """Ты - эксперт по Finam TradeAPI. Твоя задача - проанализировать вопрос трейдера и извлечь точное намерение в формате TradingIntent.

Формат ответа: JSON с полями:
{
    "method": "HTTP_METHOD",
    "path": "/v1/api/path",
    "parameters": {"param": "value"},
    "confirmation_required": true/false,
    "reasoning": "Краткое объяснение CoT"
}

Доступные API эндпоинты (строго следуй документации Finam TradeAPI):
- GET /v1/accounts/{account_id} - информация о счете и позиции
- GET /v1/accounts/{account_id}/orders - список ордеров
- GET /v1/accounts/{account_id}/orders/{order_id} - детали ордера
- GET /v1/accounts/{account_id}/trades - история сделок (на демо "no data")
- GET /v1/accounts/{account_id}/transactions - транзакции (на демо "no data")
- POST /v1/sessions/details - детали сессии (JWT, права доступа)
- GET /v1/assets - список инструментов
- GET /v1/assets/{symbol} - информация об инструменте (лот, шаг цены)
- GET /v1/assets/{symbol}/params?account_id={account_id} - параметры для счета
- GET /v1/assets/{symbol}/options - опционы на базовый актив
- GET /v1/assets/{symbol}/schedule - расписание торгов
- GET /v1/instruments/{symbol}/quotes/latest - текущая котировка
- GET /v1/instruments/{symbol}/orderbook - биржевой стакан
- GET /v1/instruments/{symbol}/trades/latest - последние сделки
- GET /v1/instruments/{symbol}/bars?timeframe={tf}&interval.start_time={start}&interval.end_time={end} - исторические бары

Параметры для bars:
- timeframe: TIME_FRAME_M1/M5/M15/M30/H1/H4/D/W/MN
- interval.start_time/end_time: ISO 8601 (UTC), e.g. "2025-09-01T00:00:00Z"

Символы: ticker@mic (SBER@MISX, AAPL@XNGS, YDEX@TQBR, RIZ5@RTSX)
Демо-ограничения: Нет trades/transactions (код 13, "no data"), только условные/лимитные ордера.

Примеры (few-shot из train.csv):

"""
        
        for ex in get_examples + other_examples[:3]:  # Баланс примеров
            prompt += f'Вопрос: "{ex["question"]}"\n'
            intent = {
                "method": ex["type"],
                "path": ex["request"],
                "parameters": {},  # Извлечь параметры (тикер из пути)
                "confirmation_required": ex["type"] in ["POST", "DELETE"],
                "reasoning": f"Из вопроса извлечен {ex['type']} запрос для {ex['request']}"
            }
            prompt += f'TradingIntent: {json.dumps(intent, ensure_ascii=False)}\n\n'

        prompt += f"""**Chain of Thought (CoT):**
1. Определи намерение: {question}
2. Извлеки параметры: тикер (SBER@MISX), account_id (если нужно), order_id (для отмены), timeframe (M1/D/W), даты (за неделю/месяц).
3. Выбери endpoint: Сопоставь с документацией API.
4. Учти безопасность: confirmation_required=True для POST/DELETE.
5. Обработай edge cases: YNDX→YDEX, "no data" для trades.

Вопрос: "{question}"
TradingIntent (JSON): """

        return prompt

    def extract_intent(self, question: str, train_examples: List[Dict[str, str]]) -> TradingIntent:
        """
        Извлечь торговое намерение из вопроса с помощью LLM
        
        Args:
            question: Вопрос пользователя
            train_examples: Примеры из train.csv для few-shot
            
        Returns:
            TradingIntent объект
        """
        prompt = self.create_few_shot_prompt(question, train_examples)
        
        messages = [
            {"role": "system", "content": "Ты эксперт по Finam TradeAPI. Отвечай только валидным JSON с TradingIntent."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.post(
                f"{self.settings.openrouter_base}/chat/completions",
                json={
                    "model": self.settings.openrouter_model,
                    "messages": messages,
                    "temperature": 0.1,  # Низкая температура для точности
                    "max_tokens": 300,
                    "response_format": {"type": "json_object"}  # Structured output
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Парсим JSON
            intent_data = json.loads(content)
            
            # Нормализуем path: заменяем плейсхолдеры на параметры
            path = intent_data.get("path", "/v1/assets")
            parameters = intent_data.get("parameters", {})
            
            # Замена плейсхолдеров в path
            for placeholder, value in parameters.items():
                path = path.replace(f"{{{placeholder}}}", str(value))
            
            return TradingIntent(
                method=intent_data.get("method", "GET"),
                path=path,
                parameters=parameters,
                confirmation_required=intent_data.get("confirmation_required", False)
            )
            
        except Exception as e:
            # Fallback: базовый парсинг
            import re
            method_match = re.search(r'\b(GET|POST|DELETE)\b', question.upper())
            method = method_match.group(1) if method_match else "GET"
            
            # Извлекаем тикер (простой паттерн)
            ticker_match = re.search(r'(?:акций|фьючерс|опцион|инструмент)\s+([A-Z]+(?:@\w+)?)', question.upper())
            symbol = ticker_match.group(1) if ticker_match else "SBER@MISX"
            
            path = f"/v1/instruments/{symbol}/quotes/latest"
            if method == "POST":
                path = f"/v1/accounts/{{account_id}}/orders"
            elif method == "DELETE":
                path = f"/v1/accounts/{{account_id}}/orders/{{order_id}}"
            
            return TradingIntent(
                method=method,
                path=path,
                parameters={"symbol": symbol},
                confirmation_required=method in ["POST", "DELETE"]
            )

    def call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Вызов LLM через OpenRouter (универсальный метод)
        """
        payload = {
            "model": self.settings.openrouter_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        response = self.client.post(
            f"{self.settings.openrouter_base}/chat/completions",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def generate_analysis(self, api_response: Dict[str, Any], question: str) -> str:
        """
        Сгенерировать текстовый анализ на основе API ответа
        """
        messages = [
            {"role": "system", "content": "Ты финансовый аналитик. Проанализируй данные API и дай краткий информативный ответ на русском."},
            {"role": "user", "content": f"Вопрос: {question}\nДанные API: {json.dumps(api_response, ensure_ascii=False, indent=2)}"}
        ]
        
        try:
            response = self.call_llm(messages, temperature=0.3, max_tokens=400)
            return response["choices"][0]["message"]["content"]
        except Exception:
            # Fallback анализ
            if isinstance(api_response, dict) and "error" in api_response:
                return f"⚠️ Ошибка API: {api_response['error']}. Проверьте параметры запроса."
            elif isinstance(api_response, list) and api_response:
                if "close" in api_response[0]:
                    latest_price = api_response[-1]["close"]
                    return f"✅ Последняя цена: {latest_price:.2f}"
            return "Данные получены. Информация о балансе, позициях или котировках доступна."
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
