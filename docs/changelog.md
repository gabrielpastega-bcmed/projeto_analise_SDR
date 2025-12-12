# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

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

> **Nota:** Apenas as últimas 5 versões são exibidas. Para histórico completo, consulte as [Releases no GitHub](https://github.com/gabrielpastega-bcmed/projeto_analise_SDR/releases).
