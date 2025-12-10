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

## 🚀 Início Rápido

=== "Instalação"

    ```bash
    # Clone o repositório
    git clone https://github.com/gabrielpastega-empresa/projeto_analise_SDR.git
    cd projeto_analise_SDR

    # Instale as dependências
    poetry install
    ```

=== "Executar Análise"

    ```bash
    # Pipeline principal
    poetry run python main.py

    # Dashboard interativo
    poetry run streamlit run dashboard.py
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

## 📊 Exemplo de Métricas

!!! success "TME (Tempo Médio de Espera)"
    Quanto tempo o cliente aguarda por uma resposta.

    **Meta recomendada:** < 2 minutos

!!! info "TMA (Tempo Médio de Atendimento)"
    Duração total da conversa.

!!! warning "Taxa de Conversão"
    Porcentagem de chats que resultam em venda.

---

## 🔗 Links Úteis

- [GitHub](https://github.com/gabrielpastega-empresa/projeto_analise_SDR)
- [Dashboard](http://localhost:8501) (local)
