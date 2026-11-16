#!/usr/bin/env python3
"""Lista modelos liberados para a chave, sem exibir a chave."""
import json
import os
import sys
from getpass import getpass
import urllib.error
import urllib.request

key = os.environ.get("GEMINI_API_KEY") or (getpass("Gemini API Key: ") if sys.stdin.isatty() else "")
if not key:
    sys.exit("Defina GEMINI_API_KEY no ambiente (sem gravá-la em arquivo).")

url = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000"
models = []
try:
    while url:
        req = urllib.request.Request(url, headers={"x-goog-api-key": key})
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.load(response)
        models += [m["name"] for m in data.get("models", [])
                   if "generateContent" in m.get("supportedGenerationMethods", [])]
        token = data.get("nextPageToken")
        url = ("https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000&pageToken=" + token) if token else None
except urllib.error.HTTPError as exc:
    sys.exit(f"Gemini respondeu HTTP {exc.code}. Verifique a chave, a cota e a rede.")
except (urllib.error.URLError, TimeoutError) as exc:
    sys.exit(f"Falha de rede ao consultar Gemini: {type(exc).__name__}.")

if "--smoke" not in sys.argv:
    for model in models:
        print(model)
if not models:
    sys.exit("Nenhum modelo com generateContent disponível para esta chave.")

if "--smoke" in sys.argv:
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    if f"models/{model}" not in models:
        sys.exit(f"Modelo {model} não apareceu na lista generateContent.")
    payload = json.dumps({
        "contents": [{"parts": [{"text": 'Retorne apenas o objeto JSON {"ok":true}.'}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=payload, headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            answer = json.load(response)
        text = answer.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if json.loads(text).get("ok") is not True:
            sys.exit("A API não retornou o JSON esperado.")
        print(f"generateContent {model}: OK")
    except urllib.error.HTTPError as exc:
        try:
            reason = json.load(exc).get("error", {}).get("status", "")
        except (ValueError, OSError):
            reason = ""
        sys.exit(f"generateContent {model}: HTTP {exc.code} {reason}.")
    except (urllib.error.URLError, TimeoutError) as exc:
        sys.exit(f"generateContent {model}: falha de rede ({type(exc).__name__}).")
