# Perguntas Frequentes (FAQ)

## Geral

### Como acesso o dashboard?
```bash
poetry run streamlit run dashboard.py
```
Depois abra `http://localhost:8501` no navegador.

---

### De onde vêm os dados?
Atualmente, de um arquivo JSON (`data/raw/exemplo.json`). No futuro, será integrado diretamente com o BigQuery.

---

### Com que frequência devo rodar a análise?
- **Semanal**: Para acompanhar tendências
- **Mensal**: Para relatórios executivos
- **Sob demanda**: Para investigar casos específicos

---

### Posso filtrar por período?
Ainda não. Esta funcionalidade está planejada para versões futuras.

---

## Métricas

### O que significa TME?
**Tempo Médio de Espera** - quanto tempo o cliente aguarda por uma resposta do atendente.

---

### O que significa TMA?
**Tempo Médio de Atendimento** - duração total da conversa, da primeira à última mensagem.

---

### Por que a taxa de conversão está baixa?
Pode ser por vários motivos:
- Preço não competitivo
- Falta de produtos em estoque
- Atendimento demorado
- Scripts de venda fracos

Consulte os "Motivos de Perda" no dashboard para entender melhor.

---

## Técnico

### Como instalo o projeto?
```bash
git clone https://github.com/gabrielpastega-bcmed/projeto_analise_SDR.git
cd projeto_analise_SDR
poetry install
```

---

### Como rodo os testes?
```bash
poetry run pytest --cov=src
```

---

### Como gero a documentação localmente?
```bash
poetry run mkdocs serve
```
Acesse `http://localhost:8000`

---

### Os dados são confiáveis?

| Tipo de Análise | Confiabilidade |
|-----------------|----------------|
| Métricas quantitativas (TME, TMA) | ✅ Alta (matemático) |
| Análises qualitativas (sentimento) | ⚠️ Mock (até integrar LLM real) |

---

## Problemas Comuns

### O dashboard não carrega
1. Verifique se instalou as dependências: `poetry install`
2. Verifique se está na pasta correta do projeto
3. Tente: `poetry run streamlit run dashboard.py --server.port 8502`

---

### Erro de import
Execute dentro do ambiente virtual:
```bash
poetry shell
python dashboard.py
```

---

### Dados não aparecem
Verifique se o arquivo `data/raw/exemplo.json` existe e está no formato correto.

---

## Contato

Para outras dúvidas, abra uma [Issue no GitHub](https://github.com/gabrielpastega-bcmed/projeto_analise_SDR/issues).
