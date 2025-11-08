# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Secrets validation and checking (`check` command)**
  - New `secrets-manager check` command for comprehensive validation
  - Detects missing secrets in GSM
  - Identifies placeholder values (PLACEHOLDER, TODO, changeme, etc.)
  - Identifies placeholder service accounts
  - Verifies service account access to secrets
  - Parses GitHub Actions workflow files to extract secret references
  - Validates that workflow secrets are defined in config
  - Supports both individual workflow files and directories
  - Returns error exit code for CI/CD integration
  - Color-coded output showing errors (red), warnings (yellow), and success (green)
  - Verbose mode for detailed findings
  - Use cases: pre-deployment validation, audit, troubleshooting
- **Automatic service account access grants during bootstrap**
  - Configure service accounts in `secrets.yml` at environment and project levels
  - Bootstrap command automatically grants `secretAccessor` role to configured service accounts
  - Idempotent access granting: only grants if access is missing
  - New `service_accounts` field in EnvironmentConfig and ProjectConfig
  - New GSM methods: `has_access()`, `ensure_access()`
  - Automatic inheritance: project secrets get both env-level and project-level service accounts
- Bulk IAM permission granting via `grant-access` command
  - Grant access to all secrets in an environment or project scope
  - Support for multiple service accounts via repeatable `--sa` flag
  - Interactive confirmation with preview of affected secrets
  - Python API: `grant_access_bulk()` method in SecretsManager
- Placeholder highlighting in list command
  - Placeholder values displayed in red for easy identification
  - Works with both masked and revealed values
- Scope filtering in list command
  - New `--scope` option with values: `env`, `project`, `all`
  - Filter secrets by environment-level or project-level
  - Returns 3-tuple with scope information
- Comprehensive documentation for automatic access grants and check command in README
- Auto-merge workflow: automatically merges `develop` into `main` when all tests pass
- Type checking improvements and mypy compliance

### Changed
- Bootstrap command now reads and applies service accounts from config automatically
- `--runtime-sa` and `--deployer-sa` flags now add to configured service accounts (not replace)
- Updated Python type annotations for better mypy compatibility
- Changed mypy Python version target from 3.8 to 3.9
- Clarified README documentation to emphasize this tool IS the GCP interface
- Detangled from superbot references, updated all URLs to standalone repository

### Fixed
- Code formatting with Black across all Python files
- Type checking errors in cli.py and gsm.py
- Return type annotation in parse_target function

## [0.1.0] - 2025-01-07

### Added
- Initial release of Botmaro Secrets Manager
- Multi-environment secret management with Google Secret Manager
- CLI commands: bootstrap, set, get, list, delete
- Environment-scoped and project-scoped secret organization
- Double-hyphen naming convention for hierarchical secrets
- IAM integration for service account access management
- GitHub Actions CI/CD support
- Python 3.8+ compatibility
- Rich CLI with beautiful terminal output
- Configuration via YAML files
- Secret versioning support
- Automatic secret creation and updates

### Security
- Automatic IAM permission grants for runtime service accounts
- Secret value masking in CLI output by default
- Support for reading secrets from stdin for security

[Unreleased]: https://github.com/B9ice/botmaro-gcp-secret-manager/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/B9ice/botmaro-gcp-secret-manager/releases/tag/v0.1.0