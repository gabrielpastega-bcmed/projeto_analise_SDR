# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [2.0.0] - 2026-01-06

### Adicionado
- **Prompts Externalizados**: Prompts de LLM movidos para `config/prompts/` para customização
- **Templates de Prompts**: Arquivos `.example.txt` incluídos como referência
- **Páginas Health e Automação**: Monitoramento de integrações e GitHub Actions
- **Sistema de Alertas**: Monitoramento em tempo real com notificações

### Corrigido
- Import quebrado em `dashboard.py` (SyntaxError)
- Código morto em `dashboard_utils.py` (linhas 191 e 1232)
- Nomes de propriedades em `filters.py` (`agentName` → `agent.name`, `timestamp` → `firstMessageDate`)
- Deprecação `asyncio.get_event_loop()` → `asyncio.get_running_loop()` (Python 3.10+)
- Import `Dict` faltante em `ingestion.py`
- Deprecação `use_container_width` → `width="stretch"` (Streamlit 1.41+)

### Alterado
- Prompts agora são carregados de arquivos externos em `config/prompts/`
- `gemini_client.py` usa método `_load_prompt()` para carregar prompts
- Documentação atualizada para refletir nova estrutura

### Segurança
- Prompts específicos agora são gitignored (`config/prompts/*.txt`)
- Apenas templates genéricos são commitados (`*.example.txt`)

---

## [1.0.0] - 2025-12-18

### Adicionado
- Dashboard multi-página com Streamlit
- Autenticação híbrida (usuário/senha + Google OAuth)
- Análise de CX, Produto, Vendas e QA via Gemini LLM
- Análise operacional (TME, TMA, ranking de agentes)
- Exportação Excel profissional com múltiplas abas
- Filtros avançados com persistência em sessão
- Integração BigQuery para dados de produção
- Integração PostgreSQL para autenticação e resultados
- Cache Redis para respostas LLM
- CI/CD com GitHub Actions
- 200+ testes unitários com 82% de cobertura
