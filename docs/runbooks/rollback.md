# Runbook: Rollback de Deploy

> ⚠️ **CONFIDENCIAL - USO INTERNO APENAS**
>
> Este documento contém procedimentos operacionais internos.
> **Não compartilhar publicamente ou fora da organização.**
> Credenciais e URLs de produção devem estar APENAS no `.env` (nunca em git ou documentação).

## Visão Geral
Procedimento para reverter um deploy com problemas em produção.

---

## Quando Usar

Execute este runbook se:
- ✅ Deploy causou erros críticos
- ✅ Funcionalidade principal quebrada
- ✅ Usuários reportando problemas
- ✅ Sentry mostrando spike de erros

**NÃO** execute se:
- ❌ Apenas um bug menor
- ❌ Afeta < 5% dos usuários
- ❌ Pode ser corrigido com hotfix rápido

---

## Pré-requisitos

- Acesso SSH ao servidor (ou painel de controle)
- Git local com branch atualizada
- Backup recente do banco de dados
- 15 minutos de janela de manutenção

---

## Procedimento de Rollback

### 1. Confirmar Necessidade

```bash
# Verificar health check
curl https://seu-dominio.com/health

# Verificar Sentry
# Abrir: https://sentry.io/organizations/your-org/issues/
# Procurar por erros recentes
```

**Decisão:** Se > 10 erros/min, prosseguir com rollback.

---

### 2. Comunicar Stakeholders

```markdown
🚨 ALERTA DE ROLLBACK

Status: Iniciando rollback do deploy X.Y.Z
Motivo: [Descrever problema]
ETA: 15 minutos
Ação: Sistema em manutenção
```

Enviar para:
- Canal #tech no Slack
- Email: equipe@empresa.com

---

### 3. Git Rollback

```bash
# Identificar commit antes do problema
git log --oneline -10

# Fazer rollback
git revert <commit-hash-problemático> --no-edit

# OU, se múltiplos commits:
git reset --hard <commit-hash-bom>
git push origin main --force-with-lease
```

⚠️ **CUIDADO:** `--force` reescreve histórico!

---

### 4. Deploy da Versão Anterior

**Opção A: Plataforma Cloud (Heroku/Railway)**
```bash
# Usar interface web
# Dashboard > Deployments > Rollback to <hash>
```

**Opção B: Docker**
```bash
# Fazer build da versão anterior
git checkout <commit-hash-bom>
docker build -t sdr-analytics:rollback .
docker stop sdr-analytics
docker run -d --name sdr-analytics sdr-analytics:rollback
```

**Opção C: Streamlit Cloud**
```bash
# Push no branch main vai triggerar redeploy automático
git push origin main --force-with-lease
```

---

### 5. Verificar Database Migrations

```bash
# Se o deploy incluiu migrations, reverter:
cd projeto_analise_SDR

# Alembic (se usando)
poetry run alembic downgrade -1

# OU manual
psql -U postgres -d sdr_analytics < backup/rollback_migration.sql
```

⚠️ **Atenção:** Migrations de dados são irreversíveis!

---

### 6. Smoke Tests

```bash
# 1. Health check
curl https://seu-dominio.com/health
# Esperado: {"status": "healthy"}

# 2. Login
# Abrir: https://seu-dominio.com
# Fazer login manual

# 3. Dashboard principal
# Verificar carregamento de dados

# 4. Sentry
# Confirmar que erros pararam
```

---

### 7. Monitorar por 30 min

```bash
# Abrir Sentry
# Filtrar por "Last 30 minutes"

# Verificar logs
tail -f /var/log/sdr-analytics/app.log

# Verificar métricas
# Abrir Grafana/DataDog (se configurado)
```

---

### 8. Comunicar Resolução

```markdown
✅ ROLLBACK COMPLETO

Status: Sistema restaurado
Versão: X.Y.Z → X.Y.(Z-1)
Uptime: 100% desde rollback
Próximos passos:
- Investigar causa raiz
- Fix em branch separada
- Code review extra
```

---

## Post-Mortem (24h depois)

### Criar Incident Report

```markdown
## Incident Report - YYYY-MM-DD

**Duração:** [início] → [fim]
**Impacto:** [X usuários afetados, Y downtime]
**Causa Raiz:** [Descrição técnica]

**Timeline:**
- 10:00 - Deploy da versão X.Y.Z
- 10:15 - Primeiros erros no Sentry
- 10:20 - Decisão de rollback
- 10:35 - Rollback completo
- 10:50 - Verificação OK

**Lições Aprendidas:**
1. [O que funcionou bem]
2. [O que pode melhorar]

**Action Items:**
- [ ] Adicionar teste de integração para caso X
- [ ] Melhorar staging environment
- [ ] Code review extra para mudanças em Y
```

---

## Prevenção Futura

- ✅ **Staging obrigatório**: Todo deploy passa por staging primeiro
- ✅ **Smoke tests**: Automáticos pós-deploy
- ✅ **Gradual rollout**: Deploy para 10% → 50% → 100%
- ✅ **Feature flags**: Desabilitar features sem redeploy

---

## Contatos de Emergência

| Pessoa | Role | Contato |
|--------|------|---------|
| [Nome] | Tech Lead | +55 11 99999-9999 |
| [Nome] | DevOps | devops@empresa.com |
| [Nome] | DBA | +55 11 88888-8888 |

---

*Última atualização: 2024-12-29*
