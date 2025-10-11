#!/usr/bin/env python3
"""
Streamlit веб-интерфейс для AI ассистента трейдера

Использование:
    poetry run streamlit run src/app/chat_app.py
    streamlit run src/app/chat_app.py
"""

import json

import streamlit as st
import plotly.graph_objects as go  # Для визуализации

from src.app.adapters import FinamAPIClient
from src.app.core import call_llm, get_settings


def create_system_prompt() -> str:
    """Создать системный промпт для AI ассистента"""
    return """Ты - AI ассистент трейдера, работающий с Finam TradeAPI.

Когда пользователь задает вопрос о рынке, портфеле или хочет совершить действие:
1. Определи нужный API endpoint
2. Укажи запрос в формате: API_REQUEST: METHOD /path
3. После получения данных - проанализируй их и дай понятный ответ

Доступные endpoints:
- GET /v1/instruments/{symbol}/quotes/latest - котировка
- GET /v1/instruments/{symbol}/orderbook - стакан
- GET /v1/instruments/{symbol}/bars - свечи
- GET /v1/accounts/{account_id} - счет и позиции
- GET /v1/accounts/{account_id}/orders - ордера
- POST /v1/accounts/{account_id}/orders - создать ордер
- DELETE /v1/accounts/{account_id}/orders/{order_id} - отменить ордер

Отвечай на русском, кратко и по делу."""


def extract_api_request(text: str) -> tuple[str | None, str | None]:
    """Извлечь API запрос из ответа LLM"""
    if "API_REQUEST:" not in text:
        return None, None

    lines = text.split("\n")
    for line in lines:
        if line.strip().startswith("API_REQUEST:"):
            request = line.replace("API_REQUEST:", "").strip()
            parts = request.split(maxsplit=1)
            if len(parts) == 2:
                return parts[0], parts[1]
    return None, None


def main() -> None:  # noqa: C901
    """Главная функция Streamlit приложения"""
    st.set_page_config(page_title="AI Трейдер (Finam)", page_icon="🤖", layout="wide")

    # Заголовок
    st.title("🤖 AI Ассистент Трейдера")
    st.caption("Интеллектуальный помощник для работы с Finam TradeAPI")

    # Sidebar с настройками
    with st.sidebar:
        st.header("⚙️ Настройки")
        settings = get_settings()
        st.info(f"**Модель:** {settings.openrouter_model}")

        # Finam API настройки
        with st.expander("🔑 Finam API", expanded=False):
            api_token = st.text_input(
                "Access Token",
                type="password",
                help="Токен доступа к Finam TradeAPI (или используйте FINAM_ACCESS_TOKEN)",
            )
            api_base_url = st.text_input("API Base URL", value="https://api.finam.ru", help="Базовый URL API")

        account_id = st.text_input("ID счета", value="", help="Оставьте пустым если не требуется")

        if st.button("🔄 Очистить историю"):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown("### 💡 Примеры вопросов:")
        st.markdown("""
        - Какая цена Сбербанка?
        - Покажи мой портфель
        - Что в стакане по Газпрому?
        - Покажи свечи YNDX за последние дни
        - Какие у меня активные ордера?
        - Детали моей сессии
        """)

    # Инициализация состояния
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Инициализация Finam API клиента
    finam_client = FinamAPIClient(access_token=api_token or None, base_url=api_base_url if api_base_url else None)

    # Проверка токена
    if not finam_client.access_token:
        st.sidebar.warning(
            "⚠️ Finam API токен не установлен. Установите в переменной окружения FINAM_ACCESS_TOKEN или введите выше."
        )
    else:
        st.sidebar.success("✅ Finam API токен установлен")

    # Отображение истории сообщений
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Показываем API запросы
            if "api_request" in message:
                with st.expander("🔍 API запрос"):
                    st.code(f"{message['api_request']['method']} {message['api_request']['path']}", language="http")
                    st.json(message["api_request"]["response"])

    # Поле ввода
    if prompt := st.chat_input("Напишите ваш вопрос..."):
        # Добавляем сообщение пользователя
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Формируем историю для LLM
        conversation_history = [{"role": "system", "content": create_system_prompt()}]
        for msg in st.session_state.messages:
            conversation_history.append({"role": msg["role"], "content": msg["content"]})

        # Получаем ответ от ассистента
        with st.chat_message("assistant"), st.spinner("Думаю..."):
            try:
                response = call_llm(conversation_history, temperature=0.3)
                assistant_message = response["choices"][0]["message"]["content"]

                # Проверяем API запрос
                method, path = extract_api_request(assistant_message)

                api_data = None
                execute_api = True
                if method and path:
                    # Подставляем account_id если есть
                    if account_id and "{account_id}" in path:  # noqa: RUF027
                        path = path.replace("{account_id}", account_id)

                    # Безопасность: Подтверждение для POST/DELETE
                    if method in ["POST", "DELETE"]:
                        confirm = st.text_input(f"[БЕЗОПАСНОСТЬ] Подтвердите {method} {path} (да/нет):")
                        if confirm.lower() != "да":
                            st.warning("Операция отменена")
                            execute_api = False

                    if execute_api:
                        # Показываем что делаем запрос
                        st.info(f"🔍 Выполняю запрос: `{method} {path}`")

                        # Выполняем API запрос
                        api_response = finam_client.execute_request(method, path)

                        # Проверяем на ошибки
                        if "error" in api_response:
                            st.error(f"⚠️ Ошибка API: {api_response.get('error')}")
                            if "details" in api_response:
                                st.error(f"Детали: {api_response['details']}")

                        # Показываем результат
                        with st.expander("📡 Ответ API", expanded=False):
                            st.json(api_response)

                        # Визуализация: Если bars, покажи candlestick
                        if "bars" in path and isinstance(api_response, list):
                            fig = go.Figure(data=[go.Candlestick(
                                x=[bar['time'] for bar in api_response],
                                open=[bar['open'] for bar in api_response],
                                high=[bar['high'] for bar in api_response],
                                low=[bar['low'] for bar in api_response],
                                close=[bar['close'] for bar in api_response]
                            )])
                            st.plotly_chart(fig, use_container_width=True)

                        # Кейс 1: Анализ портфеля (если запрос о портфеле/счете)
                        if "accounts" in path and "positions" in str(api_response).lower():
                            # Пример sunburst для структуры портфеля (сектора)
                            # Симулируем данные: сектора и веса (в реальности из api_response['positions'])
                            sectors = ["Технологии", "Финансы", "Энергия", "Промышленность"]
                            weights = [0.4, 0.3, 0.2, 0.1]  # Из позиций
                            fig_sunburst = go.Figure(go.Sunburst(
                                labels=sectors,
                                parents=[""] * len(sectors),
                                values=weights,
                                branchvalues="total"
                            ))
                            st.plotly_chart(fig_sunburst, use_container_width=True)
                            st.caption("Структура портфеля по секторам")

                        # Кейс 2: Рыночный сканер (если запрос об активах/фильтре)
                        if "assets" in path:
                            # Таблица с sparklines (мини-графики динамики)
                            # Симулируем данные: тикеры, рост, спарклайн (из GetBars)
                            tickers = ["SBER", "GAZP", "YDEX"]
                            growth = [5.2, -1.3, 3.8]  # % изменения
                            # Sparklines: простые линии (в реальности из баров)
                            fig_spark = go.Figure()
                            for i, g in enumerate(growth):
                                fig_spark.add_trace(go.Scatter(y=[0, g], mode='lines', name=tickers[i]))
                            fig_spark.update_layout(showlegend=False, height=50)
                            st.plotly_chart(fig_spark, use_container_width=True)
                            st.dataframe({"Тикер": tickers, "Рост %": growth})

                        # Кейс 3: Песочница стратегий (бэктест на барах)
                        if "bars" in path and len(api_response) > 1:
                            # График сделок + кривая доходности
                            times = [bar['time'] for bar in api_response]
                            closes = [bar['close'] for bar in api_response]
                            fig_backtest = go.Figure()
                            fig_backtest.add_trace(go.Scatter(x=times, y=closes, mode='lines', name='Цена'))
                            # Симулируем точки входа/выхода (в реальности по стратегии)
                            entries = [times[0], times[-1]]  # Пример
                            fig_backtest.add_trace(go.Scatter(x=entries, y=[closes[0], closes[-1]], mode='markers', name='Сделки'))
                            # Кривая доходности (кумулятивная)
                            returns = [ (closes[i] - closes[0]) / closes[0] for i in range(len(closes)) ]
                            fig_backtest.add_trace(go.Scatter(x=times, y=returns, yaxis='y2', name='Доходность'))
                            fig_backtest.update_layout(yaxis2=dict(overlaying='y', side='right'))
                            st.plotly_chart(fig_backtest, use_container_width=True)

                        api_data = {"method": method, "path": path, "response": api_response}

                        # Добавляем результат в контекст
                        conversation_history.append({"role": "assistant", "content": assistant_message})
                        conversation_history.append({
                            "role": "user",
                            "content": f"Результат API: {json.dumps(api_response, ensure_ascii=False)}\n\nПроанализируй.",
                        })

                        # Получаем финальный ответ
                        response = call_llm(conversation_history, temperature=0.3)
                        assistant_message = response["choices"][0]["message"]["content"]

                st.markdown(assistant_message)

                # Сохраняем сообщение ассистента
                message_data = {"role": "assistant", "content": assistant_message}
                if api_data:
                    message_data["api_request"] = api_data
                st.session_state.messages.append(message_data)

            except Exception as e:
                st.error(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Streamlit веб-интерфейс для AI ассистента трейдера

Использование:
    poetry run streamlit run src/app/chat_app.py
    streamlit run src/app/chat_app.py
"""

import json

import streamlit as st
import plotly.graph_objects as go  # Для визуализации

from src.app.adapters import FinamAPIClient
from src.app.core import call_llm, get_settings


def create_system_prompt() -> str:
    """Создать системный промпт для AI ассистента"""
    return """Ты - AI ассистент трейдера, работающий с Finam TradeAPI.

Когда пользователь задает вопрос о рынке, портфеле или хочет совершить действие:
1. Определи нужный API endpoint
2. Укажи запрос в формате: API_REQUEST: METHOD /path
3. После получения данных - проанализируй их и дай понятный ответ

Доступные endpoints:
- GET /v1/instruments/{symbol}/quotes/latest - котировка
- GET /v1/instruments/{symbol}/orderbook - стакан
- GET /v1/instruments/{symbol}/bars - свечи
- GET /v1/accounts/{account_id} - счет и позиции
- GET /v1/accounts/{account_id}/orders - ордера
- POST /v1/accounts/{account_id}/orders - создать ордер
- DELETE /v1/accounts/{account_id}/orders/{order_id} - отменить ордер

Отвечай на русском, кратко и по делу."""


def extract_api_request(text: str) -> tuple[str | None, str | None]:
    """Извлечь API запрос из ответа LLM"""
    if "API_REQUEST:" not in text:
        return None, None

    lines = text.split("\n")
    for line in lines:
        if line.strip().startswith("API_REQUEST:"):
            request = line.replace("API_REQUEST:", "").strip()
            parts = request.split(maxsplit=1)
            if len(parts) == 2:
                return parts[0], parts[1]
    return None, None


def main() -> None:  # noqa: C901
    """Главная функция Streamlit приложения"""
    st.set_page_config(page_title="AI Трейдер (Finam)", page_icon="🤖", layout="wide")

    # Заголовок
    st.title("🤖 AI Ассистент Трейдера")
    st.caption("Интеллектуальный помощник для работы с Finam TradeAPI")

    # Sidebar с настройками
    with st.sidebar:
        st.header("⚙️ Настройки")
        settings = get_settings()
        st.info(f"**Модель:** {settings.openrouter_model}")

        # Finam API настройки
        with st.expander("🔑 Finam API", expanded=False):
            api_token = st.text_input(
                "Access Token",
                type="password",
                help="Токен доступа к Finam TradeAPI (или используйте FINAM_ACCESS_TOKEN)",
            )
            api_base_url = st.text_input("API Base URL", value="https://api.finam.ru", help="Базовый URL API")

        account_id = st.text_input("ID счета", value="", help="Оставьте пустым если не требуется")

        if st.button("🔄 Очистить историю"):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown("### 💡 Примеры вопросов:")
        st.markdown("""
        - Какая цена Сбербанка?
        - Покажи мой портфель
        - Что в стакане по Газпрому?
        - Покажи свечи YNDX за последние дни
        - Какие у меня активные ордера?
        - Детали моей сессии
        """)

    # Инициализация состояния
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Инициализация Finam API клиента
    finam_client = FinamAPIClient(access_token=api_token or None, base_url=api_base_url if api_base_url else None)

    # Проверка токена
    if not finam_client.access_token:
        st.sidebar.warning(
            "⚠️ Finam API токен не установлен. Установите в переменной окружения FINAM_ACCESS_TOKEN или введите выше."
        )
    else:
        st.sidebar.success("✅ Finam API токен установлен")

    # Отображение истории сообщений
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Показываем API запросы
            if "api_request" in message:
                with st.expander("🔍 API запрос"):
                    st.code(f"{message['api_request']['method']} {message['api_request']['path']}", language="http")
                    st.json(message["api_request"]["response"])

    # Поле ввода
    if prompt := st.chat_input("Напишите ваш вопрос..."):
        # Добавляем сообщение пользователя
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Формируем историю для LLM
        conversation_history = [{"role": "system", "content": create_system_prompt()}]
        for msg in st.session_state.messages:
            conversation_history.append({"role": msg["role"], "content": msg["content"]})

        # Получаем ответ от ассистента
        with st.chat_message("assistant"), st.spinner("Думаю..."):
            try:
                response = call_llm(conversation_history, temperature=0.3)
                assistant_message = response["choices"][0]["message"]["content"]

                # Проверяем API запрос
                method, path = extract_api_request(assistant_message)

                api_data = None
                execute_api = True
                if method and path:
                    # Подставляем account_id если есть
                    if account_id and "{account_id}" in path:  # noqa: RUF027
                        path = path.replace("{account_id}", account_id)

                    # Безопасность: Подтверждение для POST/DELETE
                    if method in ["POST", "DELETE"]:
                        confirm = st.text_input(f"[БЕЗОПАСНОСТЬ] Подтвердите {method} {path} (да/нет):")
                        if confirm.lower() != "да":
                            st.warning("Операция отменена")
                            execute_api = False

                    if execute_api:
                        # Показываем что делаем запрос
                        st.info(f"🔍 Выполняю запрос: `{method} {path}`")

                        # Выполняем API запрос
                        api_response = finam_client.execute_request(method, path)

                        # Проверяем на ошибки
                        if "error" in api_response:
                            st.error(f"⚠️ Ошибка API: {api_response.get('error')}")
                            if "details" in api_response:
                                st.error(f"Детали: {api_response['details']}")

                        # Показываем результат
                        with st.expander("📡 Ответ API", expanded=False):
                            st.json(api_response)

                        # Визуализация: Если bars, покажи candlestick
                        if "bars" in path and isinstance(api_response, list):
                            fig = go.Figure(data=[go.Candlestick(
                                x=[bar['time'] for bar in api_response],
                                open=[bar['open'] for bar in api_response],
                                high=[bar['high'] for bar in api_response],
                                low=[bar['low'] for bar in api_response],
                                close=[bar['close'] for bar in api_response]
                            )])
                            st.plotly_chart(fig, use_container_width=True)

                        # Кейс 1: Анализ портфеля (если запрос о портфеле/счете)
                        if "accounts" in path and "positions" in str(api_response).lower():
                            # Пример sunburst для структуры портфеля (сектора)
                            # Симулируем данные: сектора и веса (в реальности из api_response['positions'])
                            sectors = ["Технологии", "Финансы", "Энергия", "Промышленность"]
                            weights = [0.4, 0.3, 0.2, 0.1]  # Из позиций
                            fig_sunburst = go.Figure(go.Sunburst(
                                labels=sectors,
                                parents=[""] * len(sectors),
                                values=weights,
                                branchvalues="total"
                            ))
                            st.plotly_chart(fig_sunburst, use_container_width=True)
                            st.caption("Структура портфеля по секторам")

                        # Кейс 2: Рыночный сканер (если запрос об активах/фильтре)
                        if "assets" in path:
                            # Таблица с sparklines (мини-графики динамики)
                            # Симулируем данные: тикеры, рост, спарклайн (из GetBars)
                            tickers = ["SBER", "GAZP", "YDEX"]
                            growth = [5.2, -1.3, 3.8]  # % изменения
                            # Sparklines: простые линии (в реальности из баров)
                            fig_spark = go.Figure()
                            for i, g in enumerate(growth):
                                fig_spark.add_trace(go.Scatter(y=[0, g], mode='lines', name=tickers[i]))
                            fig_spark.update_layout(showlegend=False, height=50)
                            st.plotly_chart(fig_spark, use_container_width=True)
                            st.dataframe({"Тикер": tickers, "Рост %": growth})

                        # Кейс 3: Песочница стратегий (бэктест на барах)
                        if "bars" in path and len(api_response) > 1:
                            # График сделок + кривая доходности
                            times = [bar['time'] for bar in api_response]
                            closes = [bar['close'] for bar in api_response]
                            fig_backtest = go.Figure()
                            fig_backtest.add_trace(go.Scatter(x=times, y=closes, mode='lines', name='Цена'))
                            # Симулируем точки входа/выхода (в реальности по стратегии)
                            entries = [times[0], times[-1]]  # Пример
                            fig_backtest.add_trace(go.Scatter(x=entries, y=[closes[0], closes[-1]], mode='markers', name='Сделки'))
                            # Кривая доходности (кумулятивная)
                            returns = [ (closes[i] - closes[0]) / closes[0] for i in range(len(closes)) ]
                            fig_backtest.add_trace(go.Scatter(x=times, y=returns, yaxis='y2', name='Доходность'))
                            fig_backtest.update_layout(yaxis2=dict(overlaying='y', side='right'))
                            st.plotly_chart(fig_backtest, use_container_width=True)

                        api_data = {"method": method, "path": path, "response": api_response}

                        # Добавляем результат в контекст
                        conversation_history.append({"role": "assistant", "content": assistant_message})
                        conversation_history.append({
                            "role": "user",
                            "content": f"Результат API: {json.dumps(api_response, ensure_ascii=False)}\n\nПроанализируй.",
                        })

                        # Получаем финальный ответ
                        response = call_llm(conversation_history, temperature=0.3)
                        assistant_message = response["choices"][0]["message"]["content"]

                st.markdown(assistant_message)

                # Сохраняем сообщение ассистента
                message_data = {"role": "assistant", "content": assistant_message}
                if api_data:
                    message_data["api_request"] = api_data
                st.session_state.messages.append(message_data)

            except Exception as e:
                st.error(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
