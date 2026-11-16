# Solução de problemas

| Sintoma | Verificação e ação |
|---|---|
| Webhook 404 | Ative o workflow para `/webhook/`; no modo teste use `/webhook-test/` enquanto o editor aguarda. |
| HTTP 400 | Envie JSON com `sessionId` de 1 a 64 caracteres alfanuméricos, `_` ou `-`, e `message` de 1 a 4000 caracteres. |
| HTTP 401/403 na API Gemini | Reconfira `x-goog-api-key` na credencial Header Auth de cada nó. |
| HTTP 404 na API Gemini | Liste modelos com `check-gemini.py`, altere `MODEL` no gerador e reimporte. |
| HTTP 429 | Aguarde a cota liberar; o fluxo não repete 429 automaticamente. |
| HTTP 500/502/503/504 | O fluxo tenta novamente uma vez após 2 s e então devolve erro 503. |
| `EAI_AGAIN` ou timeout | Rode `check-network.sh`; confira se `/etc/resolv.conf` do container tem um `nameserver`. Se estiver vazio, siga a correção em `instalacao.md`. |
| Resposta 502 com JSON inválido | Confira `candidates[0].content.parts` no teste manual; confirme que o modelo aceita `responseMimeType: application/json`. |
| Sem registros | Confirme que a Data Table `atendimento_mvp` existe no mesmo projeto e que as seis colunas têm os tipos documentados. |

O host alcança a API por IPv4, mas não por IPv6. O resolver do container estava vazio antes da recriação e agora contém um `nameserver`. O usuário atual ainda não tem acesso ao socket Docker para inspecionar logs; a leitura do resolver é possível via `/proc/<pid-do-n8n>/root/etc/resolv.conf`.
