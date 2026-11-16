# Arquitetura

[Abra o diagrama interativo](arquitetura-interativa.html) para visualizar os componentes e o caminho da mensagem.

```text
POST /webhook/atendimento-empresarial
  → Validar e preparar (entrada, base JSON, prompt)
  → Entrada válida? ── não → HTTP 400
  → Consultar Gemini (Header Auth, 10 s)
  → Falha temporária? ── sim → aguardar 2 s → Repetir Gemini
  → Validar resposta (JSON e enumerações)
  → Registrar atendimento (Data Table local, apenas metadados)
  → Respond to Webhook (JSON, código HTTP)
```

A interface opcional em `http://127.0.0.1:8765` usa um pequeno servidor Python local: `navegador → /api/message → webhook n8n`. Ele encaminha a mensagem ao mesmo fluxo, sem expor a chave Gemini ou exigir CORS no navegador. O servidor atende apenas em localhost e não persiste mensagens.

O HTTP Request usa o endpoint `v1beta/models/{model}:generateContent` e credencial Header Auth. A [API Gemini](https://ai.google.dev/api/generate-content) aceita `x-goog-api-key`; a [API de modelos](https://ai.google.dev/api/models) lista suporte a `generateContent`. O modelo fica centralizado em `MODEL` no gerador de workflows. O teste de conexão não chama o Webhook nem registra atendimentos.

O `knowledge/empresa.json` é incorporado ao código do workflow no momento da geração. Isso mantém o export autocontido. A resposta do modelo é validada antes de ser enviada ao cliente. O retorno público só inclui os cinco campos definidos no contrato; erros internos e a base não são devolvidos.

O registro `atendimento_mvp` é uma Data Table local do n8n com apenas seis colunas de metadados. Como a gravação de execuções foi desativada, o histórico completo de mensagens não é armazenado pelo projeto.
