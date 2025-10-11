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
"""
Finam API Client для асинхронных вызовов к Finam Trade API.

Использует FinamPy для gRPC/REST, tenacity для retry (500/503),
кэширование для GetAssets, JWT refresh каждые 15 мин.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional

import tenacity
from finam import FinamPy  # Предполагается установка FinamPy

from src.app.core.config import get_settings

logger = logging.getLogger(__name__)


class FinamClient:
    """Клиент для Finam Trade API с async и retry."""

    def __init__(self):
        self.settings = get_settings()
        self.client = FinamPy(
            token=self.settings.finam_token,
            client_id=self.settings.finam_client_id,
        )
        self._jwt_expires_at = datetime.now() + timedelta(minutes=15)  # Инициализация JWT

    async def _refresh_jwt_if_needed(self):
        """Обновить JWT если истекло (каждые 15 мин)."""
        if datetime.now() >= self._jwt_expires_at:
            # Логика обновления JWT из FinamPy
            await self.client.refresh_token()
            self._jwt_expires_at = datetime.now() + timedelta(minutes=15)
            logger.info("JWT refreshed")

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    async def get_assets(self, symbol: str) -> Dict[str, Any]:
        """Получить информацию об инструменте (кэшировано)."""
        await self._refresh_jwt_if_needed()
        # Используем кэширование для GetAssets, как указано в plan.md
        return await self._cached_get_assets(symbol)

    @lru_cache(maxsize=128)
    async def _cached_get_assets(self, symbol: str) -> Dict[str, Any]:
        """Кэшированная версия GetAssets."""
        try:
            response = await self.client.get_assets(symbol=symbol)
            return response
        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                logger.warning(f"Asset {symbol} not found")
                return {"error": "Not Found"}
            raise

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    )
    async def get_quotes_latest(self, symbol: str) -> Dict[str, Any]:
        """Получить последнюю котировку."""
        await self._refresh_jwt_if_needed()
        try:
            response = await self.client.get_quotes_latest(symbol=symbol)
            return response
        except Exception as e:
            if "no data" in str(e).lower():
                return {"error": "no data"}
            raise

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    )
    async def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> List[Dict[str, Any]]:
        """Получить исторические свечи (async для производительности)."""
        await self._refresh_jwt_if_needed()
        # Форматируем параметры согласно Finam API спецификации из docs/create
        params = {
            "securityBoard": symbol.split('@')[1],
            "securityCode": symbol.split('@')[0],
            "timeFrame": timeframe,
            "intervalFrom": start.isoformat(),
            "intervalTo": end.isoformat(),
        }
        try:
            response = await self.client.get_day_candles(params)
            return response
        except Exception as e:
            if "no data" in str(e).lower():
                return []
            raise

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    )
    async def create_order(
        self, account_id: str, order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Создать ордер (с подтверждением в интерфейсе)."""
        await self._refresh_jwt_if_needed()
        # Подтверждение обрабатывается в интерфейсе, здесь только вызов
        response = await self.client.create_order(account_id=account_id, **order_data)
        return response

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    )
    async def cancel_order(self, account_id: str, order_id: str) -> Dict[str, Any]:
        """Отменить ордер."""
        await self._refresh_jwt_if_needed()
        response = await self.client.cancel_order(account_id=account_id, order_id=order_id)
        return response

    # Добавить другие методы по мере необходимости (GetPortfolios, SubscribeQuote async)
