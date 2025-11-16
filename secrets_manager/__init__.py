"""
Botmaro Secrets Manager

A standalone secret management tool for multi-environment deployments
with Google Secret Manager.
"""

__version__ = "0.3.1"

from .core import SecretsManager
from .config import SecretConfig, EnvironmentConfig

__all__ = ["SecretsManager", "SecretConfig", "EnvironmentConfig"]
