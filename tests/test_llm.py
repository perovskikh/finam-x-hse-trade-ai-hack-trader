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

from src.app.core.llm import call_llm
from src.app.core.config import get_settings
from scripts.generate_submission import load_train_examples, create_prompt, parse_llm_response


@pytest.fixture
def settings():
    """Фикстура для настроек"""
    return get_settings()


@pytest.fixture
def train_examples():
    """Загрузка примеров из train.csv"""
    train_file = Path("data/processed/train.csv")
    return load_train_examples(train_file, num_examples=5)


def test_llm_parsing_accuracy(settings, train_examples):
    """Тест точности парсинга LLM на примерах из train.csv"""
    correct = 0
    total = len(train_examples)

    for example in train_examples:
        question = example["question"]
        expected_type = example["type"]
        expected_request = example["request"]

        # Создаем промпт
        prompt = create_prompt(question, train_examples[:10])  # Используем 10 примеров

        # Вызываем LLM
        messages = [{"role": "user", "content": prompt}]
        response = call_llm(messages, temperature=0.0, max_tokens=200)
        llm_answer = response["choices"][0]["message"]["content"].strip()

        # Парсим ответ
        predicted_type, predicted_request = parse_llm_response(llm_answer)

        # Проверяем совпадение (игнорируя account_id)
        if predicted_type == expected_type:
            # Нормализуем request для сравнения
            if "{account_id}" in expected_request:
                expected_norm = expected_request.replace("{account_id}", "<some_id>")
            else:
                expected_norm = expected_request

            if "{account_id}" in predicted_request:
                predicted_norm = predicted_request.replace("{account_id}", "<some_id>")
            else:
                predicted_norm = predicted_request

            if predicted_norm == expected_norm:
                correct += 1

    accuracy = correct / total
    assert accuracy >= 0.2, f"LLM parsing accuracy: {accuracy:.2f} (expected >= 0.2)"
    print(f"✅ LLM parsing accuracy: {accuracy:.2f} ({correct}/{total})")


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


def test_end_to_end_generation(settings, train_examples):
    """Энд-to-end тест: вопрос → промпт → LLM → парсинг"""
    question = "Покажи котировку Газпрома"
    expected_type = "GET"
    expected_path = "/v1/instruments/GAZP@MISX/quotes/latest"
    
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
    for example in examples[:5]:  # Тестируем на 5 примерах
        question = example["question"]
        expected_type = example["type"]
        expected_request = example["request"]
        
        prompt = create_prompt(question, examples[:3])
        messages = [{"role": "user", "content": prompt}]
        
        response = call_llm(messages, temperature=0.0, max_tokens=100)
        llm_answer = response["choices"][0]["message"]["content"].strip()
        
        method, request = parse_llm_response(llm_answer)
        
        # Простая проверка типа
        if method == expected_type:
            correct += 1
    
    accuracy = correct / 5
    assert accuracy >= 0.6, f"Batch processing accuracy: {accuracy:.2f}"
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
