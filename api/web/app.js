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
    MAX_TEXT_LENGTH: 10000,
    DEMO_TOKEN_KEY: 'promptReviewDemoToken'
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
    copyBtn: document.getElementById('copy-btn'),

    // Demo session (demo mode)
    demoBadge: document.getElementById('demo-badge'),
    demoDot: document.getElementById('demo-dot'),
    demoDetail: document.getElementById('demo-detail'),
    demoNewBtn: document.getElementById('demo-new-btn'),
    demoExhausted: document.getElementById('demo-exhausted')
};

// ============================================================================
// STATE
// ============================================================================

let currentText = '';
let isAnalyzing = false;

// Demo session (demo mode)
let demoSession = null;       // {token, requestsRemaining, expiresAt, intervalSeconds}
let demoTimerId = null;

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
async function analyzePrompt(text, isRetry = false) {
    const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };
    if (demoSession && demoSession.token) {
        headers['x-demo-token'] = demoSession.token;
    }

    const response = await fetch(`${CONFIG.API_URL}/review`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            prompt_text: text,
            user_id: generateUserId(),
            source: 'web',
            review_mode: 'standard'
        })
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (demoSession && !isRetry && (response.status === 401 || response.status === 403)) {
            // Токен неизвестен серверу (сессия истекла или API перезапущен):
            // сбрасываем, прозрачно начинаем новую демо-сессию и повторяем запрос
            handleDemoErrors(response, errorData);
            try {
                await startDemoSession();
                return await analyzePrompt(text, true);
            } catch (recoveryError) {
                // Восстановление не удалось (например, лимит сессий с IP исчерпан) —
                // показываем его ошибку, она информативнее исходного 403
                throw new Error(recoveryError.message || errorData.message || `Ошибка сервера: ${response.status}`);
            }
        }
        handleDemoErrors(response, errorData);
        throw new Error(errorData.message || `Ошибка сервера: ${response.status}`);
    }

    // Обновляем остаток квоты из заголовка ответа
    const remaining = response.headers.get('x-demo-requests-remaining');
    if (remaining !== null && demoSession) {
        demoSession.requestsRemaining = parseInt(remaining, 10);
        updateDemoBadge();
        setDemoInputLock(demoSession.requestsRemaining <= 0);
        if (demoSession.requestsRemaining <= 0) {
            showDemoExhausted(true);
        }
    }

    return await response.json();
}

// ============================================================================
// DEMO SESSION (demo mode)
// ============================================================================

/**
 * Проверка/восстановление демо-сессии при загрузке страницы.
 */
async function initDemoSession() {
    try {
        const health = await fetch(`${CONFIG.API_URL}/health`, {
            headers: { 'Accept': 'application/json' }
        });
        if (!health.ok || !(await health.json()).demo_mode) {
            setDemoVisible(false);
            return;
        }

        const storedToken = localStorage.getItem(CONFIG.DEMO_TOKEN_KEY);
        if (storedToken) {
            const status = await getDemoStatus(storedToken);
            if (status && status.is_active && status.requests_remaining > 0) {
                demoSession = {
                    token: storedToken,
                    requestsRemaining: status.requests_remaining,
                    requestsLimit: status.requests_limit,
                    expiresAt: new Date(status.expires_at),
                    intervalSeconds: 0
                };
                updateDemoBadge();
                setDemoInputLock(demoSession.requestsRemaining <= 0);
                showDemoExhausted(demoSession.requestsRemaining <= 0);
                return;
            }
        }

        // Токена нет или он истёк — новая сессия
        localStorage.removeItem(CONFIG.DEMO_TOKEN_KEY);
        await startDemoSession();
    } catch (error) {
        console.error('Demo session init error:', error);
        setDemoVisible(false);
    }
}

/**
 * Создание новой демо-сессии.
 */
async function startDemoSession() {
    const response = await fetch(`${CONFIG.API_URL}/demo/start`, {
        method: 'POST',
        headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        // 429: слишком много сессий с этого IP — сессию не даём
        setDemoDetail(errorData.message || 'Лимит демо-сессий. Попробуйте позже.');
        setDemoDotState(false);
        showDemoExhausted(false);
        setDemoInputLock(true);
        return;
    }

    const data = await response.json();
    demoSession = {
        token: data.token,
        requestsRemaining: data.requests_remaining,
        requestsLimit: data.requests_limit,
        expiresAt: new Date(data.expires_at),
        intervalSeconds: data.interval_seconds || 0
    };
    localStorage.setItem(CONFIG.DEMO_TOKEN_KEY, data.token);

    updateDemoBadge();
    showDemoExhausted(false);
    setDemoInputLock(false);
}

/**
 * Статус демо-сессии по токену.
 */
async function getDemoStatus(token) {
    const response = await fetch(`${CONFIG.API_URL}/demo/status`, {
        headers: {
            'Accept': 'application/json',
            'x-demo-token': token
        }
    });
    if (!response.ok) return null;
    return await response.json();
}

/**
 * Кнопка «Новая демо-сессия».
 */
async function handleDemoNewSession() {
    elements.demoNewBtn.disabled = true;
    try {
        await startDemoSession();
    } catch (error) {
        console.error('New demo session error:', error);
    } finally {
        elements.demoNewBtn.disabled = false;
    }
}

/**
 * Маппинг демо-ошибок API в UX.
 */
function handleDemoErrors(response, errorData) {
    if (!demoSession) return;

    if (response.status === 401) {
        // Сессия истекла — сбрасываем, пользователь может начать новую
        localStorage.removeItem(CONFIG.DEMO_TOKEN_KEY);
        demoSession = null;
        setDemoDetail('Сессия истекла — нажмите ⟲');
        setDemoDotState(false);
        setDemoInputLock(true);
        return;
    }

    if (response.status === 429) {
        const code = errorData.error || '';
        if (code === 'demo_quota_exhausted') {
            demoSession.requestsRemaining = 0;
            updateDemoBadge();
            setDemoInputLock(true);
            showDemoExhausted(true);
        }
        // demo_rate_limit — просто показываем сообщение из ответа (throw выше)
    }
    // 403 demo_token_missing/invalid — токен неизвестен серверу (рестарт API):
    if (response.status === 403) {
        localStorage.removeItem(CONFIG.DEMO_TOKEN_KEY);
        demoSession = null;
        setDemoDetail('Токен недействителен — нажмите ⟲');
        setDemoDotState(false);
    }
}

/**
 * Показать/скрыть демо-бейдж.
 */
function setDemoVisible(visible) {
    elements.demoBadge.style.display = visible ? 'flex' : 'none';
    if (!visible) {
        showDemoExhausted(false);
        setDemoInputLock(false);
        demoSession = null;
     }
}

/**
 * Обновление содержимого бейджа.
 */
function updateDemoBadge() {
    if (!demoSession) {
        setDemoVisible(false);
        return;
    }
    setDemoVisible(true);
    setDemoDotState(true);
    startDemoTimer();
    renderDemoDetail();
}

/**
 * Текст бейджа: остаток запросов + таймер до истечения.
 */
function renderDemoDetail() {
    if (!demoSession) return;
    const minutesLeft = Math.max(0, Math.floor((demoSession.expiresAt - Date.now()) / 60000));
    const timer = `${minutesLeft} мин`;
    if (demoSession.requestsRemaining <= 0) {
        elements.demoDetail.textContent = 'квота исчерпана';
    } else {
        elements.demoDetail.textContent = `осталось ${demoSession.requestsRemaining}/${demoSession.requestsLimit} · ${timer}`;
    }
}

/**
 * Живой таймер до истечения сессии (обновление раз в минуту достаточно).
 */
function startDemoTimer() {
    if (demoTimerId) clearInterval(demoTimerId);
    demoTimerId = setInterval(() => {
        if (!demoSession) {
            clearInterval(demoTimerId);
            demoTimerId = null;
            return;
        }
        const msLeft = demoSession.expiresAt - Date.now();
        if (msLeft <= 0) {
            clearInterval(demoTimerId);
            demoTimerId = null;
            setDemoDetail('Сессия истекла — нажмите ⟲');
            setDemoDotState(false);
            return;
        }
        renderDemoDetail();
    }, 30000);
}

/**
 * Состояние точки-индикатора бейджа.
 */
function setDemoDotState(active) {
    elements.demoDot.classList.toggle('expired', !active);
}

/**
 * Краткий текст бейджа (для ошибок без сессии).
 */
function setDemoDetail(text) {
    elements.demoBadge.style.display = 'flex';
    elements.demoDetail.textContent = text;
}

/**
 * Блокировка ввода при исчерпанной квоте.
 */
function setDemoInputLock(locked) {
    elements.analyzeBtn.disabled = locked || isAnalyzing;
}

/**
 * Баннер «квота исчерпана».
 */
function showDemoExhausted(visible) {
    elements.demoExhausted.style.display = visible ? 'flex' : 'none';
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

    // Время обработки и токены
    elements.notPromptTime.textContent = formatProcessingFooter(data);
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

    // Время обработки и токены
    elements.promptTime.textContent = formatProcessingFooter(data);
}

/**
 * Строка метрик обработки: время + учёт токенов LLM (если backend их отдал).
 */
function formatProcessingFooter(data) {
    let text = `Время обработки: ${data.processing_time_ms || 0} мс`;
    const usage = data.token_usage;
    if (usage && usage.total_tokens > 0) {
        text += ` · Токены: ${usage.total_tokens} (${usage.input_tokens}/${usage.output_tokens})`;
    }
    return text;
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
        // Демо-блокировка (квота исчерпана / истёкшая сессия) перекрывает retry
        const demoLocked = demoSession && demoSession.requestsRemaining <= 0;
        elements.analyzeBtn.disabled = Boolean(demoLocked);
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

    // Демо-сессия (если включён demo mode)
    initDemoSession();

    // Привязка обработчиков
    elements.promptInput.addEventListener('input', handleInput);
    elements.analyzeBtn.addEventListener('click', handleAnalyze);
    elements.errorRetryBtn.addEventListener('click', handleRetry);
    elements.copyBtn.addEventListener('click', handleCopy);
    elements.demoNewBtn.addEventListener('click', handleDemoNewSession);

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