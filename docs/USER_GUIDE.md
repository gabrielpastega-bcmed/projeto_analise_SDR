# Guia do Usuário - Sistema de Análise de Atendimento

## O que é este sistema?

Este sistema analisa **conversas de atendimento** (chats) para extrair informações úteis sobre:

- 🏆 **Desempenho dos atendentes** (quem responde mais rápido?)
- 🔥 **Produtos mais procurados** (o que os clientes mais perguntam?)
- 📊 **Resultados de vendas** (quantos chats viram vendas?)
- 😊 **Satisfação do cliente** (o atendimento foi bom?)

---

## Como funciona? (Explicação Simples)

Imagine que você tem milhares de conversas de WhatsApp com clientes. Ler todas manualmente seria impossível, certo?

Este sistema **lê automaticamente** todas essas conversas e responde perguntas como:

| Pergunta | O sistema responde |
|----------|---------------------|
| "Qual atendente é mais rápido?" | Lista ordenada por velocidade |
| "Quais produtos são mais pedidos?" | Top 10 mais mencionados |
| "Quantas vendas fechamos?" | Números e porcentagens |
| "Por que perdemos vendas?" | Principais motivos |

---

## O Dashboard (Painel Visual)

O sistema tem um **painel interativo** onde você pode ver os resultados:

### O que você encontra no painel:

#### 1. 📈 Métricas Gerais
- **Total de Chats**: Quantas conversas foram analisadas
- **TME Médio**: Tempo que o cliente espera por resposta
- **TMA Médio**: Duração média das conversas
- **Taxa de Conversão**: Quantos % viraram vendas

#### 2. 🏆 Ranking de Atendentes
- Lista dos atendentes ordenados por velocidade
- Pontuação de "humanização" (1-5)
- Quantidade de atendimentos

#### 3. 🔥 Produtos Mais Pedidos
- Gráfico de pizza mostrando distribuição
- Lista dos mais mencionados

#### 4. 📊 Funil de Vendas
- Quantos estão "em progresso"
- Quantos foram "convertidos"
- Quantos foram "perdidos"

---

## Perguntas Frequentes

### "Como acesso o painel?"
1. Abra o terminal
2. Navegue até a pasta do projeto
3. Execute: `poetry run streamlit run dashboard.py`
4. Abra o navegador em `http://localhost:8501`

### "De onde vêm os dados?"
Os dados vêm de arquivos JSON exportados do sistema de chat (ex: cama na cloud
 Zenvia, Hubspot, etc.). No futuro, será integrado diretamente com o BigQuery.

### "Com que frequência devo rodar a análise?"
Recomendamos rodar **semanalmente** para acompanhar tendências, ou **mensalmente** para relatórios executivos.

### "Posso filtrar por período?"
Ainda não. Esta funcionalidade está planejada para versões futuras.

### "Os dados são confiáveis?"
- **Métricas quantitativas** (TME, TMA): São calculadas matematicamente, alta confiabilidade.
- **Análises qualitativas** (sentimento, produtos): Atualmente usam dados simulados. Quando integrado com LLM real, terão ~85% de precisão.

---

## Glossário de Termos

| Termo | Significado |
|-------|-------------|
| **TME** | Tempo Médio de Espera - quanto o cliente espera por resposta |
| **TMA** | Tempo Médio de Atendimento - duração total do chat |
| **LLM** | Large Language Model - IA que "entende" texto (tipo ChatGPT) |
| **Dashboard** | Painel visual com gráficos e números |
| **Funil** | Visualização do "caminho" do cliente até a compra |
| **Conversão** | Quando um chat resulta em venda |
| **Top of Mind** | Produtos que estão "na cabeça" dos clientes |

---

## Métricas Explicadas

### TME (Tempo Médio de Espera)
**O que é?** O tempo que o cliente fica esperando uma resposta do atendente.

**Por que importa?** Clientes que esperam muito ficam insatisfeitos e podem desistir.

**Meta recomendada:** Menos de 2 minutos.

---

### TMA (Tempo Médio de Atendimento)
**O que é?** Quanto tempo dura a conversa inteira (do início ao fim).

**Por que importa?** Conversas muito longas podem indicar dificuldade em resolver problemas. Conversas muito curtas podem indicar respostas superficiais.

**Meta recomendada:** Depende do tipo de produto/serviço.

---

### Taxa de Conversão
**O que é?** Porcentagem de conversas que resultaram em venda.

**Cálculo:** (Chats convertidos / Total de chats) × 100

**Por que importa?** Mostra a efetividade do time de vendas.

---

### Score de Humanização (1-5)
**O que é?** Avaliação de quão "humana" foi a conversa.

| Score | Significado |
|-------|-------------|
| 1 | Muito robótico, respostas genéricas |
| 2-3 | Neutro, funcional |
| 4-5 | Personalizado, empático |

---

## Contato e Suporte

Para dúvidas sobre o sistema, entre em contato com a equipe de tecnologia ou abra uma Issue no GitHub do projeto.
