# Security Policy

## 🔒 Segurança do Projeto SDR Analytics

### Reporting Security Vulnerabilities

Se você descobrir uma vulnerabilidade de segurança, **NÃO abra uma issue pública**.

**Contato:**
- Email: [SEU_EMAIL_SECURITY_AQUI]
- Tempo de resposta: 48 horas

---

## ❌ Nunca Commitar

Os seguintes tipos de informação **NUNCA** devem ser commitados no repositório:

### Credenciais e Secrets
- ❌ API Keys (Gemini, Sentry, etc)
- ❌ Senhas de banco de dados
- ❌ Tokens de autenticação
- ❌ Chaves privadas (`.pem`, `.key`)
- ❌ OAuth secrets
- ❌ Cookies de sessão

### Informações de Infraestrutura
- ❌ URLs de produção
- ❌ IPs de servidores
- ❌ Nomes de domínio internos
- ❌ Configurações de firewall

### Dados Sensíveis
- ❌ Dados de clientes ou usuários
- ❌ Conversas/chats reais
- ❌ Métricas de negócio proprietárias
- ❌ Backups de banco de dados (`.sql`, `.dump`)

### Arquivos de Configuração Local
- ❌ `.env` (use `.env.example` como template)
- ❌ IDE configs pessoais (`.vscode/settings.json`)
- ❌ Logs com potencial de dados sensíveis

---

## ✅ Seguro para Compartilhar

As seguintes informações são **seguras** para incluir no repositório:

### Documentação Técnica
- ✅ Decisões arquiteturais (ADRs)
- ✅ Diagramas genéricos de arquitetura
- ✅ Escolhas de tecnologia (PostgreSQL, Streamlit)

### Código
- ✅ Código-fonte da aplicação (sem secrets)
- ✅ Testes unitários
- ✅ Schemas de banco de dados (sem dados)

### Configuração
- ✅ `.env.example` (com placeholders)
- ✅ Docker configuration
- ✅ CI/CD pipelines (sem secrets inline)

### Documentação Pública
- ✅ README.md
- ✅ Guias de instalação
- ✅ API documentation (pública)

---

## 🛡️ Práticas de Segurança

### Para Desenvolvedores

1. **Sempre use `.env` para secrets**
   ```bash
   # ❌ ERRADO
   GEMINI_API_KEY = "AIza..." # Hard-coded

   # ✅ CORRETO
   GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
   ```

2. **Verifique antes de commitar**
   ```bash
   # Rode antes de cada commit
   git diff --cached | grep -E "(password|secret|key|token)"
   ```

3. **Use .gitignore rigorosamente**
   - Nunca force add (`git add -f`) de arquivos ignorados
   - Revise `.gitignore` periodicamente

4. **Rotacione credenciais se expostas**
   - Se acidentalmente commitou um secret:
     1. Revoke/regenerate a credencial IMEDIATAMENTE
     2. Limpe o histórico do Git (`git filter-branch`)
     3. Force push (cuidado!)
     4. Notifique o time

### Para Operações

5. **Backups seguros**
   - Criptografar backups de DB
   - Armazenar em S3 privado (não público)
   - Rotação automática (manter últimos 30 dias)

6. **Logs**
   - Redact senhas de logs automaticamente
   - Não logar payloads completos de API
   - Rotate logs diariamente

7. **Acesso**
   - Princípio do menor privilégio
   - MFA obrigatório para produção
   - Audit trail de acessos

---

## 📋 Security Checklist

Antes de cada release, verificar:

- [ ] Nenhum secret hard-coded no código
- [ ] `.env.example` atualizado (sem valores reais)
- [ ] Dependências atualizadas (`poetry update`)
- [ ] Security scan rodado (`safety check`)
- [ ] Logs não expõem dados sensíveis
- [ ] Rate limiting ativado em produção
- [ ] HTTPS enforced
- [ ] Database backups funcionando
- [ ] Sentry configurado (sem PII)

---

## 🚨 Em Caso de Incidente

### Vazamento de Secret Detectado

1. **IMEDIATO** (< 5 min):
   - Revocar/regenerar a credencial exposta
   - Notificar tech lead e security team

2. **CURTO PRAZO** (< 1 hora):
   - Auditar logs para uso não autorizado
   - Limpar histórico Git se necessário
   - Atualizar `.env` em todos os ambientes

3. **LONGO PRAZO** (< 1 semana):
   - Post-mortem: Como aconteceu?
   - Melhorar processos para prevenir
   - Treinar time se necessário

### Vulnerabilidade Descoberta

1. Avaliar severidade (CVSS score)
2. Se crítico: Patch imediato + deploy
3. Se menor: Agendar para próximo sprint
4. Documentar no CHANGELOG

---

## 🔗 Recursos Úteis

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Git Secret Management](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Sentry Security](https://docs.sentry.io/security-legal-pii/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

## 📝 Histórico de Alterações

| Data | Mudança |
|------|---------|
| 2024-12-29 | Criação inicial da política |

---

*Última atualização: 2024-12-29*
*Versão: 1.0*
