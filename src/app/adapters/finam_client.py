"""
Клиент для работы с Finam TradeAPI
https://tradeapi.finam.ru/
"""

import asyncio
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import os
from typing import Any

import requests


class FinamAPIClient:
    """
    Клиент для взаимодействия с Finam TradeAPI

    Документация: https://tradeapi.finam.ru/
    """

    def __init__(self, access_token: str | None = None, base_url: str | None = None) -> None:
        """
        Инициализация клиента

        Args:
            access_token: Токен доступа к API (из переменной окружения FINAM_ACCESS_TOKEN)
            base_url: Базовый URL API (по умолчанию из документации)
        """
        self.access_token = access_token or os.getenv("FINAM_ACCESS_TOKEN", "")
        self.base_url = base_url or os.getenv("FINAM_API_BASE_URL", "https://api.finam.ru")
        self.session = requests.Session()
        self.jwt_expiry = datetime.now() + timedelta(minutes=15)  # Инициализация для refresh

        if self.access_token:
            self.session.headers.update({
                "Authorization": self.access_token,  # No "Bearer" prefix for Finam API
                "Content-Type": "application/json",
            })

    async def refresh_jwt(self):
        """Асинхронное обновление JWT токена каждые 15 мин"""
        # Логика refresh (используйте Finam API для /v1/sessions)
        response = await asyncio.to_thread(self.execute_request, "POST", "/v1/sessions")
        if "access_token" in response:
            self.access_token = response["access_token"]
            self.session.headers["Authorization"] = self.access_token  # No "Bearer"
            self.jwt_expiry = datetime.now() + timedelta(minutes=15)
        return response

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.HTTPError)
    )
    def execute_request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        """
        Выполнить HTTP запрос к Finam TradeAPI

        Args:
            method: HTTP метод (GET, POST, DELETE и т.д.)
            path: Путь API (например, /v1/instruments/SBER@MISX/quotes/latest)
            **kwargs: Дополнительные параметры для requests
        # Критически важно: Подтверждение для POST/DELETE
        if method in ["POST", "DELETE"]:
            confirm = input(f"[БЕЗОПАСНОСТЬ] Подтвердите операцию: {method} {path} (да/нет): ")
            if confirm.lower() != "да":
                return {"status": "cancelled", "message": "Операция отменена"}

        Returns:
            Ответ API в виде словаря

        Raises:
            requests.HTTPError: Если запрос завершился с ошибкой
        """
        url = f"{self.base_url}{path}"
        # Проверка JWT expiry
        if datetime.now() > self.jwt_expiry:
            asyncio.run(self.refresh_jwt())

        try:
            resp = self.session.request(method, url, timeout=30, **kwargs)
            if resp.status_code in [500, 503]:
                raise requests.HTTPError("Retryable error")
            resp.raise_for_status()

            # Если ответ пустой (например, для DELETE)
            if not resp.content:
                return {"status": "success", "message": "Operation completed"}

            return resp.json()

        except requests.exceptions.HTTPError as e:
            # Пытаемся извлечь детали ошибки из ответа
            error_detail = {"error": str(e), "status_code": e.response.status_code if e.response else None}

            try:
                if e.response and e.response.content:
                    error_detail["details"] = e.response.json()
            except Exception:
                error_detail["details"] = e.response.text if e.response else None

            return error_detail

        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}

    # Удобные методы для частых операций

    def get_quote(self, symbol: str) -> dict[str, Any]:
        """Получить текущую котировку инструмента"""
        return self.execute_request("GET", f"/v1/instruments/{symbol}/quotes/latest")

    def get_orderbook(self, symbol: str, depth: int = 10) -> dict[str, Any]:
        """Получить биржевой стакан"""
        return self.execute_request("GET", f"/v1/instruments/{symbol}/orderbook", params={"depth": depth})

    def get_candles(
        self, symbol: str, timeframe: str = "D", start: str | None = None, end: str | None = None
    ) -> dict[str, Any]:
        """Получить исторические свечи"""
        params = {"timeframe": timeframe}
        if start:
            params["interval.start_time"] = start
        if end:
            params["interval.end_time"] = end
        return self.execute_request("GET", f"/v1/instruments/{symbol}/bars", params=params)

    # Метод по train.csv: "Покажи мой портфель" → GET /v1/portfolios (но в API это /v1/accounts/{account_id})
    async def get_portfolios(self, account_id: str) -> dict[str, Any]:
        """Получить портфель (позиции) по счету"""
        return await asyncio.to_thread(self.execute_request, "GET", f"/v1/accounts/{account_id}")

    def get_account(self, account_id: str) -> dict[str, Any]:
        """Получить информацию о счете"""
        return self.execute_request("GET", f"/v1/accounts/{account_id}")

    def get_orders(self, account_id: str) -> dict[str, Any]:
        """Получить список ордеров"""
        return self.execute_request("GET", f"/v1/accounts/{account_id}/orders")

    def get_order(self, account_id: str, order_id: str) -> dict[str, Any]:
        """Получить информацию об ордере"""
        return self.execute_request("GET", f"/v1/accounts/{account_id}/orders/{order_id}")

    def create_order(self, account_id: str, order_data: dict[str, Any]) -> dict[str, Any]:
        """Создать новый ордер"""
        return self.execute_request("POST", f"/v1/accounts/{account_id}/orders", json=order_data)

    def cancel_order(self, account_id: str, order_id: str) -> dict[str, Any]:
        """Отменить ордер"""
        return self.execute_request("DELETE", f"/v1/accounts/{account_id}/orders/{order_id}")

    def get_trades(self, account_id: str, start: str | None = None, end: str | None = None) -> dict[str, Any]:
        """Получить историю сделок"""
        params = {}
        if start:
            params["interval.start_time"] = start
        if end:
            params["interval.end_time"] = end
        return self.execute_request("GET", f"/v1/accounts/{account_id}/trades", params=params)

    def get_positions(self, account_id: str) -> dict[str, Any]:
        """Получить открытые позиции"""
        # Позиции обычно включены в ответ get_account
        return self.execute_request("GET", f"/v1/accounts/{account_id}")

    def get_session_details(self) -> dict[str, Any]:
        """Получить детали текущей сессии"""
        return self.execute_request("POST", "/v1/sessions/details")
