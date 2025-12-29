# 📚 Docs Index

## Runbooks (Operacional)

Guias passo-a-passo para operações comuns:

- [Rollback de Deploy](runbooks/rollback.md) - Como reverter um deploy problemático
- [Troubleshooting](runbooks/troubleshooting.md) - Solução de problemas comuns

## ADRs (Architecture Decision Records)

Decisões técnicas importantes com contexto e justificativa:

- [ADR-001: PostgreSQL para Autenticação](adr/001-postgresql-auth.md)
- [ADR-002: ECharts vs Plotly](adr/002-echarts-vs-plotly.md)
- [ADR-003: Streamlit como Framework](adr/003-streamlit-architecture.md)

## Como Usar

### Para Desenvolvedores

- **Leia os ADRs** antes de fazer mudanças arquiteturais
- **Crie novo ADR** para decisões importantes (use template abaixo)

### Para Operações

- **Consulte Runbooks** em emergências
- **Atualize Runbooks** após resolver novos problemas

## Template de ADR

```markdown
# ADR-XXX: [Título da Decisão]

**Status:** [Proposta | Aceita | Rejeitada | Deprecated]
**Data:** YYYY-MM-DD
**Decisores:** [Nomes]
**Tags:** [tech, database, etc]

## Contexto
[Descrever problema e requisitos]

## Decisão
[O que foi decidido]

## Consequências
[Impactos positivos e negativos]
```

---

*Última atualização: 2024-12-29*
