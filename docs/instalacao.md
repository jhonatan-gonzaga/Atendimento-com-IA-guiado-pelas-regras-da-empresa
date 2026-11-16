# Instalação e validação

1. Verifique que o n8n atual abre em `http://127.0.0.1:5678`. Não execute `docker compose down -v`.
2. Rode `bash scripts/check-network.sh`. Acesso ao socket Docker exige um usuário autorizado; sem isso, o script ainda testa host, DNS e HTTPS.
3. Rode `python3 scripts/check-gemini.py --smoke`; a chave é solicitada no terminal e não é salva. O teste deve imprimir `generateContent ...: OK`.
4. Gere os exports com `python3 scripts/build_workflows.py` e valide com `node --test tests/workflow.test.js`.
5. Crie no n8n uma credencial **Header Auth** (`x-goog-api-key` → sua chave) e a Data Table `atendimento_mvp` com colunas `sessionId`, `category`, `priority`, `status`, `timestamp` (texto) e `processingMs` (número). Em outra instância, copie o ID da tabela para `TABLE_ID` em `scripts/build_workflows.py` e regenere os exports. Importe e execute `teste-gemini.json` com essa credencial.
6. Importe `atendimento-gemini.json`. Atribua a credencial aos dois nós HTTP Request. Confirme que o caminho do Webhook é `atendimento-empresarial`, que o modo de resposta usa Respond to Webhook e que todas as conexões estão presentes.
7. Teste no editor com `/webhook-test/atendimento-empresarial`. Depois ative o workflow e rode `bash scripts/test-webhook.sh` para testar `/webhook/atendimento-empresarial`. Confirme uma linha nova na Data Table.

O arquivo `docker/compose.yaml` é referência para instalar uma instância nova. Na instalação já existente, o Compose fica em `~/projetos/n8n/compose.yaml`, com rede host e volume próprio. A correção de `NODE_OPTIONS` foi aplicada ao arquivo existente; o usuário recriou o container e confirmou o Webhook com HTTP 200.

## DNS e validação nesta instalação

O n8n em execução é a versão 2.47.7. Antes da recriação, o arquivo `/etc/resolv.conf` do container não continha `nameserver` e o HTTP Request recebia `EAI_AGAIN`. Após a recriação pelo usuário, o arquivo passou a conter um servidor DNS. O Webhook respondeu HTTP 200 para orçamento e horário; a verificação do horário gerou uma linha `success` na Data Table.

Se o problema voltar, confira o DNS e recrie somente o container n8n com uma conta autorizada a usar Docker:

```bash
cd ~/projetos/n8n
docker compose config --quiet
docker compose up -d --no-deps --force-recreate --pull never n8n
docker exec n8n cat /etc/resolv.conf
```

Confirme que o último comando mostra ao menos um `nameserver`. Esse procedimento recria somente o container n8n com a imagem local e preserva o volume `n8n_data`; haverá uma breve interrupção. Em seguida, envie uma mensagem válida ao Webhook de produção e confira a resposta HTTP 200 e uma linha `success` na Data Table. Se o resolver ainda estiver vazio, compare o DNS do host com `docker exec n8n cat /etc/resolv.conf` antes de alterar a rede ou fixar um servidor DNS no Compose.
