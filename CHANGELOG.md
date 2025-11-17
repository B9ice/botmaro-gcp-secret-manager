# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.1] - 2025-01-16

### Fixed
- **Import command prefix display bug**
  - Fixed bug where import command displayed secret names without the environment prefix
  - Now correctly shows full secret name: `botmaro-staging--SENDGRID_API_KEY` instead of `staging.SENDGRID_API_KEY`
  - Updated `set_secret()` method to return full secret name in result dictionary
  - Applied consistent naming display across both `import` and `set` commands

## [0.4.0] - 2025-01-16

### Added
- **Secret Import Command (`import` command)**
  - New `secrets-manager import` command for bulk secret imports from files
  - Support for multiple file formats: .env, JSON (.json), YAML (.yml, .yaml)
  - Automatic placeholder detection and filtering (skips PLACEHOLDER, TODO, CHANGEME, etc.)
  - `--dry-run` flag for previewing changes without importing
  - `--skip-placeholders` flag to control placeholder filtering behavior
  - `--force` flag to skip confirmation prompts
  - `--grant` flag to assign service account access during import
  - `--project` flag for importing to project-scoped secrets
  - Intelligent parsing of .env files with quote handling
  - Progress tracking with success/failure counts and detailed error reporting
  - Import summary table showing preview of secrets to be imported
  - Graceful error handling for missing or malformed files

### Changed
- `--config` option now defaults to `./secrets.yml` across all commands
- Improved error messages when config file is not found
- Better file format detection for .env files (including files starting with .env)

### Security
- Automatic masking of secret values in import preview (shows first 10 characters)
- Skip empty or placeholder values by default to prevent accidental placeholder imports

## [0.3.0] - 2025-01-10

### Added
- **GitHub Actions Integration**
  - Native GitHub Actions composite action at `.github/actions/setup-secrets/`
  - Automatic secret loading from GCP Secret Manager into workflow environments
  - Workload Identity Federation support (no long-lived keys required)
  - Automatic secret masking in GitHub Actions logs for enhanced security
  - Example workflows for simple, multi-environment, matrix, and advanced patterns
  - Comprehensive documentation in `GITHUB_ACTIONS.md` with complete setup guide
- **Multi-format Secret Export (`export` command)**
  - New `secrets-manager export` command supporting multiple output formats
  - Formats: dotenv, JSON, YAML, GitHub Actions, shell scripts
  - `--github-env` flag for GitHub Actions environment file integration
  - `--github-output` flag for step outputs in GitHub Actions
  - Built-in validation before export to ensure secret integrity
  - Support for environment and project scoping
  - Enables zero-duplication secret management with GCP as single source of truth
- **Secret Formatters Module**
  - New `secrets_manager/formatters.py` with format-specific implementations
  - Comprehensive test suite for all formatters (`tests/test_formatters.py`)
  - Proper escaping and quoting for each format type
  - Support for nested structures in JSON and YAML formats

### Changed
- Updated README with enhanced CI/CD examples and export command documentation
- Improved GitHub Actions examples with best practices
- Enhanced security recommendations for Workload Identity Federation

### Fixed
- Corrected formatter implementations to match test expectations
- Applied Black formatting to `formatters.py` for code consistency

## [0.2.0] - 2025-01-08

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

[Unreleased]: https://github.com/B9ice/botmaro-gcp-secret-manager/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/B9ice/botmaro-gcp-secret-manager/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/B9ice/botmaro-gcp-secret-manager/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/B9ice/botmaro-gcp-secret-manager/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/B9ice/botmaro-gcp-secret-manager/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/B9ice/botmaro-gcp-secret-manager/releases/tag/v0.1.0