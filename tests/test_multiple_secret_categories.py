"""Test that all *_secrets sections are read correctly (not just global_secrets)."""

import pytest
from secrets_manager.core import SecretsManager
from secrets_manager.config import SecretsConfig, EnvironmentConfig, SecretConfig


def test_multiple_secret_categories():
    """Test that bootstrap reads all *_secrets categories."""

    # Create test config with multiple secret categories
    config = SecretsConfig(
        environments={
            "staging": EnvironmentConfig(
                name="staging",
                gcp_project="test-project",
                prefix="botmaro-staging",
                global_secrets=[
                    SecretConfig(name="GLOBAL_API_KEY", required=True)
                ],
                **{
                    "serverside_secrets": [
                        {"name": "SENDGRID_API_KEY", "required": True},
                        {"name": "TWILIO_TOKEN", "required": True},
                    ],
                    "mobile_secrets": [
                        {"name": "MOBILE_API_KEY", "required": True},
                    ],
                }
            )
        }
    )

    # Test that environment config has the extra fields
    env = config.get_environment("staging")
    assert env is not None

    # Test get_all_secret_categories returns all categories
    categories = env.get_all_secret_categories()

    # Should have 3 categories
    assert len(categories) == 3

    # Check each category exists and has the right secrets
    assert "global_secrets" in categories
    assert len(categories["global_secrets"]) == 1
    assert categories["global_secrets"][0].name == "GLOBAL_API_KEY"

    assert "serverside_secrets" in categories
    assert len(categories["serverside_secrets"]) == 2
    assert categories["serverside_secrets"][0].name == "SENDGRID_API_KEY"
    assert categories["serverside_secrets"][1].name == "TWILIO_TOKEN"

    assert "mobile_secrets" in categories
    assert len(categories["mobile_secrets"]) == 1
    assert categories["mobile_secrets"][0].name == "MOBILE_API_KEY"


def test_secret_naming_with_different_categories():
    """Test that secret naming works for all categories."""

    config = SecretsConfig(
        environments={
            "prod": EnvironmentConfig(
                name="prod",
                gcp_project="test-project",
                prefix="my-app-prod",
                global_secrets=[
                    SecretConfig(name="SUPABASE_URL", required=True)
                ],
                **{
                    "serverside_secrets": [
                        {"name": "STRIPE_SECRET_KEY", "required": True},
                    ],
                }
            )
        }
    )

    manager = SecretsManager(config)

    # All secrets should use the same naming convention regardless of category
    global_secret = manager._get_secret_name("prod", None, "SUPABASE_URL")
    assert global_secret == "my-app-prod--SUPABASE_URL"

    serverside_secret = manager._get_secret_name("prod", None, "STRIPE_SECRET_KEY")
    assert serverside_secret == "my-app-prod--STRIPE_SECRET_KEY"


def test_empty_secret_categories():
    """Test that empty secret categories are handled correctly."""

    config = SecretsConfig(
        environments={
            "dev": EnvironmentConfig(
                name="dev",
                gcp_project="test-project",
                prefix="my-app-dev",
                global_secrets=[],
                **{
                    "serverside_secrets": [],
                    "mobile_secrets": [],
                }
            )
        }
    )

    env = config.get_environment("dev")
    categories = env.get_all_secret_categories()

    # Should return empty lists for empty categories
    assert len(categories) == 3
    assert len(categories["global_secrets"]) == 0
    assert len(categories["serverside_secrets"]) == 0
    assert len(categories["mobile_secrets"]) == 0


def test_only_global_secrets():
    """Test backward compatibility with configs that only have global_secrets."""

    config = SecretsConfig(
        environments={
            "legacy": EnvironmentConfig(
                name="legacy",
                gcp_project="test-project",
                prefix="legacy-app",
                global_secrets=[
                    SecretConfig(name="API_KEY", required=True),
                    SecretConfig(name="DB_URL", required=True),
                ]
            )
        }
    )

    env = config.get_environment("legacy")
    categories = env.get_all_secret_categories()

    # Should only have global_secrets
    assert len(categories) == 1
    assert "global_secrets" in categories
    assert len(categories["global_secrets"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])