# GitHub Actions Integration Guide

This guide explains how to integrate Botmaro Secrets Manager with GitHub Actions to automatically load secrets from GCP Secret Manager into your CI/CD workflows.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
  - [1. Configure Workload Identity Federation](#1-configure-workload-identity-federation)
  - [2. Create Service Account](#2-create-service-account)
  - [3. Grant Secret Access](#3-grant-secret-access)
  - [4. Configure secrets.yml](#4-configure-secretsyml)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [With Project Scope](#with-project-scope)
  - [Multiple Environments](#multiple-environments)
  - [Manual Export](#manual-export)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)
- [Advanced Patterns](#advanced-patterns)

## Overview

The GitHub Actions integration allows you to:

- ✅ Load secrets from GCP Secret Manager automatically
- ✅ Use Workload Identity Federation (no long-lived keys)
- ✅ Validate secrets before deployment
- ✅ Export secrets in multiple formats
- ✅ Mask secrets in logs automatically
- ✅ Support multiple environments and projects

## Prerequisites

Before you begin, ensure you have:

1. A GCP project with Secret Manager API enabled
2. Secrets stored in GCP Secret Manager
3. A `secrets.yml` configuration file in your repository
4. GitHub repository with Actions enabled
5. Permissions to configure Workload Identity Federation

## Setup

### 1. Configure Workload Identity Federation

Workload Identity Federation allows GitHub Actions to authenticate to GCP without using long-lived service account keys.

#### Step 1: Set variables

```bash
export PROJECT_ID="your-gcp-project-id"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
export POOL_NAME="github"
export PROVIDER_NAME="github-provider"
export REPO="your-org/your-repo"  # e.g., "acme/web-app"
```

#### Step 2: Create Workload Identity Pool

```bash
gcloud iam workload-identity-pools create $POOL_NAME \
  --project=$PROJECT_ID \
  --location=global \
  --display-name="GitHub Actions Pool"
```

#### Step 3: Create Workload Identity Provider

```bash
gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME \
  --project=$PROJECT_ID \
  --location=global \
  --workload-identity-pool=$POOL_NAME \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

#### Step 4: Get the Workload Identity Provider resource name

```bash
gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
  --project=$PROJECT_ID \
  --location=global \
  --workload-identity-pool=$POOL_NAME \
  --format='value(name)'
```

Save this output - you'll use it in your workflows:
```
projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider
```

### 2. Create Service Account

```bash
export SA_NAME="github-actions"
export SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Create service account
gcloud iam service-accounts create $SA_NAME \
  --project=$PROJECT_ID \
  --display-name="GitHub Actions Service Account" \
  --description="Service account for GitHub Actions workflows"
```

### 3. Grant Secret Access

#### Grant Secret Manager access

```bash
# Grant secretAccessor role to the service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

#### Allow GitHub to impersonate the service account

```bash
# For a specific repository
gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/$REPO"
```

**For multiple repositories** (same organization):

```bash
# Allow all repos in an organization
gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository_owner/your-org"
```

### 4. Configure secrets.yml

Create a `secrets.yml` file in your repository root:

```yaml
version: "1.0"

environments:
  production:
    name: production
    gcp_project: your-gcp-project-id
    prefix: myapp-prod

    service_accounts:
      - prod-app@your-gcp-project.iam.gserviceaccount.com

    global_secrets:
      - name: API_KEY
        required: true
      - name: DATABASE_URL
        required: true
      - name: REDIS_URL
        required: true

  staging:
    name: staging
    gcp_project: your-gcp-project-id
    prefix: myapp-staging

    service_accounts:
      - staging-app@your-gcp-project.iam.gserviceaccount.com

    global_secrets:
      - name: API_KEY
        required: true
      - name: DATABASE_URL
        required: true

    projects:
      web-app:
        secrets:
          - name: FRONTEND_URL
            required: true
          - name: ANALYTICS_KEY
            required: false
```

## Usage

### Basic Usage

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

permissions:
  contents: read
  id-token: write  # Required for Workload Identity

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Load Secrets
        uses: ./.github/actions/setup-secrets
        with:
          environment: production
          gcp-project-id: your-gcp-project-id
          workload-identity-provider: projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider
          service-account: github-actions@your-gcp-project.iam.gserviceaccount.com

      - name: Deploy
        run: |
          # Secrets are now available as environment variables
          echo "API_KEY is set: ${API_KEY:+yes}"
          ./deploy.sh
```

### With Project Scope

Load project-specific secrets:

```yaml
- name: Load Web App Secrets
  uses: ./.github/actions/setup-secrets
  with:
    environment: staging
    project: web-app
    gcp-project-id: your-gcp-project-id
    workload-identity-provider: projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider
    service-account: github-actions@your-gcp-project.iam.gserviceaccount.com
```

### Multiple Environments

Deploy to different environments based on branch:

```yaml
name: Multi-Environment Deploy

on:
  push:
    branches: [main, staging, develop]

permissions:
  contents: read
  id-token: write

jobs:
  determine-environment:
    runs-on: ubuntu-latest
    outputs:
      environment: ${{ steps.set-env.outputs.environment }}
    steps:
      - id: set-env
        run: |
          if [ "${{ github.ref }}" = "refs/heads/main" ]; then
            echo "environment=production" >> $GITHUB_OUTPUT
          elif [ "${{ github.ref }}" = "refs/heads/staging" ]; then
            echo "environment=staging" >> $GITHUB_OUTPUT
          else
            echo "environment=development" >> $GITHUB_OUTPUT
          fi

  deploy:
    needs: determine-environment
    runs-on: ubuntu-latest
    environment: ${{ needs.determine-environment.outputs.environment }}

    steps:
      - uses: actions/checkout@v4

      - name: Load Secrets
        uses: ./.github/actions/setup-secrets
        with:
          environment: ${{ needs.determine-environment.outputs.environment }}
          gcp-project-id: your-gcp-project-id
          workload-identity-provider: projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider
          service-account: github-actions@your-gcp-project.iam.gserviceaccount.com

      - name: Deploy
        run: ./deploy.sh
```

### Manual Export

Export secrets in different formats:

```yaml
- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'

- name: Install secrets-manager
  run: pip install botmaro-gcp-secret-manager

- name: Authenticate to GCP
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider
    service_account: github-actions@your-gcp-project.iam.gserviceaccount.com

- name: Export secrets as JSON
  run: |
    secrets-manager export production --format json --output secrets.json

- name: Export secrets as .env
  run: |
    secrets-manager export production --format dotenv --output .env.production
```

## Security Best Practices

### 1. Use Workload Identity Federation

✅ **DO**: Use Workload Identity Federation
❌ **DON'T**: Use long-lived service account keys

```yaml
# Good
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: projects/.../providers/github-provider
    service_account: github-actions@project.iam.gserviceaccount.com

# Bad - Never do this!
- uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}  # ❌
```

### 2. Enable Secret Masking

Always keep masking enabled (default):

```yaml
- uses: ./.github/actions/setup-secrets
  with:
    environment: production
    mask-values: true  # Default, can be omitted
    # ...
```

### 3. Use Least Privilege

Grant only necessary permissions:

```bash
# Only secretAccessor, not secretmanager.admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"  # Read-only
```

### 4. Scope Workload Identity Bindings

Limit which repositories can use the service account:

```bash
# Specific repository
--member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/org/repo"

# Specific branch (even more restrictive)
--member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/org/repo/refs/heads/main"
```

### 5. Enable Validation

Always validate secrets before deployment:

```yaml
- uses: ./.github/actions/setup-secrets
  with:
    environment: production
    validate: true  # Default
    # ...
```

### 6. Use GitHub Environments

Leverage GitHub's environment protection rules:

```yaml
jobs:
  deploy:
    environment:
      name: production
      url: https://myapp.com
    # Required reviewers, wait timer, etc.
```

### 7. Audit Logs

Enable Cloud Audit Logging for Secret Manager:

```bash
# View secret access logs
gcloud logging read "resource.type=secretmanager.googleapis.com/Secret" \
  --limit 50 \
  --format json
```

## Troubleshooting

### Authentication Errors

**Error**: `failed to generate Google Cloud ID token`

**Solutions**:
1. Verify `id-token: write` permission is set
2. Check Workload Identity Pool exists
3. Verify service account binding

```yaml
permissions:
  contents: read
  id-token: write  # ← Required!
```

### Missing Secrets

**Error**: `Required secret 'API_KEY' not found`

**Solutions**:
1. Check secret exists in GCP Secret Manager
2. Verify naming convention matches `secrets.yml`
3. Ensure service account has `secretAccessor` role
4. Check secret is in correct GCP project

```bash
# List secrets
gcloud secrets list --project=your-project-id

# Check secret access
gcloud secrets get-iam-policy SECRET_NAME --project=your-project-id
```

### Validation Failures

**Error**: `Validation failed with errors`

**Solutions**:
1. Run check locally:
   ```bash
   secrets-manager check production --verbose
   ```
2. Fix placeholder values
3. Grant missing service account access
4. Add missing required secrets

### Workload Identity Issues

**Error**: `Permission denied on service account`

**Solutions**:

```bash
# Verify binding
gcloud iam service-accounts get-iam-policy $SA_EMAIL \
  --project=$PROJECT_ID

# Re-add binding if missing
gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/$REPO"
```

## Advanced Patterns

### Conditional Secret Loading

Load different secrets based on conditions:

```yaml
- name: Load Base Secrets
  uses: ./.github/actions/setup-secrets
  with:
    environment: production
    # ...

- name: Load Feature Secrets
  if: contains(github.event.head_commit.message, '[feature-flags]')
  uses: ./.github/actions/setup-secrets
  with:
    environment: production
    project: feature-flags
    # ...
```

### Secret Rotation Detection

Schedule checks to detect secrets needing rotation:

```yaml
name: Secret Health Check

on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - run: pip install botmaro-gcp-secret-manager

      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ env.WIP }}
          service_account: ${{ env.SA }}

      - name: Check secrets
        run: |
          secrets-manager check production --verbose

      - name: Create issue on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Secrets validation failed',
              labels: ['security']
            })
```

### Multi-Project Deployment

Deploy multiple projects in parallel:

```yaml
jobs:
  deploy:
    strategy:
      matrix:
        project: [web-app, api-service, worker]

    steps:
      - uses: actions/checkout@v4

      - name: Load ${{ matrix.project }} secrets
        uses: ./.github/actions/setup-secrets
        with:
          environment: production
          project: ${{ matrix.project }}
          # ...

      - name: Deploy ${{ matrix.project }}
        run: ./scripts/deploy-${{ matrix.project }}.sh
```

### Export to Artifacts

Export secrets for later use:

```yaml
- name: Export secrets
  run: |
    secrets-manager export production \
      --format json \
      --output secrets.json \
      --no-mask  # Only if artifact is secured!

- name: Upload artifact
  uses: actions/upload-artifact@v4
  with:
    name: secrets
    path: secrets.json
    retention-days: 1  # Short retention for security
```

## Related Documentation

- [Setup Secrets Action README](.github/actions/setup-secrets/README.md)
- [Workload Identity Federation Guide](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

## Need Help?

- 📖 [Main README](../README.md)
- 🐛 [Report an Issue](https://github.com/your-org/botmaro-gcp-secret-manager/issues)
- 💬 [Discussions](https://github.com/your-org/botmaro-gcp-secret-manager/discussions)