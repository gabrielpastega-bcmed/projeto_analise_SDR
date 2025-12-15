# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [0.6.0] - 2025-12-15

### Adicionado
- **Filtros Globais** na sidebar:
  - Período (datas de início e fim)
  - Agentes
  - Origem do Lead
  - Tags de Qualificação
  - Checkbox "Apenas Horário Comercial"
- Função `apply_filters()` centralizada para aplicar filtros em todas as páginas
- Destaque de horário comercial (08h-18h) em gráficos temporais
- Timestamps visíveis na transcrição de chat com diferença de tempo entre mensagens
- Keys únicos em todos os 18 `plotly_chart` para evitar erro de IDs duplicados

### Alterado
- Gráfico "Distribuição de Qualificação" (P1) convertido para barras horizontais
- Gráfico "TME vs Volume" (P2) dividido em dois gráficos separados
- Ordenação de barras horizontais: maior valor sempre no topo
- `get_lead_origin()` agora trata `null`, `None`, vazio como "Não Informado"
- Modelo `Organization` com campos `id` e `name` opcionais para dados incompletos

### Corrigido
- Bug `StreamlitDuplicateElementId` em gráficos Plotly (solucionado com `key=`)
- Gráficos "Volume por Origem" e "Performance por Origem" não renderizavam
- Horário comercial incorreto nos gráficos temporais (era 08-17, corrigido para 08-18)
- Remoção de tags HTML do corpo das mensagens na transcrição

---

## [0.5.0] - 2025-12-15

### Adicionado
- **Visualização de Chat vs Análise** lado-a-lado na página Insights
- Botão para carregar análises locais sem BigQuery
- Nome do remetente visível na transcrição do chat (Bot, Agente, Cliente)
- Labels com valores numéricos visíveis em todos os gráficos (sem hover)

### Alterado
- Modelo Gemini atualizado para `gemini-2.5-flash` (estável)
- Gráficos ordenados do maior para menor
- Pie charts mostram valor + porcentagem
- Implementadas boas práticas do Chart Guide

### Corrigido
- Erro `is_bot` ao carregar chat do BigQuery
- Compatibilidade com estrutura JSON aninhada (`analysis.cx`)

---

## [0.4.0] - 2025-12-12

### Adicionado
- **Persistência BigQuery** para análises qualitativas do Gemini
- Script `create_analysis_table.py` para criação da tabela de resultados
- Script `run_weekly_analysis.py` para execução de análises semanais
- Métodos `save_to_bigquery()`, `load_from_bigquery()`, `get_available_weeks()` em `BatchAnalyzer`
- Seletor de semanas no dashboard de Insights
- Documentação técnica da integração Gemini

### Alterado
- Página de Insights agora carrega resultados do BigQuery com fallback para JSON local

---

## [0.3.0] - 2025-12-10

### Adicionado
- **Integração Gemini 2.5 Flash** para análise qualitativa de conversas
- Página **🧠 Insights** no dashboard com análise de sentimento e CX
- `BatchAnalyzer` para processamento em lote com rate limiting
- Documentação completa no GitHub Pages

### Alterado
- Dashboard Multi-Página com 5 páginas especializadas

---

## [0.2.0] - 2025-12-05

### Adicionado
- **Dashboard Multi-Página** com 4 páginas (Visão Geral, Agentes, Temporal, Leads)
- Filtros globais por agente, origem e período
- Modo Lightweight para carregamento otimizado
- Tema adaptativo (claro/escuro)

### Segurança
- Anonimização de PII (emails, telefones, CPFs) conforme LGPD

---

## [0.1.0] - 2025-12-01

### Adicionado
- Setup inicial do projeto com Poetry
- Modelos Pydantic para parsing de dados
- Integração BigQuery para ingestão de dados
- Análise operacional (TME, TMA, ranking de agentes)
- CI/CD com GitHub Actions
- Testes unitários com pytest

---

## [0.0.1] - 2025-11-28

### Adicionado
- Estrutura inicial do repositório
- README com instruções básicas
- Licença Apache 2.0

---

> **Nota:** Apenas as últimas 5 versões são exibidas. Para histórico completo, consulte as [Releases no GitHub](https://github.com/gabrielpastega-empresa/projeto_analise_SDR/releases).
