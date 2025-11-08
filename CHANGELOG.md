# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Bulk IAM permission granting via `grant-access` command
  - Grant access to all secrets in an environment or project scope
  - Support for multiple service accounts via repeatable `--sa` flag
  - Interactive confirmation with preview of affected secrets
  - Python API: `grant_access_bulk()` method in SecretsManager
- Comprehensive documentation for grant-access in README
- Auto-merge workflow: automatically merges `develop` into `main` when all tests pass
- Type checking improvements and mypy compliance

### Changed
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