# Project Guidelines - Projeto Análise SDR

> **Versão**: 1.0
> **Última atualização**: 2025-12-18

Este documento estabelece padrões de qualidade, boas práticas de desenvolvimento e diretrizes para trabalho eficiente com AI assistants.

---

## 📋 Índice

1. [Padrões de Qualidade](#padrões-de-qualidade)
2. [Práticas de Desenvolvimento](#práticas-de-desenvolvimento)
3. [Otimização de Performance](#otimização-de-performance)
4. [Trabalhando com AI Assistants](#trabalhando-com-ai-assistants)
5. [Code Review Checklist](#code-review-checklist)

---

## 🎯 Padrões de Qualidade

### Métricas Objetivo

| Métrica | Alvo | Status v0.8.0 |
|---------|------|---------------|
| **Cobertura de Testes** | ≥ 75% | ✅ 75% |
| **Testes Passando** | 100% | ✅ 175/175 |
| **Type Coverage** | ≥ 90% | ✅ mypy strict |
| **Lint Warnings** | 0 | ✅ 0 |
| **Complexidade Ciclomática** | ≤ 10 por função | 🎯 Em monitoramento |

### Padrões de Código

**1. Type Hints Obrigatórios**
```python
# ✅ Correto
def analyze_chat(chat: Chat, validate: bool = True) -> Dict[str, Any]:
    ...

# ❌ Incorreto
def analyze_chat(chat, validate=True):
    ...
```

**2. Docstrings em Funções Públicas**
```python
# ✅ Correto - Google Style
def stream_chats_from_bigquery(
    days: Optional[int] = None,
    limit: Optional[int] = None,
) -> Iterator[Chat]:
    """
    Carrega chats do BigQuery em modo streaming.

    Args:
        days: Número de dias retroativos para carregar
        limit: Número máximo de chats

    Returns:
        Iterator de objetos Chat

    Yields:
        Chat: Objeto Chat individual
    """
    ...
```

**3. Nomes Descritivos**
```python
# ✅ Correto
def calculate_average_response_time(messages: List[Message]) -> float:
    ...

# ❌ Incorreto
def calc_avg(msgs):
    ...
```

**4. Funções Pequenas e Focadas**
- **Máximo**: 50 linhas por função
- **Ideal**: 10-20 linhas
- **Uma responsabilidade** por função

---

## 🔧 Práticas de Desenvolvimento

### Git Workflow

**1. Branches**
```bash
# Padrão de nomenclatura
feat/nome-da-feature      # Nova funcionalidade
fix/nome-do-bug          # Correção de bug
refactor/nome-melhoria   # Refatoração
docs/nome-doc            # Documentação
test/nome-teste          # Adição de testes
chore/nome-tarefa        # Manutenção
```

**2. Commits Semânticos**
```bash
# Formato
<tipo>: <descrição curta>

[corpo opcional]

# Exemplos
feat: add BigQuery streaming to prevent OOM
fix: resolve mypy type error in run_batch
docs: update README with streaming features
test: add comprehensive streaming tests
chore: bump version to 0.8.0
```

**3. Pull Requests**
- ✅ Todos os testes passando
- ✅ Cobertura mantida ou aumentada
- ✅ Changelog atualizado
- ✅ Documentação atualizada
- ✅ Pre-commit hooks passando

### Testes

**1. Estrutura de Testes**
```
tests/
├── test_<module_name>.py           # Testes do módulo
├── test_<module_name>_bq.py        # Testes BigQuery
├── test_<module_name>_streaming.py # Testes streaming
└── fixtures/                        # Dados de teste
```

**2. Padrão de Nomenclatura**
```python
class TestBatchAnalyzer:
    def test_save_to_bigquery_chunked_writes(self):
        """Test that save_to_bigquery splits large batches into chunks."""
        ...
```

**3. Coverage Mínima**
- **Novos arquivos**: 80% de cobertura
- **Arquivos modificados**: Não diminuir cobertura
- **Funções críticas**: 100% de cobertura

---

## ⚡ Otimização de Performance

### Memória

**1. Streaming para Datasets Grandes**
```python
# ✅ Correto - Streaming (>1000 items)
chats = stream_chats_from_bigquery(days=30, page_size=1000)
for chat in chats:
    process(chat)

# ❌ Incorreto - Carrega tudo na memória
chats = load_chats_from_bigquery(days=30)  # Pode causar OOM
```

**2. Generators em Vez de Listas**
```python
# ✅ Correto - Memory efficient
def process_items(items: Iterator[Item]) -> Iterator[Result]:
    for item in items:
        yield process(item)

# ❌ Incorreto - Acumula tudo
def process_items(items: List[Item]) -> List[Result]:
    return [process(item) for item in items]
```

**3. Chunked Operations**
```python
# ✅ Correto - Processa em chunks
batch_analyzer.save_to_bigquery(results, chunk_size=500)

# ❌ Incorreto - Tudo de uma vez
batch_analyzer.save_to_bigquery(results)  # Pode exceder 10MB
```

### Database/BigQuery

**1. Filtrar no Banco, Não em Python**
```python
# ✅ Correto - Filtro na query
query = f"""
    SELECT * FROM table
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    LIMIT {limit}
"""

# ❌ Incorreto - Carrega tudo e filtra
all_data = query("SELECT * FROM table")
filtered = [d for d in all_data if d.date >= cutoff]
```

**2. Lightweight Mode Quando Possível**
```python
# ✅ Correto - Apenas campos necessários
chats = load_chats_from_bigquery(lightweight=True)  # Sem mensagens

# ❌ Incorreto - Carrega campos desnecessários
chats = load_chats_from_bigquery(lightweight=False)
```

### Cache

**1. Usar Redis Cache para LLM**
```python
# ✅ Correto - Cache habilitado
analyzer = BatchAnalyzer()  # Cache automático
result = await analyzer.analyze_chat(chat)  # Cacheia resultado

# ❌ Incorreto - Chamadas duplicadas
result1 = await gemini.analyze(chat)
result2 = await gemini.analyze(chat)  # Chamada LLM duplicada!
```

---

## 🤖 Trabalhando com AI Assistants

### Economia de Tokens

**1. Fornecer Contexto Específico**
```bash
# ✅ Correto - Específico
"Fix the mypy error in src/batch_analyzer.py line 219"

# ❌ Incorreto - Vago (requer análise de todo o código)
"Fix all errors in the project"
```

**2. Usar Ferramentas Certas**
```bash
# ✅ Correto - Search específico
grep_search("stream_chats_from_bigquery")

# ❌ Incorreto - View arquivo inteiro
view_file("src/ingestion.py")  # 500+ linhas
```

**3. Limitar Outputs de Comandos**
```bash
# ✅ Correto - Limita output
git log --oneline -10

# ❌ Incorreto - Output imenso
git log  # Todo o histórico
```

**4. Ser Incremental**
```bash
# ✅ Correto - Passo a passo
1. "Create streaming function"
2. "Add tests for streaming"
3. "Update documentation"

# ❌ Incorreto - Tudo de uma vez
"Implement complete streaming system with tests and docs"
```

### Estrutura de Solicitações

**Template Recomendado:**
```markdown
**Objetivo**: [O que fazer]
**Contexto**: [Por que fazer]
**Arquivos**: [Quais arquivos modificar]
**Testes**: [Como validar]
```

**Exemplo:**
```markdown
**Objetivo**: Adicionar paginação ao streaming do BigQuery
**Contexto**: Prevenir OOM em datasets >1000 chats
**Arquivos**: src/ingestion.py
**Testes**: Verificar que result() é chamado com page_size
```

### Boas Práticas com AI

**1. Revisar Antes de Commitar**
- ✅ Sempre rodar testes localmente
- ✅ Verificar mypy e ruff
- ✅ Ler o código gerado

**2. Validar Lógica de Negócio**
- ✅ AI pode errar em regras de negócio
- ✅ Conferir cálculos e algoritmos
- ✅ Testar casos extremos

**3. Documentar Decisões**
- ✅ Explicar "por quês" no código
- ✅ Adicionar comentários em lógica complexa
- ✅ Atualizar documentação

---

## ✅ Code Review Checklist

### Pre-Commit

```bash
□ Testes passando localmente
□ Cobertura mantida/aumentada
□ Mypy sem erros
□ Ruff sem warnings
□ Docstrings atualizadas
□ Type hints completos
□ Changelog atualizado (se aplicável)
```

### Code Quality

```bash
□ Nomes descritivos
□ Funções < 50 linhas
□ Complexidade ciclomática < 10
□ Sem código duplicado
□ Sem "magic numbers"
□ Tratamento de erros adequado
□ Logs apropriados
```

### Performance

```bash
□ Streaming para grandes datasets
□ Cache utilizado quando apropriado
□ Queries otimizadas
□ Sem N+1 queries
□ Memory leaks verificados
```

### Security & LGPD

```bash
□ Sem PII em logs
□ Anonimização aplicada
□ Credenciais não expostas
□ .gitignore atualizado
□ Validação de inputs
```

---

## 📚 Recursos

### Documentação Interna
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Guia para contribuidores
- [README.md](../README.md) - Visão geral do projeto
- [docs/changelog.md](changelog.md) - Histórico de mudanças
- [docs/algorithms_guide.md](algorithms_guide.md) - Guia interno de algoritmos

### Ferramentas
- **Testes**: pytest, pytest-cov, pytest-asyncio
- **Linting**: ruff
- **Type Checking**: mypy
- **Pre-commit**: pre-commit hooks configurados
- **CI/CD**: GitHub Actions

### Padrões Externos
- [PEP 8](https://pep8.org/) - Style Guide for Python Code
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

---

## 🎯 Princípios Fundamentais

1. **Qualidade > Velocidade**
   - Código bem testado e documentado

2. **Clareza > Cleverness**
   - Código legível e mantível

3. **Performance Importa**
   - Otimizar para escala desde o início

4. **LGPD First**
   - Privacidade de dados é prioridade

5. **Iterate & Improve**
   - Melhorias contínuas são bem-vindas

---

**Mantenha este documento atualizado à medida que o projeto evolui!**
