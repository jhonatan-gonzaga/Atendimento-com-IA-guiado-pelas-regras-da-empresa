const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const workflow = JSON.parse(fs.readFileSync(new URL('../workflows/atendimento-gemini.json', `file://${__filename}`)));
const knowledge = JSON.parse(fs.readFileSync(new URL('../knowledge/empresa.json', `file://${__filename}`)));
const code = name => workflow.nodes.find(n => n.name === name).parameters.jsCode;

function run(name, input, prepared = null) {
  const store = {};
  const context = {
    $input: { first: () => ({ json: input }) },
    $: () => ({ first: () => ({ json: prepared }) }),
    Date, JSON,
  };
  const output = vm.runInNewContext(`(() => { ${code(name)} })()`, context)[0].json;
  return { output, store };
}

const prepare = body => run('Validar e preparar', { body }).output;
const finish = (result, prepared = { sessionId: 'cliente-001', startedAt: Date.now() }) =>
  run('Validar resposta', result, prepared);
const gemini = (category, priority, response) => ({ statusCode: 200, body: { candidates: [{ content: { parts: [{ text: JSON.stringify({ category, priority, response }) }] } }] } });

test('colunas da Data Table usam expressões n8n válidas', () => {
  const table = workflow.nodes.find(n => n.name === 'Registrar atendimento');
  for (const [name, value] of Object.entries(table.parameters.columns.value)) {
    assert.equal(value, `={{ $json.logRecord.${name} }}`);
  }
  assert.equal(table.onError, 'continueErrorOutput');
});

test('mensagem válida gera solicitação Gemini e mantém base', () => {
  const p = prepare({ sessionId: 'cliente-001', message: 'Como encontro um profissional?' });
  assert.equal(p.valid, true);
  const prompt = p.geminiBody.contents[0].parts[0].text;
  const base = prompt.split('\n').find(line => line.startsWith('BASE: '));
  assert.deepEqual(JSON.parse(base.slice(6)), knowledge);
});
test('mensagem vazia retorna 400 sem chamar Gemini', () => {
  const p = prepare({ sessionId: 'cliente-001', message: ' ' });
  assert.equal(p.httpStatus, 400);
  assert.equal(p.publicResponse.status, 'error');
});
test('orçamento retorna categoria e prioridade esperadas', () => {
  const r = finish(gemini('orcamento', 'media', 'Informe o serviço desejado.'));
  assert.equal(r.output.publicResponse.category, 'orcamento');
  assert.equal(r.output.logRecord.priority, 'media');
  assert.equal(Object.hasOwn(r.output.logRecord, 'message'), false);
});
test('reclamação de alta prioridade é preservada', () => {
  assert.equal(finish(gemini('reclamacao', 'alta', 'Vamos verificar.')).output.publicResponse.priority, 'alta');
});
test('pergunta fora da base instrui o modelo a não inventar', () => {
  assert.match(prepare({ sessionId: 'cliente-001', message: 'Qual o preço?' }).geminiBody.contents[0].parts[0].text, /Não invente preço/);
  assert.equal(finish(gemini('duvida_geral', 'baixa', 'Não posso confirmar o preço.')).output.publicResponse.status, 'success');
});
test('API indisponível retorna 503', () => {
  assert.equal(finish({ statusCode: 503, body: {} }).output.httpStatus, 503);
});
test('timeout retorna erro claro', () => {
  const r = finish({ error: { message: 'ETIMEDOUT' } });
  assert.equal(r.output.httpStatus, 503);
  assert.match(r.output.publicResponse.response, /tempo limite/);
});
test('modelo inválido retorna erro claro', () => {
  assert.match(finish({ statusCode: 404, body: {} }).output.publicResponse.response, /modelo Gemini/);
});
test('JSON inválido não é enviado ao cliente', () => {
  assert.equal(finish(gemini('inventado', 'baixa', 'Teste')).output.httpStatus, 502);
});
