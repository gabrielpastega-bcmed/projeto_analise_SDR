# Runbook: Troubleshooting

> ⚠️ **CONFIDENCIAL - USO INTERNO APENAS**
>
> Este documento contém procedimentos de diagnóstico e comandos de sistema.
> **Não compartilhar publicamente.** Senhas e credenciais reais nunca devem ser documentadas aqui.

## Problemas Comuns e Soluções

---

## 🔴 Login Não Funciona

### Sintomas
- Usuário não consegue fazer login
- Mensagem "Credenciais inválidas" mesmo com senha correta
- Google OAuth não redireciona

### Diagnóstico

```bash
# 1. Verificar PostgreSQL
curl http://localhost:8501/health
# Observar status do "postgres"

# 2. Verificar logs
tail -f logs/app.log | grep "login"

# 3. Testar conexão direta
psql -h $AUTH_DATABASE_HOST -U $AUTH_DATABASE_USER -d $AUTH_DATABASE_NAME
```

### Causas Comuns

| Causa | Solução |
|-------|---------|
| PostgreSQL down | Reiniciar: `sudo systemctl restart postgresql` |
| Credenciais erradas em `.env` | Verificar `AUTH_DATABASE_*` vars |
| Senha hash inválido | Resetar senha via admin panel |
| OAuth mal configurado | Verificar `GOOGLE_OAUTH_*` vars |

### Solução Rápida

```bash
# Reset de senha via Python
poetry run python
>>> from src.auth.models import User
>>> from src.auth.database import SessionLocal
>>> db = SessionLocal()
>>> user = db.query(User).filter(User.username == "admin").first()
>>> user.set_password("nova_senha_123")
>>> db.commit()
```

---

## ⚠️ Dashboard Lento

### Sintomas
- Páginas demoram > 10s para carregar
- Gráficos não aparecem
- Timeout em queries

### Diagnóstico

```bash
# 1. Verificar uso de CPU/memória
top
# Procurar processo python

# 2. Verificar queries lentas no PostgreSQL
psql -U postgres -d sdr_analytics
SELECT * FROM pg_stat_activity WHERE state = 'active';

# 3. Verificar cache
# Abrir Streamlit, ver console do browser
# Procurar por "Using cached data"
```

### Causas Comuns

| Causa | Solução |
|-------|---------|
| BigQuery query pesada | Adicionar filtro de data |
| Cache desabilitado | Verificar `@st.cache_data` |
| Muitos chats carregados | Limitar a 1000 registros |
| Índices faltando | Criar índices (ver abaixo) |

### Solução: Adicionar Índices

```sql
-- PostgreSQL (auth)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status, created_at);

-- Se usar PostgreSQL para dados de chats
CREATE INDEX IF NOT EXISTS idx_chats_timestamp ON chats(timestamp);
CREATE INDEX IF NOT EXISTS idx_chats_agent ON chats(agent_name);
```

---

## 🔵 Alertas Não Disparando

### Sintomas
- TME alto mas sem alerta
- Badge de alertas sempre em 0
- Página de alertas vazia

### Diagnóstico

```bash
# 1. Verificar se tabelas existem
psql -U postgres -d sdr_analytics
\dt alerts*

# 2. Testar serviço manualmente
poetry run python
>>> from src.auth.alert_service import AlertService
>>> alert = AlertService.check_tme_threshold(current_tme=20.0)
>>> print(alert)

# 3. Verificar thresholds
>>> threshold = AlertService.get_threshold("tme_high")
>>> print(threshold)  # Esperado: 15.0
```

### Causas Comuns

| Causa | Solução |
|-------|---------|
| Tabelas não criadas | Rodar migrations: `alembic upgrade head` |
| Thresholds muito altos | Ajustar na página de Alertas |
| Alertas já reconhecidos | Verificar histórico |

---

## 🟡 Exportação Excel Falha

### Sintomas
- Botão "Exportar Excel" não funciona
- Download fica carregando infinito
- Erro "Memory Error"

### Diagnóstico

```bash
# 1. Verificar dependências
poetry show openpyxl
# Deve estar instalado

# 2. Testar manualmente
poetry run python
>>> from src.excel_export import create_chat_export
>>> chats = []  # Lista vazia para teste
>>> buffer = create_chat_export(chats)
>>> print(len(buffer.getvalue()))  # Deve retornar > 0

# 3. Verificar memória disponível
free -h
```

### Causas Comuns

| Causa | Solução |
|-------|---------|
| openpyxl não instalado | `poetry add openpyxl` |
| Muitos dados (>10k chats) | Adicionar paginação/filtros |
| Memória insuficiente | Aumentar RAM ou limitar export |

---

## 🟢 Sentry Não Capturando Erros

### Sintomas
- Nenhum erro aparece no Sentry
- Dashboard do Sentry em branco

### Diagnóstico

```bash
# 1. Verificar DSN configurado
echo $SENTRY_DSN
# Deve retornar algo como: https://...@sentry.io/...

# 2. Testar captura manual
poetry run python
>>> from src.observability import capture_exception
>>> try:
>>>     raise ValueError("Teste Sentry")
>>> except Exception as e:
>>>     capture_exception(e)
# Verificar no Sentry se erro apareceu

# 3. Verificar inicialização
tail -f logs/app.log | grep -i sentry
```

### Causas Comuns

| Causa | Solução |
|-------|---------|
| SENTRY_DSN vazio | Adicionar DSN no `.env` |
| Ambiente não configurado | Verificar `SENTRY_ENVIRONMENT` |
| Firewall bloqueando | Liberar saída HTTPS para sentry.io |

---

## 📊 BigQuery Timeout

### Sintomas
- Erro "Query timeout"
- Insights page não carrega
- Mensagem de API limit excedido

### Diagnóstico

```bash
# 1. Verificar credenciais
echo $GOOGLE_APPLICATION_CREDENTIALS
cat $GOOGLE_APPLICATION_CREDENTIALS
# Deve ser um JSON válido

# 2. Testar query simples
poetry run python
>>> from google.cloud import bigquery
>>> client = bigquery.Client()
>>> query = "SELECT 1"
>>> client.query(query).result()
```

### Causas Comuns

| Causa | Solução |
|-------|---------|
| Credenciais expiradas | Gerar nova service account key |
| Quota excedida | Aguardar reset ou aumentar quota |
| Query muito complexa | Simplificar ou adicionar LIMIT |
| Projeto/dataset errado | Verificar `BIGQUERY_*` vars |

---

## 🔧 Logs Úteis

```bash
# Todos os erros das últimas 24h
journalctl -u sdr-analytics --since "24 hours ago" | grep ERROR

# Logins bem-sucedidos
tail -f logs/app.log | grep "Login successful"

# Queries lentas (> 1s)
tail -f logs/app.log | grep "slow query"

# Health checks
watch -n 5 'curl -s http://localhost:8501/health | jq'
```

---

## 🆘 Escalação

| Severidade | Tempo de Resposta | Contato |
|------------|-------------------|---------|
| **CRÍTICO** (sistema down) | Imediato | Tech Lead + DevOps |
| **ALTO** (feature quebrada) | 1 hora | Tech Lead |
| **MÉDIO** (lentidão) | 4 horas | Equipe de dev |
| **BAIXO** (bug menor) | 1 dia | Criar issue no GitHub |

---

*Última atualização: 2024-12-29*
