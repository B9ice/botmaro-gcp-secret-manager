# Botmaro Secrets Manager - Setup Guide

## Prerequisites

1. **Google Cloud Project** - You need at least one GCP project
2. **Google Cloud SDK** - Install `gcloud` CLI
3. **Python 3.8+** - Required for running the tool
4. **Permissions** - Service account with Secret Manager permissions

## Step-by-Step Setup

### 1. Install the Package

```bash
# Development install (from source)
cd /path/to/botmaro-gcp-secret-manager
pip install -e .

# Verify installation
secrets-manager version
```

### 2. Configure Google Cloud

```bash
# Authenticate
gcloud auth application-default login

# Set default project
gcloud config set project YOUR_PROJECT_ID

# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com
```

### 3. Create Configuration File

Copy the example configuration:

```bash
cp secrets.example.yml secrets.yml
```

Edit `secrets.yml` to match your setup:

```yaml
version: "1.0"

environments:
  staging:
    name: staging
    gcp_project: your-staging-project-id
    global_secrets:
      - name: SUPABASE_URL
        required: true
      # Add more secrets as needed
```

### 4. Create Service Accounts

For GitHub Actions deployment, create service accounts:

```bash
# Create deployer service account
gcloud iam service-accounts create gh-actions-deployer-staging \
  --display-name="GitHub Actions Deployer (Staging)" \
  --project=your-staging-project-id

# Create runtime service account
gcloud iam service-accounts create botmaro-runner \
  --display-name="Botmaro Runtime Service Account" \
  --project=your-staging-project-id

# Grant Secret Manager Admin to deployer (for managing secrets)
gcloud projects add-iam-policy-binding your-staging-project-id \
  --member="serviceAccount:gh-actions-deployer-staging@your-staging-project-id.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"

# Runtime SA will get accessor role automatically via the tool
```

### 5. Initialize Secrets

Set your initial secrets (they'll be stored with `--` separators in GSM):

```bash
# Set Supabase secrets
secrets-manager set staging.SUPABASE_URL \
  --value "https://xxxxx.supabase.co"

secrets-manager set staging.SUPABASE_ANON_KEY \
  --value "eyJxxxxx..."

secrets-manager set staging.SUPABASE_SERVICE_ROLE_KEY \
  --value "eyJxxxxx..."

# Grant access to runtime service account
secrets-manager set staging.SUPABASE_URL \
  --value "https://xxxxx.supabase.co" \
  --grant botmaro-runner@your-project.iam.gserviceaccount.com

# Verify
secrets-manager list staging --reveal
```

### 6. Test Bootstrap

```bash
# Bootstrap and export to environment
secrets-manager bootstrap staging --verbose

# Save to .env file
secrets-manager bootstrap staging --output .env.staging

# Source the .env file
source .env.staging

# Verify variables are set
echo $SUPABASE_URL
```

### 7. Setup GitHub Actions

Add secrets to your GitHub repository:

```bash
# For Workload Identity (recommended)
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER
gh secret set GCP_SA_EMAIL

# OR for service account key (less secure)
# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=gh-actions-deployer-staging@your-project.iam.gserviceaccount.com

# Add to GitHub (then delete local copy)
gh secret set GCP_SA_KEY < key.json
rm key.json
```

Create workflow file:

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [staging]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install secrets manager
        run: pip install -e .

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Bootstrap secrets
        run: |
          secrets-manager bootstrap staging \
            --runtime-sa botmaro-runner@your-project.iam.gserviceaccount.com

      - name: Deploy
        run: ./scripts/deploy.sh
```

### 8. Local Development

For local development, use the `dev` environment:

```bash
# Create dev config with defaults
cat >> secrets.yml <<EOF
  dev:
    name: dev
    gcp_project: your-dev-project-id
    global_secrets:
      - name: SUPABASE_URL
        required: false
        default: "http://localhost:54321"
EOF

# Bootstrap dev environment
secrets-manager bootstrap dev
```

## Common Commands

```bash
# Set a secret
secrets-manager set staging.API_KEY --value "xxx"

# Get a secret
secrets-manager get staging.API_KEY --reveal

# List all secrets
secrets-manager list staging

# Delete a secret
secrets-manager delete staging.OLD_KEY --force

# Bootstrap with service account grants
secrets-manager bootstrap staging \
  --runtime-sa bot@project.iam.gserviceaccount.com \
  --deployer-sa deploy@project.iam.gserviceaccount.com
```

## Troubleshooting

### "Permission denied" errors

Grant required roles:

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:YOUR_SA@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"
```

### "Secret not found"

Check the secret exists in GSM:

```bash
gcloud secrets list --project PROJECT_ID | grep botmaro
```

Check your config file environment names match.

### Authentication issues

Re-authenticate:

```bash
gcloud auth application-default login
gcloud auth list  # Verify correct account is active
```

## Security Best Practices

1. **Never commit secrets.yml with actual values** - Use placeholders only
2. **Use Workload Identity** for GitHub Actions instead of service account keys
3. **Rotate secrets regularly** using versioning
4. **Grant minimal permissions** - Runtime SAs only need `secretAccessor`
5. **Audit access** - Review IAM policies periodically

```bash
# Review who has access to a secret
gcloud secrets get-iam-policy SECRET_NAME --project PROJECT_ID
```

## Next Steps

- Set up secrets for production environment
- Configure project-specific secrets
- Integrate with your deployment pipeline
- Set up secret rotation policies

## Support

If you encounter issues:
1. Check the [README](README.md)
2. Review [example configs](secrets.example.yml)
3. Open an issue on GitHub