# План Изменений для Структурирования example.docs/create

## Этап 1: Анализ и Удаление Лишних Файлов
- Проанализировать директорию.
- Удалить: draft plan.task.trader.llm.interface.md, example.aide/*, example.CONVENTIONS.md, vibe-code.md.
- Обоснование: Черновики и примеры не нужны; оставляем ключевые (guide, prompt, task, вопросы).
- Действие: git rm <файлы>; git commit -m "Удаление лишних файлов из example.docs/create по plan_changes.md".

## Этап 2: Написание Промптов и Создание Файлов Управления
- Создать CONTRIBUTING.md с промптом (см. выше).
- Создать GOVERNANCE.md с промптом.
- Действие: aider --message "<промпт>" --file CONTRIBUTING.md; git commit.

## Этап 3: Обновление .aider.conf.yml
- Обновить раздел read: удалить ссылки на удаленные файлы, добавить CONTRIBUTING.md, GOVERNANCE.md.
- Действие: diff-изменения; git commit.

## Этап 4: Обновление .aider.model.settings.yml
- Обновить system_prompt_prefix: интегрировать ссылки на новые файлы (CONTRIBUTING, GOVERNANCE) и docs/create/*.
- Действие: diff-изменения; git commit.

## Этап 5: Валидация
- Запустить Aider с новыми конфигами; проверить на test.csv (>85% accuracy).
- Действие: Тесты; git commit если нужно.
# План Изменений для Структурирования example.docs/create

## Этап 1: Анализ и Удаление Лишних Файлов
- Проанализировать директорию.
- Удалить: draft plan.task.trader.llm.interface.md, example.aide/*, example.CONVENTIONS.md, vibe-code.md.
- Обоснование: Черновики и примеры не нужны; оставляем ключевые (guide, prompt, task, вопросы).
- Действие: git rm <файлы>; git commit -m "Удаление лишних файлов из example.docs/create по plan_changes.md".

## Этап 2: Написание Промптов и Создание Файлов Управления
- Создать CONTRIBUTING.md с промптом (см. выше).
- Создать GOVERNANCE.md с промптом.
- Действие: aider --message "<промпт>" --file CONTRIBUTING.md; git commit.

## Этап 3: Обновление .aider.conf.yml
- Обновить раздел read: удалить ссылки на удаленные файлы, добавить CONTRIBUTING.md, GOVERNANCE.md.
- Действие: diff-изменения; git commit.

## Этап 4: Обновление .aider.model.settings.yml
- Обновить system_prompt_prefix: интегрировать ссылки на новые файлы (CONTRIBUTING, GOVERNANCE) и docs/create/*.
- Действие: diff-изменения; git commit.

## Этап 5: Валидация
- Запустить Aider с новыми конфигами; проверить на test.csv (>85% accuracy).
- Действие: Тесты; git commit если нужно.
# План Изменений для Структурирования example.docs/create

## Этап 1: Анализ и Удаление Лишних Файлов
- Проанализировать директорию.
- Удалить: draft plan.task.trader.llm.interface.md, example.aide/*, example.CONVENTIONS.md, vibe-code.md.
- Обоснование: Черновики и примеры не нужны; оставляем ключевые (guide, prompt, task, вопросы).
- Действие: git rm <файлы>; git commit -m "Удаление лишних файлов из example.docs/create по plan_changes.md".

## Этап 2: Написание Промптов и Создание Файлов Управления
- Создать CONTRIBUTING.md с промптом (см. выше).
- Создать GOVERNANCE.md с промптом.
- Действие: aider --message "<промпт>" --file CONTRIBUTING.md; git commit.

## Этап 3: Обновление .aider.conf.yml
- Обновить раздел read: удалить ссылки на удаленные файлы, добавить CONTRIBUTING.md, GOVERNANCE.md.
- Действие: diff-изменения; git commit.

## Этап 4: Обновление .aider.model.settings.yml
- Обновить system_prompt_prefix: интегрировать ссылки на новые файлы (CONTRIBUTING, GOVERNANCE) и docs/create/*.
- Действие: diff-изменения; git commit.

## Этап 5: Валидация
- Запустить Aider с новыми конфигами; проверить на test.csv (>85% accuracy).
- Действие: Тесты; git commit если нужно.
