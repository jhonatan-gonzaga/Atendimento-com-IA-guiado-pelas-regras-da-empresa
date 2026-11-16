#!/usr/bin/env bash
set -u
domain=generativelanguage.googleapis.com
echo 'DNS no host:'
getent ahostsv4 "$domain" | head -3 || true
getent ahostsv6 "$domain" | head -3 || true
echo 'HTTPS no host (HTTP 400/403 também comprovam conectividade):'
curl -sS -o /dev/null -w 'IPv4: HTTP %{http_code}, DNS %{time_namelookup}s, total %{time_total}s\n' -4 --connect-timeout 5 --max-time 12 "https://$domain/v1beta/models" || true
curl -sS -o /dev/null -w 'IPv6: HTTP %{http_code}, DNS %{time_namelookup}s, total %{time_total}s\n' -6 --connect-timeout 5 --max-time 12 "https://$domain/v1beta/models" || true
echo 'Docker (se houver permissão):'
if docker info >/dev/null 2>&1; then
  docker ps --format '{{.Names}} {{.Image}} {{.Ports}}'
  if docker inspect n8n >/dev/null 2>&1; then
    docker inspect n8n --format 'network={{.HostConfig.NetworkMode}} dns={{json .HostConfig.Dns}}'
    docker exec n8n sh -c 'cat /etc/resolv.conf; getent hosts generativelanguage.googleapis.com' || true
    docker exec n8n node -e 'const https=require("node:https");const r=https.get("https://generativelanguage.googleapis.com/v1beta/models",x=>{console.log("HTTPS no container:",x.statusCode);x.resume()});r.setTimeout(10000,()=>r.destroy(new Error("timeout")));r.on("error",e=>console.log("HTTPS no container:",e.code||e.message))' || true
    echo 'Tipos de erro nos últimos logs (sem conteúdo das mensagens):'
    docker logs --tail 100 n8n 2>&1 | rg -io 'EAI_AGAIN|ENOTFOUND|ETIMEDOUT|ECONNREFUSED|ECONNRESET' | sort | uniq -c || true
  fi
else
  echo 'Sem acesso ao socket Docker; execute como usuário autorizado para inspecionar container e logs.'
  n8n_pid=$(pgrep -u "$(id -u)" -x n8n | head -1)
  if [[ -n "$n8n_pid" && -r "/proc/$n8n_pid/root/etc/resolv.conf" ]]; then
    echo 'DNS do container via /proc:'
    rg '^nameserver[[:space:]]+' "/proc/$n8n_pid/root/etc/resolv.conf" || echo 'Nenhum nameserver no container.'
  fi
fi
