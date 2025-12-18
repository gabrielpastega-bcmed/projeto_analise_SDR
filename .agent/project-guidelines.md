# AI Assistant Guidelines - Projeto Análise SDR

> **Para**: AI Assistants trabalhando neste projeto
> **Versão**: 1.0
> **Auto-carregado**: ✅ Lido automaticamente pelo workflow

---

## 🎯 Padrões de Qualidade Obrigatórios

### Métricas Mínimas
- **Testes**: ≥75% cobertura, 100% passando
- **Type Hints**: Obrigatório em todas as funções públicas
- **Lint**: 0 warnings (ruff + mypy)
- **Docstrings**: Obrigatório (Google Style)

### Code Standards
```python
# ✅ SEMPRE use type hints
def analyze_chat(chat: Chat, validate: bool = True) -> Dict[str, Any]:
    """Google-style docstring obrigatória."""
    ...

# ✅ Funções pequenas (máx 50 linhas)
# ✅ Nomes descritivos (não abreviar)
# ✅ Uma responsabilidade por função
```

---

## 🔧 Git Workflow - SEGUIR SEMPRE

### Branches
```bash
feat/nome-feature    # Nova funcionalidade
fix/nome-bug        # Correção
refactor/nome       # Refatoração
docs/nome           # Documentação
test/nome           # Testes
chore/nome          # Manutenção
```

### Commits Semânticos
```bash
feat: add streaming to prevent OOM
fix: resolve mypy type error
docs: update README with examples
test: add streaming tests
chore: bump version to 0.8.0
```

### Pre-Push Checklist
- [ ] Todos os testes passando
- [ ] Mypy sem erros
- [ ] Ruff sem warnings
- [ ] Docstrings atualizadas
- [ ] Changelog atualizado (se features/fixes)

---

## ⚡ Performance - SEMPRE OTIMIZAR

### Memória
```python
# ✅ USAR: Streaming para >1000 items
chats = stream_chats_from_bigquery(days=30, page_size=1000)

# ❌ EVITAR: Carregar tudo na memória
chats = load_chats_from_bigquery(days=30)  # OOM risk!
```

### BigQuery
```python
# ✅ USAR: Lightweight mode quando possível
load_chats_from_bigquery(lightweight=True)

# ✅ USAR: Chunked writes
save_to_bigquery(results, chunk_size=500)

# ❌ EVITAR: Queries sem filtros
# ❌ EVITAR: Carregar campos desnecessários
```

### Cache
```python
# ✅ SEMPRE: Use Redis cache para LLM responses
analyzer = BatchAnalyzer()  # Cache automático habilitado
```

---

## 🤖 Economia de Tokens - CRÍTICO

### 1. Contexto Específico
```bash
# ✅ BOM: "Fix mypy error in batch_analyzer.py line 219"
# ❌ RUIM: "Fix all errors" (requer análise completa)
```

### 2. Ferramentas Certas
```bash
# ✅ USAR: grep_search, search_in_file (baixo custo)
# ❌ EVITAR: view_file em arquivos grandes (alto custo)

# ✅ LIMITAR: Outputs de comandos
git log --oneline -10  # Bom
git log               # Ruim (muito output)
```

### 3. Abordagem Incremental
```bash
# ✅ BOM: Dividir em pequenas tarefas
1. Implementar função
2. Adicionar testes
3. Atualizar docs

# ❌ RUIM: "Implementar tudo de uma vez"
```

### 4. Evitar Redundância
- Não re-visualizar arquivos já vistos
- Cachear informações importantes
- Usar `%SAME%` em task_boundary quando aplicável

---

## 📋 Workflow de Desenvolvimento

### 1. Planning (SEMPRE)
- Criar `implementation_plan.md`
- Pedir aprovação do usuário
- Só então implementar

### 2. Implementation
- Feature branch obrigatória
- Commits pequenos e frequentes
- Testes junto com código

### 3. Testing
- Rodar testes após cada mudança
- Verificar cobertura não diminuiu
- Validar mypy + ruff

### 4. Documentation
- Atualizar README se necessário
- Adicionar entry no changelog
- Docstrings completas

### 5. Verification
- Criar `walkthrough.md` mostrando resultados
- Screenshots/evidências quando aplicável
- Validar com usuário

---

## 🚫 Anti-Patterns - EVITAR

### Código
```python
# ❌ Funções sem type hints
# ❌ Funções > 50 linhas
# ❌ Magic numbers sem constantes
# ❌ Código duplicado
# ❌ Nomes vagos (data, temp, aux)
```

### Git
```bash
# ❌ Commits direto na main
# ❌ Commits sem mensagem descritiva
# ❌ PRs sem testes
# ❌ Quebrar CI/CD
```

### Performance
```python
# ❌ N+1 queries
# ❌ Carregar datasets completos
# ❌ Não usar cache quando disponível
# ❌ Loops desnecessários
```

### Tokens
```bash
# ❌ View_file de arquivos >500 linhas sem necessidade
# ❌ Revisitar mesmos arquivos repetidamente
# ❌ Outputs ilimitados de comandos
# ❌ Análises completas quando bastava busca
```

---

## ✅ Checklist de Qualidade

Antes de cada commit:
```bash
□ Type hints completos
□ Docstrings (Google Style)
□ Testes passando (pytest)
□ Cobertura ≥75%
□ Mypy sem erros
□ Ruff sem warnings
□ Performance otimizada
□ LGPD/PII verificado
□ Documentação atualizada
□ Changelog atualizado (se aplicável)
```

---

## 🎯 Princípios Fundamentais

1. **Qualidade > Velocidade**
2. **Type Safety First** (mypy strict)
3. **Test Everything** (≥75% coverage)
4. **Optimize Early** (streaming, cache, chunks)
5. **Document Why, Not What**
6. **LGPD Compliance** (anonimizar PII)
7. **Token Economy** (otimizar uso de contexto)

---

## 📊 Performance Tips

### BigQuery Queries
- Sempre filtrar por data
- Usar LIMIT quando possível
- Lightweight mode por padrão
- Paginação com page_size=1000

### Memória
- Streaming para >1000 items
- Chunked writes (500 linhas)
- Generators em vez de listas
- Liberar recursos grandes após uso

### Cache
- Redis para LLM responses (automático)
- Cache de queries frequentes
- TTL de 7 dias (padrão)

---

## 🔍 Debug & Troubleshooting

### Testes Falhando
1. Rodar localmente primeiro
2. Verificar mocks corretos
3. Conferir fixtures
4. Validar tipos

### CI/CD Falhando
1. Verificar poetry.lock atualizado
2. Conferir mypy erros
3. Validar ruff formatting
4. Checar dependências

### Performance Issues
1. Usar streaming
2. Habilitar cache
3. Otimizar queries
4. Verificar chunks

---

## 📚 Recursos Rápidos

**Documentação:**
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Guia completo
- [docs/project-guidelines.md](../docs/project-guidelines.md) - Guidelines internas
- [docs/changelog.md](../docs/changelog.md) - Histórico

**Comandos Úteis:**
```bash
# Testes
poetry run pytest --cov=src --cov-report=term-missing

# Lint
poetry run ruff check .
poetry run mypy .

# Format
poetry run ruff format .
```

---

**LEMBRETE**: Este projeto preza por qualidade, otimização e economia de tokens. Sempre seguir estas diretrizes!
