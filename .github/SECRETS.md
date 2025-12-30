# GitHub Actions - Secrets Configuration

This document lists all the secrets required for the GitHub Actions workflows to function properly.

## Required Secrets

Configure these in: **Settings > Secrets and variables > Actions > New repository secret**

### 1. Gemini API

**Name:** `GEMINI_API_KEY`
**Description:** API key for Google Gemini LLM
**Where to get:** https://makersuite.google.com/app/apikey
**Format:** String (e.g., `AIzaSy...`)

---

### 2. BigQuery / GCP

**Name:** `GCP_SA_KEY`
**Description:** Full JSON content of Google Cloud Service Account key
**Where to get:** GCP Console > IAM & Admin > Service Accounts > Create Key (JSON)
**Format:** Complete JSON (entire file content)

**Permissions required:**
- BigQuery Data Editor
- BigQuery Job User

**Name:** `BIGQUERY_PROJECT_ID`
**Description:** Your GCP Project ID
**Format:** String (e.g., `my-project-12345`)

**Name:** `BIGQUERY_DATASET_ID`
**Description:** BigQuery dataset name
**Format:** String (e.g., `octadesk`)

---

### 3. Redis Cache (Optional)

**Name:** `REDIS_URL`
**Description:** Redis connection URL for LLM caching
**Format:** `redis://hostname:port/db` or `redis://user:password@hostname:port/db`
**Example:** `redis://localhost:6379/0`

**Note:** If not provided, caching will be disabled (analysis still works).

---

### 4. Email Notifications

**Name:** `MAIL_USERNAME`
**Description:** Email address to send notifications FROM
**Format:** email@example.com

**Name:** `MAIL_PASSWORD`
**Description:** Email password or app-specific password
**Format:** String
**Note:** For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)

**Name:** `NOTIFICATION_EMAIL`
**Description:** Email address to send notifications TO
**Format:** email@example.com
**Note:** Can be the same as MAIL_USERNAME

---

## Optional Secrets

### Slack/Discord Webhooks

**Name:** `SLACK_WEBHOOK_URL`
**Description:** Slack incoming webhook URL (for future integration)
**Format:** https://hooks.slack.com/services/...

---

## Testing Secrets

After configuring secrets, test them with:

```bash
# Trigger manual workflow from GitHub UI
# Go to: Actions > Manual Chat Analysis > Run workflow

# Or via CLI:
gh workflow run manual_analysis.yml \
  -f max_chats=10 \
  -f save_to_bigquery=false
```

---

## Troubleshooting

### Secret not found error

```
Error: Secret GEMINI_API_KEY is not set
```

**Solution:** Verify the secret name matches exactly (case-sensitive)

### GCP authentication failed

```
Error: Could not authenticate with GCP
```

**Solution:**
1. Verify `GCP_SA_KEY` contains the FULL JSON (including `{ }`)
2. Check service account has required permissions
3. Ensure project ID is correct

### Email sending failed

```
Error: Authentication failed
```

**Solution:**
1. For Gmail, use an App Password, not your regular password
2. Enable "Less secure app access" (not recommended) OR use App Password
3. Verify SMTP settings (server, port)

---

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Rotate keys** periodically (every 90 days recommended)
3. **Use minimal permissions** for service accounts
4. **Monitor usage** via workflow logs
5. **Limit access** to repository secrets (Settings > Actions > General)

---

## Workflow Permissions

The workflows require the following GitHub token permissions:

```yaml
permissions:
  actions: read      # To check workflow status
  contents: read     # To checkout code
  id-token: write    # For OIDC (future)
```

These are set automatically by GitHub Actions.

---

*Last updated: 2024-12-30*
