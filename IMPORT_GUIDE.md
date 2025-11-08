# Secret Import Guide

## Important: How Secrets Work

**DO NOT put actual secret values in `secrets.yml`!**

- `secrets.yml` = Configuration schema (what secrets should exist)
- `.env.staging.secrets` = Actual secret values (NOT committed to git)
- Google Secret Manager = Where secrets are actually stored

## Step 1: Update secrets.yml with YOUR GCP Project ID

```bash
vim secrets.yml
```

Change line 6:
```yaml
gcp_project: your-gcp-project-id  # Replace with YOUR actual GCP project ID
```

## Step 2: Authenticate to GCP

```bash
gcloud auth application-default login
```

## Step 3: Import Secrets to GSM

```bash
# Preview what will be imported (dry run)
python import_secrets.py --dry-run

# Import for real
python import_secrets.py
```

This will:
- Read secrets from `.env.staging.secrets`
- Skip placeholders automatically
- Import each secret to Google Secret Manager
- Create secrets with naming: `botmaro-staging--SECRET_NAME`

## Step 4: Verify

```bash
# List all secrets
secrets-manager list staging

# List with values (be careful!)
secrets-manager list staging --reveal

# List only environment-level secrets
secrets-manager list staging --scope env
```

## File Structure

```
.env.staging.secrets  ← Your actual secret values (gitignored)
secrets.yml           ← Configuration schema (gitignored)
secrets.example.yml   ← Example schema (committed to git)
import_secrets.py     ← Import script (gitignored)
```

## Troubleshooting

### Error: "Environment 'staging' not found"
- Make sure you updated `gcp_project` in secrets.yml

### Error: "Permission denied"
- Run: `gcloud auth application-default login`
- Ensure your GCP account has `secretmanager.admin` role

### Secrets not showing up
- Check the prefix matches: `botmaro-staging--`
- Verify GCP project ID is correct in secrets.yml