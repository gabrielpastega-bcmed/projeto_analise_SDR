# Projeto Análise SDR

Bem-vindo à documentação do **Sistema de Análise de Atendimento SDR**.

---

## 🎯 O que é este projeto?

Este sistema analisa automaticamente conversas de atendimento (chats) para extrair insights sobre:

<div class="grid cards" markdown>

- :trophy: **Performance de Agentes**

  Ranking por velocidade e qualidade de atendimento

- :fire: **Produtos Top of Mind**

  O que os clientes mais perguntam

- :chart_with_upwards_trend: **Funil de Vendas**

  Taxa de conversão e motivos de perda

- :smile: **Satisfação do Cliente**

  Análise de sentimento e humanização

</div>

---

## 📊 Dashboard Multi-Página

O sistema inclui um **dashboard interativo** com 4 páginas especializadas:

| Página | Descrição |
|--------|-----------|
| 📊 **Visão Geral** | KPIs macro, distribuição de qualificação, volume por origem, heatmap |
| 👥 **Agentes** | Ranking de TME, taxa de qualificação, scatter TME vs Volume |
| 📈 **Análise Temporal** | Volume por hora, TME por hora, comparativo horário comercial |
| 🎯 **Leads** | Performance por origem, funil de qualificação, distribuição de tags |

---

## 🚀 Início Rápido

=== "Instalação"

    ```bash
    # Clone o repositório
    git clone https://github.com/gabrielpastega-empresa/projeto_analise_SDR.git
    cd projeto_analise_SDR

    # Instale as dependências
    poetry install
    ```

=== "Executar Dashboard"

    ```bash
    # Dashboard interativo
    poetry run streamlit run dashboard.py
    ```

    Acesse em: `http://localhost:8501`

=== "Executar Análise CLI"

    ```bash
    # Pipeline de análise
    poetry run python main.py
    ```

=== "Desenvolvimento"

    ```bash
    # Testes
    poetry run pytest --cov=src

    # Lint
    poetry run ruff check .
    ```

---

## 📚 Navegação

| Seção | Descrição |
|-------|-----------|
| [Guia do Usuário](user-guide/overview.md) | Para quem vai usar o sistema |
| [Manual Técnico](technical/architecture.md) | Para desenvolvedores |
| [Contribuindo](contributing.md) | Como colaborar |

---

## 📊 Métricas Principais

!!! success "TME (Tempo Médio de Espera)"
    Tempo até a primeira resposta **humana** (não bot).

    **Meta recomendada:** < 2 minutos

!!! info "Taxa de Qualificação"
    Porcentagem de leads classificados como qualificados.

!!! warning "Conversão"
    Leads qualificados que avançam para consultor.

---

## 🔗 Links Úteis

- [GitHub](https://github.com/gabrielpastega-empresa/projeto_analise_SDR)
- [Dashboard](http://localhost:8501) (local)
