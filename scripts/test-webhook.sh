#!/usr/bin/env bash
set -euo pipefail
base="${N8N_URL:-http://127.0.0.1:5678}"
path="${WEBHOOK_PATH:-webhook/atendimento-empresarial}"
url="${base%/}/$path"
echo 'Entrada inválida (esperado HTTP 400):'
curl -sS -i --max-time 55 -H 'Content-Type: application/json' -d '{"sessionId":"cliente-001","message":""}' "$url"
echo
echo 'Orçamento (esperado JSON de sucesso):'
curl -sS -i --max-time 55 -H 'Content-Type: application/json' -d '{"sessionId":"cliente-001","message":"Gostaria de solicitar um orçamento para um site."}' "$url"
echo
