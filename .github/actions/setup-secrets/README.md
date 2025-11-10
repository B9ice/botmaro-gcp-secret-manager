# Setup GCP Secrets Action

This GitHub Action loads secrets from GCP Secret Manager into your GitHub Actions workflow environment.

## Features

- 🔐 **Secure Authentication** - Uses Workload Identity Federation (no long-lived keys)
- ✅ **Automatic Validation** - Validates secrets before loading
- 🎯 **Environment & Project Scoping** - Load secrets for specific environments and projects
- 🔒 **Auto-Masking** - Automatically masks secrets in GitHub Actions logs
- 📊 **Outputs** - Provides count of loaded secrets and validation status

## Prerequisites

1. **GCP Workload Identity Federation** configured for GitHub Actions
2. **Service Account** with `secretAccessor` role on required secrets
3. **secrets.yml** configuration file in your repository

## Setup Workload Identity Federation

Follow the [official Google Cloud guide](https://github.com/google-github-actions/auth#setup) or use these commands:

```bash
# Set variables
PROJECT_ID="your-gcp-project"
POOL_NAME="github"
PROVIDER_NAME="github-provider"
SA_NAME="github-actions"
REPO="your-org/your-repo"

# Create Workload Identity Pool
gcloud iam workload-identity-pools create $POOL_NAME \
  --project=$PROJECT_ID \
  --location=global \
  --display-name="GitHub Actions Pool"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME \
  --project=$PROJECT_ID \
  --location=global \
  --workload-identity-pool=$POOL_NAME \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Create Service Account
gcloud iam service-accounts create $SA_NAME \
  --project=$PROJECT_ID \
  --display-name="GitHub Actions Service Account"

# Grant Service Account access to secrets
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Allow GitHub repo to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding "$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/$REPO"
```

## Usage

### Basic Example

```yaml
name: Deploy Application

on:
  push:
    branches: [main]

permissions:
  contents: read
  id-token: write  # Required for Workload Identity

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      # Load secrets from GCP Secret Manager
      - name: Load Secrets
        uses: ./.github/actions/setup-secrets
        with:
          environment: production
          gcp-project-id: my-gcp-project
          workload-identity-provider: projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider
          service-account: github-actions@my-gcp-project.iam.gserviceaccount.com

      # Secrets are now available as environment variables
      - name: Deploy
        run: |
          echo "API Key starts with: ${API_KEY:0:4}****"
          ./deploy.sh
```

### With Project Scope

```yaml
- name: Load Secrets
  uses: ./.github/actions/setup-secrets
  with:
    environment: staging
    project: web-app
    gcp-project-id: my-gcp-project
    workload-identity-provider: projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider
    service-account: github-actions@my-gcp-project.iam.gserviceaccount.com
```

### Custom Configuration Path

```yaml
- name: Load Secrets
  uses: ./.github/actions/setup-secrets
  with:
    environment: production
    config-path: config/secrets.yml
    gcp-project-id: my-gcp-project
    workload-identity-provider: projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider
    service-account: github-actions@my-gcp-project.iam.gserviceaccount.com
```

### Skip Validation

```yaml
- name: Load Secrets
  uses: ./.github/actions/setup-secrets
  with:
    environment: development
    validate: false
    gcp-project-id: my-gcp-project
    workload-identity-provider: projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider
    service-account: github-actions@my-gcp-project.iam.gserviceaccount.com
```

### Using Outputs

```yaml
- name: Load Secrets
  id: secrets
  uses: ./.github/actions/setup-secrets
  with:
    environment: staging
    gcp-project-id: my-gcp-project
    workload-identity-provider: projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider
    service-account: github-actions@my-gcp-project.iam.gserviceaccount.com

- name: Check loaded secrets
  run: |
    echo "Loaded ${{ steps.secrets.outputs.secrets-count }} secrets"
    echo "Validation passed: ${{ steps.secrets.outputs.validation-passed }}"
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `environment` | Environment name (e.g., staging, production) | Yes | - |
| `project` | Project name for project-scoped secrets | No | - |
| `gcp-project-id` | GCP Project ID containing the secrets | Yes | - |
| `workload-identity-provider` | Workload Identity Provider for authentication | Yes | - |
| `service-account` | Service account email for impersonation | Yes | - |
| `config-path` | Path to secrets.yml configuration file | No | `secrets.yml` |
| `validate` | Run validation check before export | No | `true` |
| `mask-values` | Mask secret values in logs | No | `true` |
| `python-version` | Python version to use | No | `3.11` |

## Outputs

| Output | Description |
|--------|-------------|
| `secrets-count` | Number of secrets loaded |
| `validation-passed` | Whether validation passed (true/false) |

## Security Best Practices

1. **Always use Workload Identity Federation** - Never use long-lived service account keys
2. **Enable masking** - Keep `mask-values: true` to prevent secret exposure in logs
3. **Least privilege** - Grant service accounts only `secretAccessor` role
4. **Scope access** - Use repository-specific workload identity bindings
5. **Validate secrets** - Keep `validate: true` to catch missing or placeholder secrets
6. **Audit logging** - Enable Cloud Audit Logs for Secret Manager

## Troubleshooting

### Authentication Errors

If you see authentication errors:

1. Verify Workload Identity Federation is configured correctly
2. Check service account has proper IAM bindings
3. Ensure `permissions.id-token: write` is set in workflow

```yaml
permissions:
  contents: read
  id-token: write  # Required!
```

### Missing Secrets

If secrets are not available:

1. Check validation output for missing secrets
2. Verify secrets exist in GCP Secret Manager
3. Ensure service account has `secretAccessor` role
4. Check secret naming matches `secrets.yml` configuration

### Validation Failures

If validation fails:

1. Review validation output for specific errors
2. Check for placeholder values in secrets
3. Verify all required secrets are defined
4. Ensure service accounts have proper access

## Examples

See the [examples directory](../../../examples/) for complete workflow examples:

- [Simple deployment](../../../examples/workflows/deploy.yml)
- [Multi-environment](../../../examples/workflows/multi-environment.yml)
- [Matrix builds](../../../examples/workflows/matrix.yml)

## License

MIT