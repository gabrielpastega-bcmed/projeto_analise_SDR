# ADR-001: PostgreSQL para Autenticação

**Status:** Aceita
**Data:** 2024-12-18
**Decisores:** Tech Lead, Backend Team
**Tags:** database, authentication, security

---

## Contexto

O sistema SDR Analytics Dashboard precisa de um mecanismo de autenticação robusto para controlar acesso às dashboards e dados sensíveis. Inicialmente, o projeto não tinha autenticação.

### Requisitos

- Múltiplos usuários com diferentes níveis de acesso
- Suporte para OAuth (Google)
- Auditoria de ações (compliance)
- Session management
- Escalabilidade para 100+ usuários

---

## Decisão

**Escolhemos PostgreSQL como banco de dados para o módulo de autenticação.**

### Alternativas Consideradas

#### 1. ✅ **PostgreSQL** (Escolhida)

**Prós:**
- ACID compliant (transações seguras)
- Mature e battle-tested
- Suporte nativo para JSON (user preferences)
- Excelente performance para reads (sessões)
- Ecosystem rico (pgBouncer, replicação)
- Hospedagem fácil (Railway, Supabase, RDS)

**Contras:**
- Custo de infraestrutura (vs SQLite)
- Requer manutenção (backups, vacuums)

#### 2. ❌ SQLite

**Prós:**
- Zero configuração
- Sem custos de infraestrutura
- Bom para desenvolvimento local

**Contras:**
- Não suporta concorrência (write locks)
- Difícil de escalar horizontalmente
- Backup mais complexo em produção
- Sem suporte a múltiplas conexões simultâneas

#### 3. ❌ MongoDB

**Prós:**
- Schema flexível
- Bom para dados não estruturados

**Contras:**
- Sem ACID (até recentemente)
- Overkill para dados tabulares simples (users, sessions)
- Team sem experiência
- Mais complexo para joins (audit logs)

#### 4. ❌ Firebase Auth

**Prós:**
- Managed service
- OAuth integrado
- Escalabilidade automática

**Contras:**
- Vendor lock-in (Google)
- Custo imprevisível
- Difícil de auditar (logs próprios)
- Migração complexa

---

## Justificativa

### Por que PostgreSQL?

1. **ACID Compliance**: Crítico para dados de auth
   - Exemplo: User cria conta → Session inicia → Audit log
   - Deve ser atômico (tudo ou nada)

2. **Auditoria**: Fácil fazer queries em `audit_log`
   ```sql
   SELECT * FROM audit_log
   WHERE user_id = 123
   AND action = 'login'
   ORDER BY timestamp DESC;
   ```

3. **Session Management**: Alta frequência de reads
   - PostgreSQL: 10k+ reads/s com índices
   - SQLite: Bloqueia em 100+ concurrent users

4. **Hospedagem**: Railway oferece PostgreSQL free tier
   - 0.5 GB storage, suficiente para 1000+ users
   - Backups automáticos

5. **Team Familiarity**: Equipe já usa BigQuery (SQL)

---

## Consequências

### Positivas

✅ **Escalabilidade**: Suporta crescimento para 10k+ users
✅ **Confiabilidade**: ACID garante consistência
✅ **Auditoria**: Queries complexas facilitadas
✅ **Ecosystem**: pgBouncer, replicação, monitoring
✅ **Development**: Mesma stack SQL (BigQuery + PostgreSQL)

### Negativas

⚠️ **Custo**: ~$7/mês em produção (Railway/Supabase)
⚠️ **Operação**: Requer backups, vacuums, monitoring
⚠️ **Setup**: Mais complexo que SQLite para dev local

### Mitigações

- **Custo**: Free tier suficiente inicialmente
- **Operação**: Railway faz backups automáticos
- **Setup**: Docker Compose para dev local

---

## Implementação

```python
# src/auth/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:pass@host:5432/db"

engine = create_engine(DATABASE_URL, pool_size=20)
SessionLocal = sessionmaker(bind=engine)
```

### Modelos

- `users`: id, username, email, password_hash, role
- `sessions`: id, user_id, token, expires_at
- `audit_log`: id, user_id, action, timestamp, metadata
- `user_preferences`: user_id, theme, filters (JSONB)

---

## Lições Aprendidas

1. **Índices são críticos**: Sem índice em `users.email`, login demora 500ms
2. **Connection pooling**: PgBouncer reduziu latência em 40%
3. **JSONB é poderoso**: User preferences como JSONB simplificou schema

---

## Revisões

| Data | Decisor | Mudança |
|------|---------|---------|
| 2024-12-18 | Tech Lead | Decisão inicial |
| 2024-12-20 | Backend | Adicionado JSONB para preferences |

---

*Referências:*
- [PostgreSQL vs MongoDB](https://www.postgresql.org/about/featurematrix/)
- [Railway PostgreSQL](https://railway.app/postgresql)
- [SQLAlchemy Best Practices](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
