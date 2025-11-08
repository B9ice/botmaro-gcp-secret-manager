"""Tests for secrets naming convention."""

import pytest
from secrets_manager.core import SecretsManager
from secrets_manager.config import SecretsConfig, EnvironmentConfig, SecretConfig


def test_secret_naming_convention():
    """Test that secrets use double-hyphen (--) convention."""

    # Create test config
    config = SecretsConfig(
        environments={
            "staging": EnvironmentConfig(
                name="staging",
                gcp_project="test-project",
                prefix="botmaro-staging",
                global_secrets=[
                    SecretConfig(name="API_KEY", required=True)
                ]
            )
        }
    )

    manager = SecretsManager(config)

    # Test environment-scoped secret
    secret_name = manager._get_secret_name("staging", None, "API_KEY")
    assert secret_name == "botmaro-staging--API_KEY"
    assert "--" in secret_name
    assert secret_name.count("--") == 1

    # Test project-scoped secret
    secret_name = manager._get_secret_name("staging", "orchestrator", "DATABASE_URL")
    assert secret_name == "botmaro-staging--orchestrator--DATABASE_URL"
    assert secret_name.count("--") == 2

    # Test parsing
    parts = secret_name.split("--")
    assert parts[0] == "botmaro-staging"  # prefix
    assert parts[1] == "orchestrator"      # project
    assert parts[2] == "DATABASE_URL"      # secret


def test_secret_naming_with_custom_prefix():
    """Test naming with custom prefix containing hyphens."""

    config = SecretsConfig(
        environments={
            "prod": EnvironmentConfig(
                name="prod",
                gcp_project="test-project",
                prefix="my-longer-company-prefix",
                global_secrets=[]
            )
        }
    )

    manager = SecretsManager(config)

    # Environment-scoped
    secret_name = manager._get_secret_name("prod", None, "SUPABASE_URL")
    assert secret_name == "my-longer-company-prefix--SUPABASE_URL"

    # Project-scoped
    secret_name = manager._get_secret_name("prod", "my-service", "API_KEY")
    assert secret_name == "my-longer-company-prefix--my-service--API_KEY"

    # Verify unambiguous parsing
    parts = secret_name.split("--")
    assert parts[0] == "my-longer-company-prefix"
    assert parts[1] == "my-service"
    assert parts[2] == "API_KEY"


def test_secret_naming_examples():
    """Test various real-world naming examples."""

    examples = [
        # (prefix, project, secret, expected)
        ("botmaro-staging", None, "API_KEY", "botmaro-staging--API_KEY"),
        ("botmaro-staging", "orchestrator", "DATABASE_URL", "botmaro-staging--orchestrator--DATABASE_URL"),
        ("my-company-prod", "auth-service", "JWT_SECRET", "my-company-prod--auth-service--JWT_SECRET"),
        ("acme-dev", None, "SUPABASE_URL", "acme-dev--SUPABASE_URL"),
    ]

    for prefix, project, secret, expected in examples:
        config = SecretsConfig(
            environments={
                "test": EnvironmentConfig(
                    name="test",
                    gcp_project="test-project",
                    prefix=prefix,
                    global_secrets=[]
                )
            }
        )

        manager = SecretsManager(config)
        result = manager._get_secret_name("test", project, secret)

        assert result == expected, f"Expected {expected}, got {result}"

        # Verify can be parsed back
        parts = result.split("--")
        if project:
            assert len(parts) == 3
            assert parts[0] == prefix
            assert parts[1] == project
            assert parts[2] == secret
        else:
            assert len(parts) == 2
            assert parts[0] == prefix
            assert parts[1] == secret


if __name__ == "__main__":
    pytest.main([__file__, "-v"])