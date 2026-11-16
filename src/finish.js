const request = $('Validar e preparar').first().json;
const result = $input.first().json;
const code = Number(result.statusCode || result.error?.httpCode || result.error?.statusCode || 0);
let httpStatus = 200;
let response;

if (result.error || code >= 400 || (code && code < 200)) {
  httpStatus = code === 401 || code === 403 ? 502 : code === 429 ? 503 : code === 404 ? 502 : 503;
  const detail = String(result.error?.message || result.message || '');
  const reason = code === 401 || code === 403 ? 'A credencial Gemini foi rejeitada.'
    : code === 404 ? 'O modelo Gemini configurado não está disponível.'
    : code === 429 ? 'O limite de requisições do Gemini foi atingido. Tente novamente mais tarde.'
    : /EAI_AGAIN|ENOTFOUND|DNS/i.test(detail) ? 'Falha de resolução DNS ao acessar o Gemini.'
    : /timeout|ETIMEDOUT|ECONNABORTED/i.test(detail) ? 'O Gemini não respondeu dentro do tempo limite.'
    : 'O Gemini está temporariamente indisponível.';
  response = { sessionId: request.sessionId, category: 'outros', priority: 'media', response: reason, status: 'error' };
} else {
  try {
    const text = result.body?.candidates?.[0]?.content?.parts?.map(p => p.text || '').join('');
    const parsed = JSON.parse(text);
    const categories = ['duvida_geral', 'orcamento', 'reclamacao', 'suporte_tecnico', 'outros'];
    const priorities = ['baixa', 'media', 'alta'];
    if (!categories.includes(parsed.category) || !priorities.includes(parsed.priority)
      || typeof parsed.response !== 'string' || !parsed.response.trim() || parsed.response.length > 2000) {
      throw new Error('Resposta fora do contrato');
    }
    response = { sessionId: request.sessionId, category: parsed.category, priority: parsed.priority, response: parsed.response.trim(), status: 'success' };
  } catch {
    httpStatus = 502;
    response = { sessionId: request.sessionId, category: 'outros', priority: 'media', response: 'Não foi possível validar a resposta do Gemini. Tente novamente.', status: 'error' };
  }
}

const logRecord = {
  sessionId: response.sessionId,
  category: response.category,
  priority: response.priority,
  status: response.status,
  timestamp: new Date().toISOString(),
  processingMs: Date.now() - request.startedAt,
};
return [{ json: { httpStatus, publicResponse: response, logRecord } }];
