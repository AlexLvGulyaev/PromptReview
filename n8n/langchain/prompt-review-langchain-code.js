/**
 * Prompt Review Agent - LangChain Code for n8n
 * Второй сценарий PEl05: n8n + LangChain
 *
 * Конвейер обработки:
 * 1. extractInput - извлечение текста
 * 2. collectPromptMetrics - расчёт метрик
 * 3. classifyPrompt - классификация текста
 * 4. reviewPrompt - анализ качества (если is_prompt = true)
 * 5. rewritePrompt - улучшение редакции (если is_prompt = true)
 * 6. composeResult - формирование итогового JSON
 */

// ============================================================================
// УТИЛИТЫ
// ============================================================================

/**
 * Универсальная функция парсинга JSON-ответа от LLM
 */
function parseJsonResponse(response) {
  try {
    const content = response.content || response;
    let cleaned = content
      .replace(/^```json\s*/i, '')
      .replace(/^```\s*/i, '')
      .replace(/```$/i, '')
      .trim();
    return JSON.parse(cleaned);
  } catch (error) {
    throw new Error(`Failed to parse JSON response: ${error.message}\nOriginal response: ${JSON.stringify(response)}`);
  }
}

/**
 * Генерация уникального ID запроса
 */
function generateRequestId() {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ============================================================================
// 1. EXTRACT INPUT
// ============================================================================

function extractInput(inputData) {
  const textFieldNames = ['chatInput', 'message', 'text', 'prompt_text', 'promptText'];
  let promptText = null;

  for (const field of textFieldNames) {
    if (inputData[field] && typeof inputData[field] === 'string') {
      promptText = inputData[field];
      break;
    }
  }

  if (!promptText) {
    throw new Error('No valid text field found in input. Expected: chatInput, message, text, prompt_text, or promptText');
  }

  return {
    request_id: generateRequestId(),
    source: inputData.source || 'n8n-chat',
    review_mode: inputData.review_mode || 'standard',
    prompt_text: promptText
  };
}

// ============================================================================
// 2. COLLECT PROMPT METRICS
// ============================================================================

function collectPromptMetrics(promptText) {
  const lines = promptText.split('\n');
  const nonEmptyLines = lines.filter(line => line.trim().length > 0);
  const words = promptText.match(/\b[\wА-Яа-яЁё-]+\b/g) || [];
  const markdownHeadings = lines.filter(line => line.trim().startsWith('#'));
  const bulletItems = lines.filter(line => /^\s*(-|\*|\+)\s+/.test(line));
  const numberedItems = lines.filter(line => /^\s*\d+[\.)]\s+/.test(line));
  const markdownTables = lines.filter(line => line.includes('|') && line.trim().startsWith('|'));
  const xmlTags = promptText.match(/<\/?[A-Za-z_][A-Za-z0-9_-]*>/g) || [];
  const codeBlocks = (promptText.match(/```/g) || []).length / 2;
  const maxLineLength = lines.reduce((max, line) => Math.max(max, line.length), 0);
  const avgLineLength = nonEmptyLines.length > 0
    ? Math.round(nonEmptyLines.reduce((sum, line) => sum + line.length, 0) / nonEmptyLines.length)
    : 0;

  return {
    characters: promptText.length,
    words: words.length,
    lines: lines.length,
    non_empty_lines: nonEmptyLines.length,
    markdown_headings: markdownHeadings.length,
    bullet_items: bulletItems.length,
    numbered_items: numberedItems.length,
    markdown_table_lines: markdownTables.length,
    xml_tags: xmlTags.length,
    code_blocks: Math.floor(codeBlocks),
    max_line_length: maxLineLength,
    avg_line_length: avgLineLength
  };
}

// ============================================================================
// 3. CLASSIFY PROMPT
// ============================================================================

const CLASSIFIER_PROMPT = `Ты — классификатор текстов.
Твоя задача — определить, является ли входной текст промптом для языковой модели.

Промпт — это инструкция или описание задачи, предназначенные для выполнения языковой моделью.

Признаки промпта:
- Присутствие ролевых инструкций ("Ты —...", "Act as...")
- Описание задачи или действий
- Указание формата результата
- Условия и ограничения
- Примеры или шаблоны

Признаки НЕ промпта:
- Обычный разговорный текст
- Вопрос без контекста задачи
- Описание ситуации без инструкции
- Повествовательный текст
- Фактическое утверждение

Проанализируй следующий текст и верни СТРОГО JSON без markdown:

{format_instructions}

Текст для анализа:
{prompt_text}`;

const CLASSIFIER_FORMAT_INSTRUCTIONS = `{
  "is_prompt": boolean,
  "reason": "строка с объяснением решения",
  "confidence": число от 0 до 1
}`;

async function classifyPrompt(llm, request) {
  const prompt = ChatPromptTemplate.fromTemplate(CLASSIFIER_PROMPT);
  const chain = prompt.pipe(llm);
  const response = await chain.invoke({
    prompt_text: request.prompt_text,
    format_instructions: CLASSIFIER_FORMAT_INSTRUCTIONS
  });
  const result = parseJsonResponse(response);
  return {
    is_prompt: result.is_prompt || false,
    reason: result.reason || 'Не удалось определить',
    confidence: result.confidence || 0.5
  };
}

// ============================================================================
// 4. REVIEW PROMPT
// ============================================================================

const REVIEW_PROMPT = `Ты — Prompt Review Agent.
Твоя задача — анализировать качество промптов.

Всегда отвечай на русском языке.

Метрики промпта (для справки):
{metrics}

{format_instructions}

Промпт для анализа:
{prompt_text}`;

const REVIEW_FORMAT_INSTRUCTIONS = `{
  "purpose": "краткое описание назначения промпта",
  "strengths": ["список сильных сторон"],
  "weaknesses": ["список недостатков"],
  "recommendations": ["список рекомендаций по улучшению"],
  "scores": {
    "clarity": число от 0 до 10,
    "completeness": число от 0 до 10,
    "ambiguity_absence": число от 0 до 10,
    "target_audience_fit": число от 0 до 10,
    "output_format": число от 0 до 10,
    "constraints_quality": число от 0 до 10,
    "missing_assumptions": число от 0 до 10,
    "structure_reusability": число от 0 до 10,
    "overall": число от 0 до 10
  },
  "quality_level": "один из: excellent, good, acceptable, weak, unusable"
}`;

async function reviewPrompt(llm, request, metrics) {
  const prompt = ChatPromptTemplate.fromTemplate(REVIEW_PROMPT);
  const chain = prompt.pipe(llm);
  const response = await chain.invoke({
    prompt_text: request.prompt_text,
    metrics: JSON.stringify(metrics, null, 2),
    format_instructions: REVIEW_FORMAT_INSTRUCTIONS
  });
  return parseJsonResponse(response);
}

// ============================================================================
// 5. REWRITE PROMPT
// ============================================================================

const REWRITER_PROMPT = `Ты — Prompt Engineer.
Твоя задача — подготовить улучшенную редакцию промпта.

Правила:
- Максимально сохраняй исходные формулировки пользователя
- Изменяй только те фрагменты, которые требуют улучшения
- Сохрани первоначальную цель промпта
- Сохрани целевую аудиторию
- Не меняй бизнес-смысл задачи
- Не добавляй новые требования без объективной необходимости

Исходный промпт:
{prompt_text}

Замечания по качеству:
{weaknesses}

Рекомендации:
{recommendations}

Верни СТРОГО JSON без markdown:
{format_instructions}`;

const REWRITER_FORMAT_INSTRUCTIONS = `{
  "revised_prompt": "улучшенная редакция промпта"
}`;

async function rewritePrompt(llm, request, reviewResult) {
  const prompt = ChatPromptTemplate.fromTemplate(REWRITER_PROMPT);
  const chain = prompt.pipe(llm);
  const response = await chain.invoke({
    prompt_text: request.prompt_text,
    weaknesses: reviewResult.weaknesses.join('\n'),
    recommendations: reviewResult.recommendations.join('\n'),
    format_instructions: REWRITER_FORMAT_INSTRUCTIONS
  });
  const result = parseJsonResponse(response);
  return result.revised_prompt;
}

// ============================================================================
// 6. COMPOSER
// ============================================================================

function composeResult(request, metrics, reviewResult, revisedPrompt) {
  return {
    request_id: request.request_id,
    is_prompt: true,
    purpose: reviewResult.purpose,
    strengths: reviewResult.strengths,
    weaknesses: reviewResult.weaknesses,
    recommendations: reviewResult.recommendations,
    scores: reviewResult.scores,
    quality_level: reviewResult.quality_level,
    revised_prompt: revisedPrompt,
    reason: null,
    conversion_options: [],
    metrics: metrics,
    notes: []
  };
}

function composeNotPrompt(request, metrics, classification) {
  return {
    request_id: request.request_id,
    is_prompt: false,
    purpose: null,
    strengths: [],
    weaknesses: [],
    recommendations: [],
    scores: {
      clarity: 0,
      completeness: 0,
      ambiguity_absence: 0,
      target_audience_fit: 0,
      output_format: 0,
      constraints_quality: 0,
      missing_assumptions: 0,
      structure_reusability: 0,
      overall: 0
    },
    quality_level: 'not_applicable',
    revised_prompt: null,
    reason: classification.reason,
    conversion_options: [
      'Добавьте ролевую инструкцию (например: "Ты — ...")',
      'Укажите ожидаемый формат результата',
      'Опишите конкретную задачу'
    ],
    metrics: metrics,
    notes: ['Текст не является промптом для языковой модели']
  };
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

async function main() {
  try {
    // Получаем модель из подключения
    const llm = await this.getInputConnectionData("ai_languageModel", 0);
    if (!llm) {
      throw new Error('No language model connected. Please connect OpenAI Chat Model to LangChain Code node.');
    }

    // Получаем входные данные
    const inputData = this.getInputData();
    if (!inputData || inputData.length === 0) {
      throw new Error('No input data received from Chat Trigger.');
    }

    // Этап 1: Извлечение входных данных
    const request = extractInput(inputData[0].json);

    // Этап 2: Сбор метрик
    const metrics = collectPromptMetrics(request.prompt_text);

    // Этап 3: Классификация
    const classification = await classifyPrompt(llm, request);

    // Если текст не является промптом
    if (!classification.is_prompt) {
      return composeNotPrompt(request, metrics, classification);
    }

    // Этап 4: Анализ качества
    const reviewResult = await reviewPrompt(llm, request, metrics);

    // Этап 5: Улучшенная редакция
    const revisedPrompt = await rewritePrompt(llm, request, reviewResult);

    // Этап 6: Формирование результата
    return composeResult(request, metrics, reviewResult, revisedPrompt);

  } catch (error) {
    // Возвращаем ошибку в структурированном формате
    return {
      request_id: 'error',
      is_prompt: false,
      error: true,
      message: error.message,
      purpose: null,
      strengths: [],
      weaknesses: [],
      recommendations: [],
      scores: {
        clarity: 0,
        completeness: 0,
        ambiguity_absence: 0,
        target_audience_fit: 0,
        output_format: 0,
        constraints_quality: 0,
        missing_assumptions: 0,
        structure_reusability: 0,
        overall: 0
      },
      quality_level: 'error',
      revised_prompt: null,
      reason: `Ошибка обработки: ${error.message}`,
      conversion_options: [],
      metrics: {},
      notes: ['Произошла ошибка при обработке запроса']
    };
  }
}

// Точка входа для n8n LangChain Code node
return await main.call(this);