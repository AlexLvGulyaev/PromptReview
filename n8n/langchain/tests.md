# Тестовые примеры для Prompt Review Agent - LangChain

## Позитивный тест: Валидный промпт

**Вход:**
```
Ты — опытный преподаватель Python.

Объясни начинающему разработчику, что такое словарь (dict), используя простой пример из реальной жизни.

Ответ должен содержать:
- краткое объяснение;
- пример кода;
- типичные ошибки новичков.
```

**Ожидаемый результат:**
- `is_prompt: true`
- `purpose` заполнен
- `strengths` — список сильных сторон
- `weaknesses` — список недостатков
- `recommendations` — список рекомендаций
- `scores` — оценки по критериям (числа)
- `quality_level` — один из уровней
- `revised_prompt` — улучшенная редакция
- `metrics` — рассчитанные метрики

**Проверка:**
```json
{
  "request_id": "req_...",
  "is_prompt": true,
  "purpose": "Обучение начинающих разработчиков работе со словарями Python",
  "strengths": [
    "Чёткая ролевая инструкция",
    "Конкретная задача",
    "Указан формат результата"
  ],
  "weaknesses": [
    "Не указан уровень детализации",
    "Отсутствуют ограничения по объёму"
  ],
  "recommendations": [
    "Указать ожидаемый объём ответа",
    "Добавить примеры входных данных"
  ],
  "scores": {
    "clarity": 8,
    "completeness": 7,
    "ambiguity_absence": 8,
    "target_audience_fit": 9,
    "output_format": 8,
    "constraints_quality": 6,
    "missing_assumptions": 7,
    "structure_reusability": 7,
    "overall": 7.5
  },
  "quality_level": "good",
  "revised_prompt": "...",
  "reason": null,
  "conversion_options": [],
  "metrics": {
    "characters": 150,
    "words": 25,
    "lines": 7,
    "non_empty_lines": 7,
    "markdown_headings": 0,
    "bullet_items": 3,
    "numbered_items": 0,
    "markdown_table_lines": 0,
    "xml_tags": 0,
    "code_blocks": 0,
    "max_line_length": 60,
    "avg_line_length": 40
  },
  "notes": []
}
```

---

## Негативный тест: Обычный текст

**Вход:**
```
Привет! Как дела? Что нового?
```

**Ожидаемый результат:**
- `is_prompt: false`
- `purpose: null`
- `scores` — все нули
- `quality_level: "not_applicable"`
- `revised_prompt: null`
- `reason` — объяснение, почему это не промпт
- `conversion_options` — варианты превращения в промпт

**Проверка:**
```json
{
  "request_id": "req_...",
  "is_prompt": false,
  "purpose": null,
  "strengths": [],
  "weaknesses": [],
  "recommendations": [],
  "scores": {
    "clarity": 0,
    "completeness": 0,
    "ambiguity_absence": 0,
    "target_audience_fit": 0,
    "output_format": 0,
    "constraints_quality": 0,
    "missing_assumptions": 0,
    "structure_reusability": 0,
    "overall": 0
  },
  "quality_level": "not_applicable",
  "revised_prompt": null,
  "reason": "Текст представляет собой обычное приветствие и не содержит инструкций для языковой модели",
  "conversion_options": [
    "Добавьте ролевую инструкцию (например: \"Ты — ...\")",
    "Укажите ожидаемый формат результата",
    "Опишите конкретную задачу"
  ],
  "metrics": {
    "characters": 30,
    "words": 5,
    "lines": 1,
    "non_empty_lines": 1,
    "markdown_headings": 0,
    "bullet_items": 0,
    "numbered_items": 0,
    "markdown_table_lines": 0,
    "xml_tags": 0,
    "code_blocks": 0,
    "max_line_length": 30,
    "avg_line_length": 30
  },
  "notes": ["Текст не является промптом для языковой модели"]
}
```

---

## Дополнительный тест: Пограничный случай

**Вход:**
```
Объясни, что такое API.
```

**Ожидаемый результат:**
- `is_prompt: true` (или false, зависит от решения классификатора)
- Если `true` — минимальное ревью
- Если `false` — предложение превратить в полноценный промпт

**Анализ:**
Текст содержит описание задачи ("Объясни"), но:
- Отсутствует ролевая инструкция
- Не указан формат результата
- Нет ограничений по аудитории
- Нет структуры

Классификатор может определить это как промпт (есть задача) или как неполный промпт.

---

## Тестирование в n8n

### Порядок тестирования:

1. **Импорт workflow:**
   - Открыть n8n
   - Import workflow → выбрать `Prompt Review Agent - LangChain.json`
   - Настроить OpenAI API credentials

2. **Позитивный тест:**
   - Открыть Chat Trigger
   - Ввести позитивный пример
   - Проверить, что результат содержит `is_prompt: true`

3. **Негативный тест:**
   - Открыть Chat Trigger
   - Ввести негативный пример
   - Проверить, что результат содержит `is_prompt: false`

4. **Проверка метрик:**
   - Проверить, что `metrics` заполнен корректно
   - Проверить соответствие количества слов/символов

5. **Проверка JSON-структуры:**
   - Проверить, что результат валидный JSON
   - Проверить отсутствие markdown-разметки
   - Проверить наличие всех обязательных полей

### Возможные проблемы:

1. **Ошибка подключения к OpenAI:**
   - Проверить credentials
   - Проверить API-ключ

2. **Ошибка парсинга JSON:**
   - Проверить, что модель возвращает чистый JSON
   - Проверить промпты в коде

3. **Некорректная классификация:**
   - Уточнить промпт классификатора
   - Добавить примеры в CLASSIFIER_PROMPT