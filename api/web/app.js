/**
 * Prompt Review Web UI
 * Клиентская часть для взаимодействия с FastAPI API.
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
    // Determine API URL based on current host
    // - demo subdomain -> api subdomain
    // - api subdomain or localhost -> same origin
    API_URL: window.location.hostname === 'prompt-review-demo.alex-n8n.site'
        ? 'https://prompt-review-api.alex-n8n.site'
        : (window.location.origin === 'file://'
            ? 'http://localhost:8000'
            : window.location.origin),
    TIMEOUT: 60000, // 60 seconds
    MIN_TEXT_LENGTH: 10,
    MAX_TEXT_LENGTH: 10000
};

// ============================================================================
// DOM ELEMENTS
// ============================================================================

const elements = {
    // Input
    promptInput: document.getElementById('prompt-input'),
    charCount: document.getElementById('char-count'),
    analyzeBtn: document.getElementById('analyze-btn'),

    // Status
    statusIndicator: document.getElementById('status-indicator'),
    statusText: document.getElementById('status-text'),

    // Sections
    loadingSection: document.getElementById('loading-section'),
    errorSection: document.getElementById('error-section'),
    resultsSection: document.getElementById('results-section'),

    // Error
    errorMessage: document.getElementById('error-message'),
    errorRetryBtn: document.getElementById('error-retry-btn'),

    // Not Prompt Result
    notPromptResult: document.getElementById('not-prompt-result'),
    notPromptReason: document.getElementById('not-prompt-reason'),
    notPromptChars: document.getElementById('not-prompt-chars'),
    notPromptWords: document.getElementById('not-prompt-words'),
    notPromptLines: document.getElementById('not-prompt-lines'),
    conversionList: document.getElementById('conversion-list'),
    notPromptTime: document.getElementById('not-prompt-time'),

    // Prompt Result
    promptResult: document.getElementById('prompt-result'),
    qualityCard: document.getElementById('quality-card'),
    qualityIcon: document.getElementById('quality-icon'),
    qualitySubtitle: document.getElementById('quality-subtitle'),
    qualityBadge: document.getElementById('quality-badge'),
    qualityValue: document.getElementById('quality-value'),
    purposeSection: document.getElementById('purpose-section'),
    purposeText: document.getElementById('purpose-text'),
    scoresGrid: document.getElementById('scores-grid'),
    overallScore: document.getElementById('overall-score'),
    promptTime: document.getElementById('prompt-time'),

    // Analysis
    strengthsList: document.getElementById('strengths-list'),
    weaknessesList: document.getElementById('weaknesses-list'),
    recommendationsList: document.getElementById('recommendations-list'),

    // Improved
    improvedSection: document.getElementById('improved-section'),
    improvedPrompt: document.getElementById('improved-prompt'),
    copyBtn: document.getElementById('copy-btn')
};

// ============================================================================
// STATE
// ============================================================================

let currentText = '';
let isAnalyzing = false;

// ============================================================================
// API FUNCTIONS
// ============================================================================

/**
 * Проверка статуса API.
 */
async function checkAPIStatus() {
    try {
        const response = await fetch(`${CONFIG.API_URL}/health`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            setOnlineStatus(data.backend_available);
        } else {
            setOfflineStatus();
        }
    } catch (error) {
        setOfflineStatus();
    }
}

/**
 * Анализ промпта через API.
 */
async function analyzePrompt(text) {
    const response = await fetch(`${CONFIG.API_URL}/review`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            prompt_text: text,
            user_id: generateUserId(),
            source: 'web',
            review_mode: 'standard'
        })
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail?.message || `Ошибка сервера: ${response.status}`);
    }

    return await response.json();
}

// ============================================================================
// UI FUNCTIONS
// ============================================================================

/**
 * Установка онлайн статуса.
 */
function setOnlineStatus(backendAvailable) {
    elements.statusIndicator.classList.add('online');
    elements.statusIndicator.classList.remove('error');
    elements.statusText.textContent = backendAvailable
        ? 'Backend Online'
        : 'Backend Offline';
}

/**
 * Установка офлайн статуса.
 */
function setOfflineStatus() {
    elements.statusIndicator.classList.remove('online');
    elements.statusIndicator.classList.add('error');
    elements.statusText.textContent = 'API недоступен';
}

/**
 * Обновление счётчика символов.
 */
function updateCharCount() {
    const length = elements.promptInput.value.length;
    elements.charCount.textContent = length.toLocaleString('ru-RU');
}

/**
 * Генерация уникального ID пользователя.
 */
function generateUserId() {
    const stored = localStorage.getItem('promptReviewUserId');
    if (stored) return stored;

    const userId = `web:${Date.now()}:${Math.random().toString(36).substring(2, 11)}`;
    localStorage.setItem('promptReviewUserId', userId);
    return userId;
}

/**
 * Показать секцию загрузки.
 */
function showLoading() {
    elements.loadingSection.style.display = 'block';
    elements.errorSection.style.display = 'none';
    elements.resultsSection.style.display = 'none';
    elements.notPromptResult.style.display = 'none';
    elements.promptResult.style.display = 'none';
}

/**
 * Показать секцию ошибки.
 */
function showError(message) {
    elements.loadingSection.style.display = 'none';
    elements.errorSection.style.display = 'block';
    elements.resultsSection.style.display = 'none';
    elements.errorMessage.textContent = message;
}

/**
 * Показать секцию результатов.
 */
function showResults() {
    elements.loadingSection.style.display = 'none';
    elements.errorSection.style.display = 'none';
    elements.resultsSection.style.display = 'block';
}

/**
 * Отображение результатов для не-промпта.
 */
function renderNotPromptResult(data) {
    showResults();

    elements.notPromptResult.style.display = 'block';
    elements.promptResult.style.display = 'none';

    // Причина
    elements.notPromptReason.textContent = data.reason || 'Текст не содержит инструкций для AI-модели.';

    // Метрики
    if (data.metrics) {
        elements.notPromptChars.textContent = data.metrics.characters?.toLocaleString('ru-RU') || '0';
        elements.notPromptWords.textContent = data.metrics.words?.toLocaleString('ru-RU') || '0';
        elements.notPromptLines.textContent = data.metrics.lines?.toLocaleString('ru-RU') || '0';
    }

    // Варианты преобразования
    if (data.conversion_options && data.conversion_options.length > 0) {
        elements.conversionList.innerHTML = data.conversion_options
            .map(option => `<li>${escapeHtml(option)}</li>`)
            .join('');
    } else {
        elements.conversionList.innerHTML = '<li>Добавьте роль: "Ты — ..."</li><li>Укажите цель: "Сделай так-то..."</li>';
    }

    // Время обработки
    elements.notPromptTime.textContent = `Время обработки: ${data.processing_time_ms || 0} мс`;
}

/**
 * Отображение результатов для промпта.
 */
function renderPromptResult(data) {
    showResults();

    elements.notPromptResult.style.display = 'none';
    elements.promptResult.style.display = 'block';

    // Качество
    const qualityLevel = data.quality_level || 'not_applicable';
    const qualityIcons = {
        'excellent': '🌟',
        'good': '✅',
        'fair': '⚠️',
        'poor': '❌',
        'not_applicable': '❓'
    };
    const qualityLabels = {
        'excellent': 'Отлично',
        'good': 'Хорошо',
        'fair': 'Удовлетворительно',
        'poor': 'Плохо',
        'not_applicable': 'Не применимо'
    };

    elements.qualityIcon.textContent = qualityIcons[qualityLevel] || '📊';
    elements.qualitySubtitle.textContent = data.purpose
        ? `Назначение: ${truncate(data.purpose, 100)}`
        : 'Промпт проанализирован';

    // Установка класса для карточки
    elements.qualityCard.className = 'result-card quality-card';
    elements.qualityCard.classList.add(qualityLevel);

    // Badge
    elements.qualityValue.textContent = qualityLabels[qualityLevel] || '—';
    elements.qualityValue.className = `quality-value ${qualityLevel}`;

    // Назначение
    if (data.purpose) {
        elements.purposeSection.style.display = 'block';
        elements.purposeText.textContent = data.purpose;
    } else {
        elements.purposeSection.style.display = 'none';
    }

    // Оценки
    if (data.scores) {
        renderScores(data.scores);
    }

    // Сильные стороны
    if (data.strengths && data.strengths.length > 0) {
        elements.strengthsList.innerHTML = data.strengths
            .map(s => `<li>${escapeHtml(s)}</li>`)
            .join('');
    } else {
        elements.strengthsList.innerHTML = '<li>Сильные стороны не определены</li>';
    }

    // Слабые стороны
    if (data.weaknesses && data.weaknesses.length > 0) {
        elements.weaknessesList.innerHTML = data.weaknesses
            .map(w => `<li>${escapeHtml(w)}</li>`)
            .join('');
    } else {
        elements.weaknessesList.innerHTML = '<li>Слабые стороны не определены</li>';
    }

    // Рекомендации
    if (data.recommendations && data.recommendations.length > 0) {
        elements.recommendationsList.innerHTML = data.recommendations
            .map(r => `
                <li class="recommendation-item">
                    <span class="recommendation-priority ${r.priority || 'medium'}">${r.priority || 'medium'}</span>
                    <span class="recommendation-text">${escapeHtml(r.text)}</span>
                </li>
            `)
            .join('');
    } else {
        elements.recommendationsList.innerHTML = '<li class="recommendation-item"><span class="recommendation-text">Рекомендации не сформированы</span></li>';
    }

    // Улучшенная редакция
    if (data.revised_prompt) {
        elements.improvedSection.style.display = 'block';
        elements.improvedPrompt.textContent = data.revised_prompt;
    } else {
        elements.improvedSection.style.display = 'none';
    }

    // Время обработки
    elements.promptTime.textContent = `Время обработки: ${data.processing_time_ms || 0} мс`;
}

/**
 * Отображение оценок.
 */
function renderScores(scores) {
    const criteriaLabels = {
        'clarity': 'Понятность',
        'completeness': 'Полнота',
        'ambiguity_absence': 'Отсутствие неоднозначностей',
        'target_audience_fit': 'Соответствие аудитории',
        'output_format': 'Формат результата',
        'constraints_quality': 'Качество ограничений',
        'missing_assumptions': 'Достаточность предположений',
        'structure_reusability': 'Структурированность'
    };

    const scoreItems = Object.entries(scores)
        .filter(([key]) => key !== 'overall')
        .map(([key, value]) => {
            const label = criteriaLabels[key] || key;
            const safeValue = Math.min(10, Math.max(0, Number(value) || 0));
            const percentage = safeValue * 10;

            return `
                <div class="score-item">
                    <div class="score-header">
                        <span class="score-label">${label}</span>
                        <span class="score-value">${safeValue}/10</span>
                    </div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${percentage}%"></div>
                    </div>
                </div>
            `;
        });

    elements.scoresGrid.innerHTML = scoreItems.join('');

    // Общая оценка
    const overall = scores.overall || 0;
    elements.overallScore.innerHTML = `<span class="overall-label">Общая оценка:</span><span class="overall-value">${overall.toFixed(1)}/10</span>`;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Экранирование HTML.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Сокращение текста.
 */
function truncate(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Валидация текста.
 */
function validateText(text) {
    if (!text || text.trim().length < CONFIG.MIN_TEXT_LENGTH) {
        throw new Error(`Минимальная длина текста — ${CONFIG.MIN_TEXT_LENGTH} символов.`);
    }
    if (text.length > CONFIG.MAX_TEXT_LENGTH) {
        throw new Error(`Максимальная длина текста — ${CONFIG.MAX_TEXT_LENGTH.toLocaleString('ru-RU')} символов.`);
    }
    return text.trim();
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

/**
 * Обработка ввода текста.
 */
function handleInput() {
    currentText = elements.promptInput.value;
    updateCharCount();
}

/**
 * Обработка нажатия кнопки анализа.
 */
async function handleAnalyze() {
    if (isAnalyzing) return;

    try {
        const text = validateText(elements.promptInput.value);

        isAnalyzing = true;
        elements.analyzeBtn.disabled = true;
        showLoading();

        const result = await analyzePrompt(text);

        // Отображение результата
        if (result.is_prompt) {
            renderPromptResult(result);
        } else {
            renderNotPromptResult(result);
        }

    } catch (error) {
        console.error('Analysis error:', error);
        showError(error.message || 'Произошла неизвестная ошибка. Попробуйте позже.');
    } finally {
        isAnalyzing = false;
        elements.analyzeBtn.disabled = false;
    }
}

/**
 * Обработка копирования улучшенного промпта.
 */
async function handleCopy() {
    try {
        const text = elements.improvedPrompt.textContent;
        await navigator.clipboard.writeText(text);

        // Визуальная обратная связь
        const originalText = elements.copyBtn.innerHTML;
        elements.copyBtn.innerHTML = '✓';
        elements.copyBtn.style.color = 'var(--success)';

        setTimeout(() => {
            elements.copyBtn.innerHTML = originalText;
            elements.copyBtn.style.color = '';
        }, 2000);
    } catch (error) {
        console.error('Copy error:', error);
    }
}

/**
 * Обработка повтора при ошибке.
 */
function handleRetry() {
    handleAnalyze();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

function init() {
    // Проверка статуса API
    checkAPIStatus();
    setInterval(checkAPIStatus, 30000); // Каждые 30 секунд

    // Привязка обработчиков
    elements.promptInput.addEventListener('input', handleInput);
    elements.analyzeBtn.addEventListener('click', handleAnalyze);
    elements.errorRetryBtn.addEventListener('click', handleRetry);
    elements.copyBtn.addEventListener('click', handleCopy);

    // Инициализация счётчика
    updateCharCount();

    // Обработка Enter
    elements.promptInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
            handleAnalyze();
        }
    });
}

// Запуск при загрузке страницы
document.addEventListener('DOMContentLoaded', init);