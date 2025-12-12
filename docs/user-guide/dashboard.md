# Dashboard - Manual do Usuário

Este guia explica como utilizar o **Dashboard de Análise SDR** para acompanhar KPIs e extrair insights sobre a performance do time de atendimento.

---

## 🚀 Acessando o Dashboard

1. Abra seu navegador (Chrome, Edge, Firefox)
2. Acesse o endereço fornecido pelo time de TI (normalmente `http://localhost:8501`)
3. Aguarde o carregamento da página inicial

!!! tip "Dica"
    O dashboard carrega automaticamente os dados mais recentes. Caso precise atualizar, use o botão **"🔄 Carregar/Atualizar Dados"** na barra lateral.

---

## 📊 Navegando pelas Páginas

O dashboard possui **5 páginas principais**, acessíveis pelo menu lateral esquerdo:

### 📊 Visão Geral
**O que mostra:** Resumo completo da operação - use para ter uma visão rápida do dia/semana.

| Métrica | O que significa |
|---------|-----------------|
| **Total de Atendimentos** | Quantos chats foram recebidos no período |
| **TME Médio** | Tempo médio que o cliente esperou pela primeira resposta humana |
| **Taxa de Qualificação** | % de leads classificados como potenciais compradores |
| **Distribuição de Tags** | Gráfico mostrando a classificação dos leads |

---

### 👥 Agentes
**O que mostra:** Performance individual de cada atendente.

| Métrica | O que significa | Como usar |
|---------|-----------------|-----------|
| **Ranking de TME** | Quem responde mais rápido | Identifique os melhores exemplos |
| **Taxa de Qualificação** | Quem qualifica mais leads | Avalie efetividade do atendimento |
| **TME vs Volume** | Gráfico de bolhas com performance | Encontre quem atende bem E rápido |

!!! info "Filtro: Horário Comercial"
    Marque a caixa "Apenas horário comercial" para ver métricas justas (excluindo mensagens fora do expediente).

---

### 📈 Análise Temporal
**O que mostra:** Padrões de atendimento ao longo do tempo.

| Gráfico | O que mostra | Insights possíveis |
|---------|--------------|-------------------|
| **Volume por Hora** | Picos de demanda | Quando reforçar a equipe |
| **TME por Hora** | Horários com mais demora | Quando faltam atendentes |
| **Comercial vs Fora** | Comparativo de horários | Necessidade de plantão |

---

### 🎯 Leads
**O que mostra:** Análise de origem e qualidade dos leads.

| Seção | O que mostra |
|-------|--------------|
| **Performance por Origem** | Qual canal traz mais leads qualificados |
| **Funil de Qualificação** | Quantos leads passam por cada etapa |
| **Distribuição de Tags** | Categorização detalhada dos atendimentos |

---

### 🧠 Insights (Análise com IA)
**O que mostra:** Análise qualitativa das conversas usando Google Gemini.

| Métrica | O que significa |
|---------|-----------------|
| **NPS Médio** | Previsão de satisfação do cliente (0-10) |
| **Humanização** | Quão personalizado foi o atendimento (1-5) |
| **Taxa de Conversão** | % de chats que resultaram em venda |
| **Sentimento** | Distribuição positivo/neutro/negativo |

!!! tip "Como executar a análise"
    Clique no botão **"🚀 Executar Análise com Gemini"** para processar os chats. A análise é executada sob demanda e os resultados ficam salvos.

---

## 🎛️ Usando os Filtros

### Barra Lateral - Opções de Carregamento

| Opção | O que faz |
|-------|-----------|
| **Dias para análise** | Quantos dias de histórico carregar (1-90) |
| **Limite de chats** | Máximo de atendimentos a processar |
| **Modo leve** | ✅ Mais rápido (recomendado) |

### Filtros Globais

| Filtro | Descrição |
|--------|-----------|
| **Agentes** | Ver apenas atendentes específicos |
| **Origem do Lead** | Filtrar por canal de entrada |

---

## 📈 Principais KPIs Explicados

### TME - Tempo Médio de Espera
> ⏱️ Quanto tempo o cliente aguarda até a **primeira resposta de um humano** (não conta o bot).

| Valor | Avaliação |
|-------|-----------|
| < 2 min | ✅ Excelente |
| 2-5 min | ⚠️ Aceitável |
| > 5 min | 🔴 Precisa melhorar |

---

### Taxa de Qualificação
> 🎯 Porcentagem de leads classificados como **Qualificado** ou **Qualificado Plus**.

**Como interpretar:**
- Taxa alta = Leads de boa qualidade OU bom trabalho de triagem
- Taxa baixa = Leads frios OU campanha mal direcionada

---

### Volume de Atendimentos
> 📊 Total de conversas iniciadas no período.

**Use para:**
- Dimensionar a equipe
- Medir resultado de campanhas
- Identificar sazonalidades

---

## 💡 Dicas de Uso

!!! success "Para reuniões rápidas"
    Use a página **Visão Geral** - tem todos os KPIs resumidos.

!!! info "Para feedback individual"
    Use a página **Agentes** - compare performance entre membros.

!!! warning "Para planejar escalas"
    Use a página **Análise Temporal** - veja horários de pico.

!!! tip "Para avaliar campanhas"
    Use a página **Leads** - veja qual origem traz mais qualificados.

!!! success "Para insights qualitativos"
    Use a página **Insights** - veja sentimento, humanização e tendências de produto.

---

## ❓ Perguntas Frequentes

??? question "Como atualizar os dados?"
    Clique no botão **"🔄 Carregar/Atualizar Dados"** na barra lateral.

??? question "Os dados estão demorando para carregar"
    Reduza o número de dias e ative o **"Modo leve"**.

??? question "Por que alguns gráficos estão vazios?"
    Pode ser que os filtros estejam muito restritivos. Tente desmarcar os filtros ou aumentar o período.

??? question "Posso exportar os dados?"
    Sim! Clique com o botão direito nos gráficos Plotly para baixar como imagem.

---

## 🔗 Próximos Passos

- [Entender as Métricas](metrics.md)
- [Perguntas Frequentes](faq.md)
