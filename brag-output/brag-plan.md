# Brag Plan: Atendimento Conecta Obras

## O projeto
MVP de atendimento informativo: a pessoa pergunta na interface web; o n8n valida, consulta o Gemini com uma base de regras da Conecta Obras e devolve resposta, categoria e prioridade.

## Ângulo e gancho
Uma pergunta simples percorre uma automação visível. A abertura mostra a pergunta “Como encontro um profissional?” antes de revelar o atendimento.

## Momentos centrais
- A interface real do projeto, com a pergunta de exemplo e uma resposta de demonstração baseada no README. Os dados são fictícios; não há captura de conversas reais.
- O percurso interface → n8n → Gemini → resposta, com a base `empresa.json` alimentando o prompt.
- A regra de reaproveitamento: trocar a base, gerar o export e publicar o workflow atualizado.

## Fecho
“Conecta Obras · Atendimento informativo com n8n + Gemini”.

## Fluxo de uso
Abrir o chat → enviar pergunta → receber explicação e classificação. É uma simulação visual baseada no contrato documentado; não grava uma execução ao vivo.

## Rubrica
1. É um atendimento automatizado para dúvidas sobre a plataforma Conecta Obras.
2. O fluxo usa regras da empresa e classifica a resposta; pode ser adaptado por `empresa.json`.
3. A interface em verde escuro e creme, com as bolhas do chat, é o gancho visual.
4. Mostrar o chat real reconstruído a partir de `web/index.html`.
5. 21 segundos dão tempo para ler pergunta, resposta, arquitetura e instrução de reaproveitamento.
6. Preset `polished`; direção: demonstração clara e contida.
7. Música leve, baixa, com poucos acentos sincronizados às entradas.
8. “Um atendimento para dúvidas da Conecta Obras, com n8n, Gemini e regras de negócio em JSON.”
9. Abrir → perguntar → receber resposta e classificação.

## Identidade e formato
- Paisagem, 1920×1080, 30 fps, 21 segundos.
- Fundo `#f5f3ec`, painel `#123b44`, destaque `#bce6c4`, texto `#1b343a`.
- Títulos em Georgia; corpo em fonte de sistema, como na interface.
- Elemento real: estrutura e textos do chat em `web/index.html`.

## Áudio
- Trilha: `happy-beats-business-moves-vol-10-by-ende-dot-app.mp3`, Sascha Ende, CC BY 4.0.
- Faixa discreta, com fade no fim; acentos leves na pergunta e na resposta.
- Tempo estimado 110 BPM. Revelação final perto do pulso forte em 20,19 s. Não sacrificar leitura para alinhar texto aos pulsos.

## Storyboard

### Cena 1 — Pergunta — 3 s
Fundo verde escuro; pergunta aparece grande: “Como encontro um profissional?”. Entrada rápida e sustentação para leitura.

### Cena 2 — Atendimento em uso — 8 s
Mostrar a interface do projeto, reconstruída com a composição e as cores do HTML original. A pergunta entra no chat, seguida da resposta de demonstração documentada no README. As etiquetas “Dúvida geral” e “Prioridade baixa” aparecem no fim. Pausa suficiente para leitura.

### Cena 3 — Caminho da resposta — 5 s
Quatro blocos surgem em sequência: Interface, n8n, Gemini, Resposta. `empresa.json` entra como base de regras conectada ao n8n. O Gemini sugere a classificação e o n8n valida a resposta.

### Cena 4 — Reaproveitar — 5 s
Foco em `empresa.json` e a sequência “Editar → Gerar → Publicar”. Fecho com o nome Conecta Obras e o stack. Informar que editar o JSON sozinho não altera o workflow ativo.
