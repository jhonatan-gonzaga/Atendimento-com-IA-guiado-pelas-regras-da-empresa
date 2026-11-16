#!/usr/bin/env python3
"""Regenera os exports n8n a partir do JavaScript e da base de conhecimento."""
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "workflows"
OUT.mkdir(exist_ok=True)
MODEL = "gemini-3.5-flash-lite"  # Troque aqui após consultar check-gemini.py.
TABLE_ID = "tGah8bni7Sf4gqm4"  # shortcut: ID da instância local; trocar ao importar em outra instância.


def node(name, kind, version, x, y, parameters, **extra):
    return {"id": str(uuid5(NAMESPACE_URL, "n8n-ai-atendimento/" + name)), "name": name,
            "type": f"n8n-nodes-base.{kind}", "typeVersion": version,
            "position": [x, y], "parameters": parameters, **extra}


def link(target):
    return {"node": target, "type": "main", "index": 0}


def save(filename, title, nodes, connections):
    workflow = {
        "name": title, "nodes": nodes, "connections": connections, "active": False,
        "settings": {"executionOrder": "v1", "saveDataSuccessExecution": "none",
                     "saveDataErrorExecution": "none", "executionTimeout": 55},
        "pinData": {}, "tags": [],
    }
    (OUT / filename).write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n")


knowledge = json.loads((ROOT / "knowledge/empresa.json").read_text())
prepare = (ROOT / "src/prepare.js").read_text().replace(
    "__KNOWLEDGE_JSON__", json.dumps(knowledge, ensure_ascii=False)).replace(
    "__MODEL_JSON__", json.dumps(MODEL))
finish = (ROOT / "src/finish.js").read_text()

request = {
    "method": "POST",
    "url": "={{ 'https://generativelanguage.googleapis.com/v1beta/models/' + $('Validar e preparar').first().json.model + ':generateContent' }}",
    "authentication": "genericCredentialType", "genericAuthType": "httpHeaderAuth",
    "sendBody": True, "contentType": "json", "specifyBody": "json",
    "jsonBody": "={{ $json.geminiBody }}",
    "options": {"timeout": 10000, "response": {"response": {
        "fullResponse": True, "neverError": True, "responseFormat": "json"}}},
}
def respond(source):
    prior = f"$('{source}').first().json"
    return {"respondWith": "json",
            "responseBody": "={{ " + prior + ".publicResponse }}",
            "options": {"responseCode": "={{ " + prior + ".httpStatus }}"}}


columns = [("sessionId", "string"), ("category", "string"), ("priority", "string"),
           ("status", "string"), ("timestamp", "string"), ("processingMs", "number")]
table = {"resource": "row", "operation": "insert",
         "dataTableId": {"__rl": True, "mode": "list", "value": TABLE_ID,
                         "cachedResultName": "atendimento_mvp"},
         "columns": {"mappingMode": "defineBelow",
                     "value": {key: "={{ $json.logRecord." + key + " }}" for key, _ in columns},
                     "matchingColumns": [],
                     "schema": [{"id": key, "displayName": key, "required": False,
                                 "defaultMatch": False, "display": True, "type": typ,
                                 "canBeUsedToMatch": False} for key, typ in columns]},
         "options": {}}

nodes = [
    node("Receber mensagem", "webhook", 2, 0, 80,
         {"httpMethod": "POST", "path": "atendimento-empresarial",
          "responseMode": "responseNode", "options": {}},
         webhookId="atendimento-empresarial"),
    node("Validar e preparar", "code", 2, 260, 80,
         {"mode": "runOnceForAllItems", "jsCode": prepare}),
    node("Entrada válida?", "if", 2.2, 520, 80,
         {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
                         "conditions": [{"id": "valid-input", "leftValue": "={{ $json.valid }}", "rightValue": "",
                                         "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                         "combinator": "and"}, "options": {}}),
    node("Consultar Gemini", "httpRequest", 4.2, 780, -40, request,
         onError="continueRegularOutput", retryOnFail=True, maxTries=2, waitBetweenTries=1500,
         notes="Configure uma credencial Header Auth: x-goog-api-key. O modelo é definido em build_workflows.py; confirme-o com check-gemini.py."),
    node("Falha temporária?", "if", 2.2, 1040, -40,
         {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
                         "conditions": [{"id": "retryable-status", "leftValue": "={{ [500, 502, 503, 504].includes(Number($json.statusCode)) }}", "rightValue": "",
                                         "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                         "combinator": "and"}, "options": {}}),
    node("Aguardar 2 segundos", "code", 2, 1300, -160,
         {"mode": "runOnceForAllItems", "jsCode": "await new Promise(resolve => setTimeout(resolve, 2000)); return $input.all();"}),
    node("Repetir Gemini", "httpRequest", 4.2, 1560, -160,
         {**request, "jsonBody": "={{ $('Validar e preparar').first().json.geminiBody }}"},
         onError="continueRegularOutput", retryOnFail=True, maxTries=2, waitBetweenTries=1500),
    node("Validar resposta", "code", 2, 1820, 40,
         {"mode": "runOnceForAllItems", "jsCode": finish}),
    node("Registrar atendimento", "dataTable", 1.1, 2080, 40, table,
         onError="continueErrorOutput"),
    node("Responder atendimento", "respondToWebhook", 1.4, 2340, 40, respond("Validar resposta")),
    node("Registrar entrada inválida", "dataTable", 1.1, 780, 240, table,
         onError="continueErrorOutput"),
    node("Responder entrada inválida", "respondToWebhook", 1.4, 1040, 240, respond("Validar e preparar")),
    node("Responder falha de registro", "respondToWebhook", 1.4, 2340, 240,
         {"respondWith": "json",
          "responseBody": "={{ { sessionId: $('Validar e preparar').first().json.publicResponse?.sessionId || $('Validar e preparar').first().json.sessionId || null, category: 'outros', priority: 'media', response: 'Falha ao registrar atendimento.', status: 'error' } }}",
          "options": {"responseCode": 503}}),
]
connections = {
    "Receber mensagem": {"main": [[link("Validar e preparar")]]},
    "Validar e preparar": {"main": [[link("Entrada válida?")]]},
    "Entrada válida?": {"main": [[link("Consultar Gemini")], [link("Registrar entrada inválida")]]},
    "Consultar Gemini": {"main": [[link("Falha temporária?")]]},
    "Falha temporária?": {"main": [[link("Aguardar 2 segundos")], [link("Validar resposta")]]},
    "Aguardar 2 segundos": {"main": [[link("Repetir Gemini")]]},
    "Repetir Gemini": {"main": [[link("Validar resposta")]]},
    "Validar resposta": {"main": [[link("Registrar atendimento")]]},
    "Registrar atendimento": {"main": [[link("Responder atendimento")], [link("Responder falha de registro")]]},
    "Registrar entrada inválida": {"main": [[link("Responder entrada inválida")], [link("Responder falha de registro")]]},
}
save("atendimento-gemini.json", "Atender clientes com Gemini", nodes, connections)

test_nodes = [
    node("Iniciar teste", "manualTrigger", 1, 0, 0, {}),
    node("Testar Gemini", "httpRequest", 4.2, 260, 0,
         {**request, "url": f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
          "jsonBody": "={{ { contents: [{ parts: [{ text: 'Responda somente OK.' }] }] } }}"},
         onError="continueRegularOutput"),
]
save("teste-gemini.json", "Testar conexão com Gemini", test_nodes,
     {"Iniciar teste": {"main": [[link("Testar Gemini")]]}})
