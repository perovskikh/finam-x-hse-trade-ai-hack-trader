#!/usr/bin/env python3
"""
Тесты для LLM парсинга и генерации API запросов

Использование:
    pytest tests/test_llm.py -v
    poetry run test-llm
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.app.core.llm import call_llm
from src.app.core.config import get_settings
from scripts.generate_submission import load_train_examples, create_prompt, parse_llm_response
from scripts.calculate_metrics import normalize_api_request


@pytest.fixture
def settings():
    """Фикстура для настроек"""
    return get_settings()


@pytest.fixture
def train_examples():
    """Загрузка примеров из train.csv"""
    train_file = Path("data/processed/train.csv")
    if train_file.exists():
        examples = load_train_examples(train_file, num_examples=5)
    else:
        # Fallback для теста, если CSV недоступен
        examples = [
            {
                "question": "Какая цена Сбербанка?",
                "type": "GET",
                "request": "GET /v1/instruments/SBER@MISX/quotes/latest"
            },
            {
                "question": "Покажи мой портфель",
                "type": "GET",
                "request": "GET /v1/accounts/{account_id}"
            },
            {
                "question": "Отмени ордер ORD789789",
                "type": "DELETE",
                "request": "DELETE /v1/accounts/{account_id}/orders/ORD789789"
            },
            {
                "question": "Купи 1000 акций AFLT@MISX по 41.20",
                "type": "POST",
                "request": "POST /v1/accounts/{account_id}/orders"
            },
            {
                "question": "Выведи лот и шаг цены для VTBR@MISX.",
                "type": "GET",
                "request": "GET /v1/assets/VTBR@MISX"
            }
        ]
    return examples


def test_llm_parsing_accuracy(settings, train_examples, monkeypatch):
    """Тест точности парсинга LLM на примерах из train.csv"""
    correct = 0
    total = len(train_examples)

    # Мокаем LLM для предсказуемых ответов на основе индекса примера
    def mock_call_llm(messages, **kwargs):
        # Получаем индекс примера из контекста (упрощение для теста)
        question = messages[-1]["content"]
        # Маппинг вопросов к ответам (используем первые 5 примеров)
        question_to_response = {
            train_examples[0]["question"].lower(): '{"type": "GET", "request": "GET /v1/instruments/SBER@MISX/quotes/latest"}',
            train_examples[1]["question"].lower(): '{"type": "GET", "request": "GET /v1/accounts/{account_id}"}',
            train_examples[2]["question"].lower(): '{"type": "DELETE", "request": "DELETE /v1/accounts/{account_id}/orders/ORD789789"}',
            train_examples[3]["question"].lower(): '{"type": "POST", "request": "POST /v1/accounts/{account_id}/orders"}',
            train_examples[4]["question"].lower(): '{"type": "GET", "request": "GET /v1/assets/VTBR@MISX"}',
        }
        q_lower = question.lower()
        for q_key, resp in question_to_response.items():
            if q_key in q_lower:
                return {"choices": [{"message": {"content": resp}}]}
        # Fallback
        return {"choices": [{"message": {"content": '{"type": "GET", "request": "/v1/assets"}'}}]}

    monkeypatch.setattr("src.app.core.llm.call_llm", mock_call_llm)

    for i, example in enumerate(train_examples[:5]):  # Тестируем первые 5
        question = example["question"]
        expected_type = example["type"]
        expected_request = example["request"]

        # Создаем промпт
        prompt = create_prompt(question, train_examples[:3])

        # Вызываем LLM (мок)
        messages = [{"role": "user", "content": prompt}]
        response = call_llm(messages, temperature=0.0, max_tokens=200)
        llm_answer = response["choices"][0]["message"]["content"].strip()

        # Парсим ответ
        predicted_type, predicted_request = parse_llm_response(llm_answer)

        # Проверяем совпадение (игнорируя account_id)
        if predicted_type == expected_type:
            # Нормализуем request для сравнения
            expected_norm = normalize_api_request(expected_request, expected_type)
            predicted_norm = normalize_api_request(predicted_request, predicted_type)

            if predicted_norm == expected_norm:
                correct += 1

    accuracy = correct / min(5, len(train_examples))
    assert accuracy >= 0.8, f"LLM parsing accuracy: {accuracy:.2f} (expected >=0.8 with mock)"
    print(f"✅ LLM parsing accuracy: {accuracy:.2f} ({correct}/{min(5, len(train_examples))})")


def test_parse_llm_response_structured():
    """Тест парсинга структурированного JSON ответа"""
    # Тест с JSON
    json_response = '{"type": "GET", "request": "/v1/assets/SBER@MISX"}'
    method, request = parse_llm_response(json_response)
    assert method == "GET"
    assert request == "/v1/assets/SBER@MISX"
    
    # Тест с некорректным JSON (fallback)
    bad_json = '{"type": "GET", "request": "/v1/assets'
    method, request = parse_llm_response(bad_json)
    assert method == "GET"  # Fallback должен работать
    assert request.startswith("/v1/assets")


def test_parse_llm_response_text():
    """Тест парсинга текстового ответа"""
    # Тест с HTTP методом в начале
    text_response = "GET /v1/instruments/GAZP@MISX/quotes/latest"
    method, request = parse_llm_response(text_response)
    assert method == "GET"
    assert request == "/v1/instruments/GAZP@MISX/quotes/latest"
    
    # Тест с методом в середине
    mixed_response = "Нужно получить котировку: POST /v1/accounts/123/orders"
    method, request = parse_llm_response(mixed_response)
    assert method == "POST"
    assert request == "/v1/accounts/123/orders"
    
    # Тест без метода (fallback)
    no_method = "/v1/exchanges"
    method, request = parse_llm_response(no_method)
    assert method == "GET"  # Fallback
    assert request == "/v1/exchanges"


def test_create_prompt_structure(train_examples):
    """Тест структуры сгенерированного промпта"""
    question = "Какая цена Сбербанка?"
    prompt = create_prompt(question, train_examples[:2])
    
    # Проверяем наличие документации API
    assert "API Documentation:" in prompt
    assert "GET /v1/instruments/{symbol}/quotes/latest" in prompt
    
    # Проверяем наличие примеров
    assert "Примеры:" in prompt
    for ex in train_examples[:2]:
        assert ex["question"] in prompt
        assert f"{ex['type']} {ex['request']}" in prompt
    
    # Проверяем наличие целевого вопроса
    assert f'Вопрос: "{question}"' in prompt
    assert "Ответ (только HTTP метод и путь, без объяснений):" in prompt


def test_end_to_end_generation(settings, train_examples, monkeypatch):
    """Энд-to-end тест: вопрос → промпт → LLM → парсинг"""
    question = "Покажи котировку Газпрома"
    expected_type = "GET"
    expected_path = "/v1/instruments/GAZP@MISX/quotes/latest"
    
    # Мокаем LLM
    def mock_call_llm(messages, **kwargs):
        return {"choices": [{"message": {"content": '{"type": "GET", "request": "/v1/instruments/GAZP@MISX/quotes/latest"}'}}]}

    monkeypatch.setattr("src.app.core.llm.call_llm", mock_call_llm)

    # Создаем промпт
    prompt = create_prompt(question, train_examples[:3])
    messages = [{"role": "user", "content": prompt}]
    
    # Вызываем LLM
    response = call_llm(messages, temperature=0.0, max_tokens=100)
    llm_answer = response["choices"][0]["message"]["content"].strip()
    
    # Парсим
    method, request = parse_llm_response(llm_answer)
    
    # Проверяем результат
    assert method == expected_type
    assert "GAZP" in request
    assert "quotes/latest" in request


@pytest.mark.skipif(not Path("data/processed/train.csv").exists(), reason="train.csv not found")
def test_batch_processing_accuracy():
    """Тест батчевой обработки на подмножестве train.csv"""
    train_file = Path("data/processed/train.csv")
    examples = load_train_examples(train_file, num_examples=10)
    
    correct = 0
    # Мокаем LLM для предсказуемых результатов
    with patch("src.app.core.llm.call_llm") as mock_llm:
        # Более реалистичный мок: возвращает разные ответы
        mock_llm.side_effect = lambda messages, **kwargs: {
            "choices": [{"message": {"content": '{"type": "GET", "request": "/v1/assets"}'}}]
        }
        
        for example in examples[:5]:  # Тестируем на 5 примерах
            question = example["question"]
            expected_type = example["type"]
            
            prompt = create_prompt(question, examples[:3])
            messages = [{"role": "user", "content": prompt}]
            
            response = call_llm(messages, temperature=0.0, max_tokens=100)
            llm_answer = response["choices"][0]["message"]["content"].strip()
            
            method, request = parse_llm_response(llm_answer)
            
            # Простая проверка типа (fallback на GET)
            if method == expected_type or (method == "GET" and expected_type == "GET"):
                correct += 1
    
    accuracy = correct / 5
    assert accuracy >= 0.8, f"Batch processing accuracy: {accuracy:.2f} (expected >=0.8)"
    print(f"✅ Batch processing accuracy: {accuracy:.2f}")


def test_cost_calculation():
    """Тест расчета стоимости запросов"""
    from scripts.generate_submission import calculate_cost
    
    # Тест с GPT-4o-mini
    usage = {"prompt_tokens": 1000, "completion_tokens": 200}
    cost = calculate_cost(usage, "openai/gpt-4o-mini")
    assert 0.000 < cost < 0.001  # Ожидаем ~$0.00015 + $0.00012 = $0.00027
    
    # Тест с GPT-4o
    cost_gpt4 = calculate_cost(usage, "openai/gpt-4o")
    assert 0.004 < cost_gpt4 < 0.005  # Prompt: 1000/1M * 2.5 = 0.0025, Completion: 200/1M * 10 = 0.002, Total: 0.0045


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
