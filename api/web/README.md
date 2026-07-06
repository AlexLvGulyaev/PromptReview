# Prompt Review Web UI

**Пользовательский веб-интерфейс для Prompt Review Service.**

---

## Описание

Web UI — это современный веб-интерфейс для анализа качества промптов через Prompt Review Service. Пользователи могут отправлять текст и получать подробный анализ с оценками, рекомендациями и улучшенной редакцией.

---

## Архитектура

```
Browser
    ↓
Web UI (HTML/CSS/JavaScript)
    ↓
POST /review
    ↓
FastAPI API
    ↓
Prompt Review Engine
    ↓
LangChain / LangFlow
```

**Ключевой принцип:** Web UI — это тонкий клиент. Вся бизнес-логика остаётся в Prompt Review Service.

---

## Возможности

### Для промптов

- 📊 **Итоговая оценка качества** (excellent, good, fair, poor)
- 🎯 **Назначение промпта**
- 📈 **Оценки по критериям** с визуальными шкалами:
  - Понятность
  - Полнота
  - Отсутствие неоднозначностей
  - Соответствие аудитории
  - Формат результата
  - Качество ограничений
  - Достаточность предположений
  - Структурированность
- ✅ **Сильные стороны**
- ⚠️ **Слабые стороны**
- 💡 **Рекомендации по улучшению** (с приоритетами: high/medium/low)
- 📝 **Улучшенная редакция промпта** (с кнопкой копирования)
- ⏱️ **Время обработки**

### Для обычного текста

- ❓ **Сообщение о том, что текст не распознан**
- 🔍 **Причина**
- 📊 **Метрики текста** (символы, слова, строки)
- 🔄 **Варианты преобразования в промпт**

### Интерфейс

- 🌙 **Тёмная тема** (оптимизирована для длительной работы)
- 📱 **Адаптивная вёрстка** (desktop, tablet, mobile)
- ⌨️ **Горячие клавиши** (Ctrl/Cmd+Enter для анализа)
- 📋 **Копирование в один клик**
- 🔄 **Автоматический статус API**

---

## Технологии

- **HTML5** — семантическая разметка
- **CSS3** — CSS Variables, Flexbox, Grid
- **Vanilla JavaScript** — без зависимостей
- **Fetch API** — взаимодействие с FastAPI
- **Google Fonts** — Outfit (display), Inter (body)

---

## Дизайн-система

Основана на дизайн-системе Lead Qualification (n8n-lead-qualification):

### Цвета

```css
/* Background */
--bg-primary: #0a0a0f
--bg-secondary: #111118
--bg-tertiary: #18181f

/* Text */
--text-primary: #f5f5f7
--text-secondary: #a1a1aa
--text-tertiary: #71717a

/* Accent */
--accent-primary: #14b8a6 (teal/cyan)

/* Quality Levels */
--excellent: #22c55e (green)
--good: #14b8a6 (teal)
--fair: #f59e0b (orange)
--poor: #ef4444 (red)
```

### Компоненты

- **Карточки** — с цветными акцентами для статусов
- **Прогресс-бары** — визуализация оценок (0–10)
- **Бейджи** — качество промпта
- **Теги** — приоритеты рекомендаций
- **Кнопки** — с hover/active состояниями

### Адаптивность

- Desktop: 3 колонки для оценок
- Tablet: 2 колонки
- Mobile: 1 колонка, упрощённый layout

---

## Запуск

### Требования

1. **FastAPI API** запущен на `http://localhost:8000`
2. Любой статический веб-сервер для раздачи файлов

### Локальный запуск (без сервера)

Откройте `index.html` в браузере. API URL будет `http://localhost:8000`.

### Запуск через Python

```bash
cd api/web
python -m http.server 3000
```

Откройте: http://localhost:3000

### Запуск через FastAPI (рекомендуется)

Добавьте Web UI как статические файлы в FastAPI:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/ui", StaticFiles(directory="web", html=True), name="ui")
```

Откройте: http://localhost:8000/ui

---

## Переменные окружения

Web UI не требует переменных окружения. URL API определяется автоматически:

- Если открыт как `file://`, используется `http://localhost:8000`
- Иначе используется origin с портом 8000

Для кастомизации измените `CONFIG.API_URL` в `app.js`:

```javascript
const CONFIG = {
    API_URL: 'http://your-api-url:8000',
    // ...
};
```

---

## Структура файлов

```
api/web/
├── index.html      # Главная страница
├── styles.css      # Стили (CSS Variables, компоненты)
├── app.js          # Логика (API calls, рендеринг)
└── README.md       # Документация
```

---

## API Contract

Web UI использует endpoint `POST /review`:

### Request

```json
{
    "prompt_text": "Текст для анализа...",
    "user_id": "web:1234567890:abc123def",
    "source": "web",
    "review_mode": "standard"
}
```

### Response (Prompt)

```json
{
    "request_id": "req_...",
    "user_id": "web:...",
    "is_prompt": true,
    "purpose": "Назначение промпта",
    "strengths": ["Сильная сторона 1", "Сильная сторона 2"],
    "weaknesses": ["Слабая сторона 1"],
    "recommendations": [
        {"priority": "high", "text": "Рекомендация 1"},
        {"priority": "medium", "text": "Рекомендация 2"}
    ],
    "scores": {
        "clarity": 8,
        "completeness": 7,
        "overall": 7.5
    },
    "quality_level": "good",
    "revised_prompt": "Улучшенная редакция...",
    "metrics": {
        "characters": 450,
        "words": 67,
        "lines": 12
    },
    "processing_time_ms": 2345
}
```

### Response (Not Prompt)

```json
{
    "is_prompt": false,
    "reason": "Текст не содержит инструкций для AI-модели",
    "conversion_options": [
        "Добавьте роль: 'Ты — ...'",
        "Укажите цель: 'Сделай так-то...'"
    ],
    "metrics": {...}
}
```

---

## Обработка ошибок

Web UI обрабатывает все типы ошибок:

| Ошибка | Сообщение |
|--------|-----------|
| API недоступен | "API недоступен" (status indicator) |
| Timeout | "Превышено время ожидания" |
| Network error | "Ошибка сети. Проверьте подключение" |
| 400 Bad Request | "Минимальная длина — 10 символов" |
| 500 Server Error | "Ошибка сервера. Попробуйте позже" |
| Invalid JSON | "Некорректный ответ сервера" |

---

## E2E-тестирование

### Сценарии

1. **Загрузка страницы**
   - Открыть `index.html`
   - Проверить статус API (online)
   - Проверить отображение интерфейса

2. **Анализ промпта**
   - Ввести промпт
   - Нажать "Проанализировать"
   - Проверить отображение оценок, рекомендаций, improved prompt

3. **Анализ обычного текста**
   - Ввести "Сегодня хорошая погода"
   - Нажать "Проанализировать"
   - Проверить отображение причины, метрик, conversion options

4. **Обработка ошибки**
   - Остановить FastAPI
   - Попробовать анализ
   - Проверить сообщение об ошибке

5. **Мобильное отображение**
   - Изменить размер окна
   - Проверить адаптивность карточек и grid

### Скриншоты

Требуемые скриншоты:
- Главная страница (empty state)
- Анализ промпта (full result)
- Анализ не-промпта
- Отображение ошибки
- Мобильное отображение (responsive)

---

## Совместимость

### Браузеры

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Android Chrome)

### API Backend

- LangChain backend (локальный, Ollama)
- LangFlow backend (remote, OpenAI)

---

## Производительность

- **Размер файлов:**
  - `index.html`: ~15 KB
  - `styles.css`: ~15 KB
  - `app.js`: ~12 KB
  - **Итого:** ~42 KB (без сжатия)

- **Загрузка шрифтов:** Google Fonts (Outfit, Inter) — ~30 KB

- **Время ответа API:** 2–4 секунды (зависит от backend)

---

## Безопасность

- **XSS Protection:** Все пользовательские данные экранируются через `escapeHtml()`
- **CORS:** Настроен в FastAPI (`allow_origins`)
- **Rate Limiting:** Реализуется на уровне FastAPI

---

## Дальнейшее развитие

### Возможные улучшения

1. **History** — сохранение истории запросов в localStorage
2. **Export** — экспорт результатов в JSON/Markdown
3. **Themes** — переключение между тёмной/светлой темой
4. **Internationalization** — мультиязычность (en/ru)
5. **Shortcuts** — больше горячих клавиш
6. **PWA** — Progressive Web App (offline support)

---

## Лицензия

Проект развивается в рамках AI Automation Portfolio Lab.