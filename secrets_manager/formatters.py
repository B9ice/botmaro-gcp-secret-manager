"""Formatters for exporting secrets in various formats."""

import json
import os
from abc import ABC, abstractmethod
from typing import Dict


class BaseFormatter(ABC):
    """Base class for secret formatters."""

    @abstractmethod
    def format(self, secrets: Dict[str, str], mask: bool = False) -> str:
        """
        Format secrets for output.

        Args:
            secrets: Dictionary of secret name to value
            mask: Whether to mask secrets in logs (GitHub Actions)

        Returns:
            Formatted string
        """
        pass


class DotenvFormatter(BaseFormatter):
    """Format secrets as .env file (KEY=VALUE)."""

    def format(self, secrets: Dict[str, str], mask: bool = False) -> str:
        """
        Format secrets as .env file with proper escaping.

        Args:
            secrets: Dictionary of secret name to value
            mask: Whether to mask secrets (not used for dotenv)

        Returns:
            .env formatted string
        """
        lines = []
        for key, value in sorted(secrets.items()):
            # Escape quotes and newlines
            escaped_value = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

            # Quote value if it contains spaces or special chars
            if (
                " " in value
                or "#" in value
                or "\n" in value
                or any(c in value for c in ["$", "`", "!", "&", "*"])
            ):
                lines.append(f'{key}="{escaped_value}"')
            else:
                lines.append(f"{key}={escaped_value}")

        return "\n".join(lines)


class GitHubEnvFormatter(BaseFormatter):
    """
    Format secrets for GitHub Actions environment file.

    Supports multiline values using heredoc syntax.
    Automatically masks secrets in logs if requested.
    """

    def format(self, secrets: Dict[str, str], mask: bool = True) -> str:
        """
        Format secrets for GitHub Actions $GITHUB_ENV file.

        Uses heredoc syntax for proper multiline support:
        KEY<<EOF
        value
        EOF

        Args:
            secrets: Dictionary of secret name to value
            mask: Whether to add GitHub Actions mask commands

        Returns:
            GitHub env file formatted string
        """
        lines = []

        # Add mask commands first if requested
        if mask:
            lines.append("# Masking secrets in GitHub Actions logs")
            for value in secrets.values():
                if value:  # Only mask non-empty values
                    lines.append(f"echo '::add-mask::{value}'")
            lines.append("")

        # Add secrets using heredoc syntax for multiline support
        for key, value in sorted(secrets.items()):
            if "\n" in value:
                # Multiline value - use heredoc
                lines.append(f"{key}<<EOF")
                lines.append(value)
                lines.append("EOF")
            else:
                # Single line value
                lines.append(f"{key}<<EOF")
                lines.append(value)
                lines.append("EOF")

        return "\n".join(lines)


class GitHubOutputFormatter(BaseFormatter):
    """Format secrets as GitHub Actions job outputs."""

    def format(self, secrets: Dict[str, str], mask: bool = True) -> str:
        """
        Format secrets for GitHub Actions job outputs ($GITHUB_OUTPUT).

        Args:
            secrets: Dictionary of secret name to value
            mask: Whether to add mask commands

        Returns:
            GitHub output formatted string
        """
        lines = []

        if mask:
            lines.append("# Masking secrets")
            for value in secrets.values():
                if value:
                    lines.append(f"echo '::add-mask::{value}'")
            lines.append("")

        for key, value in sorted(secrets.items()):
            # Use heredoc format for all values (GitHub Actions best practice)
            lines.append(f"{key}<<EOF")
            lines.append(value)
            lines.append("EOF")

        return "\n".join(lines)


class JsonFormatter(BaseFormatter):
    """Format secrets as JSON."""

    def format(self, secrets: Dict[str, str], mask: bool = False) -> str:
        """
        Format secrets as JSON object.

        Args:
            secrets: Dictionary of secret name to value
            mask: Whether to mask values (if True, redacts values)

        Returns:
            JSON formatted string
        """
        if mask:
            masked_secrets = {
                key: f"{value[:4]}***" if len(value) > 4 else "***"
                for key, value in secrets.items()
            }
            return json.dumps(masked_secrets, indent=2, sort_keys=True)

        return json.dumps(secrets, indent=2, sort_keys=True)


class YamlFormatter(BaseFormatter):
    """Format secrets as YAML."""

    def format(self, secrets: Dict[str, str], mask: bool = False) -> str:
        """
        Format secrets as YAML.

        Args:
            secrets: Dictionary of secret name to value
            mask: Whether to mask values

        Returns:
            YAML formatted string
        """
        lines = ["---"]

        for key, value in sorted(secrets.items()):
            if mask:
                masked = f"{value[:4]}***" if len(value) > 4 else "***"
                lines.append(f"{key}: {masked}")
            elif "\n" in value:
                # Multiline value
                lines.append(f"{key}: |")
                for line in value.split("\n"):
                    lines.append(f"  {line}")
            elif any(
                c in value
                for c in [":", "#", "[", "]", "{", "}", "&", "*", "!", "|", ">", "@", "`"]
            ):
                # Value needs quoting
                escaped = value.replace('"', '\\"')
                lines.append(f'{key}: "{escaped}"')
            else:
                lines.append(f"{key}: {value}")

        return "\n".join(lines)


class ShellFormatter(BaseFormatter):
    """Format secrets as shell export statements."""

    def format(self, secrets: Dict[str, str], mask: bool = False) -> str:
        """
        Format secrets as shell export commands.

        Args:
            secrets: Dictionary of secret name to value
            mask: Not used for shell format

        Returns:
            Shell export formatted string
        """
        lines = ["#!/bin/bash"]
        lines.append("# Auto-generated secrets export")
        lines.append("# Source this file: source secrets.sh")
        lines.append("")

        for key, value in sorted(secrets.items()):
            # Escape single quotes for shell
            escaped = value.replace("'", "'\\''")
            lines.append(f"export {key}='{escaped}'")

        return "\n".join(lines)


def get_formatter(format_name: str) -> BaseFormatter:
    """
    Get a formatter by name.

    Args:
        format_name: Format name (dotenv, github-env, github-output, json, yaml, shell)

    Returns:
        Formatter instance

    Raises:
        ValueError: If format name is invalid
    """
    formatters = {
        "dotenv": DotenvFormatter(),
        "env": DotenvFormatter(),  # Alias
        "github-env": GitHubEnvFormatter(),
        "github-output": GitHubOutputFormatter(),
        "json": JsonFormatter(),
        "yaml": YamlFormatter(),
        "yml": YamlFormatter(),  # Alias
        "shell": ShellFormatter(),
        "sh": ShellFormatter(),  # Alias
    }

    formatter = formatters.get(format_name.lower())
    if not formatter:
        valid_formats = ", ".join(sorted(set(formatters.keys())))
        raise ValueError(f"Invalid format '{format_name}'. Valid formats: {valid_formats}")

    return formatter


def write_github_env(secrets: Dict[str, str], mask: bool = True) -> None:
    """
    Write secrets directly to GitHub Actions environment file.

    This is a convenience function for use in GitHub Actions workflows.

    Args:
        secrets: Dictionary of secret name to value
        mask: Whether to mask secrets in logs

    Raises:
        RuntimeError: If GITHUB_ENV is not set (not running in GitHub Actions)
    """
    github_env = os.getenv("GITHUB_ENV")
    if not github_env:
        raise RuntimeError(
            "GITHUB_ENV environment variable not set. "
            "This function must be called from within a GitHub Actions workflow."
        )

    formatter = GitHubEnvFormatter()
    content = formatter.format(secrets, mask=mask)

    with open(github_env, "a") as f:
        f.write(content)
        f.write("\n")


def write_github_output(secrets: Dict[str, str], mask: bool = True) -> None:
    """
    Write secrets directly to GitHub Actions output file.

    This is a convenience function for use in GitHub Actions workflows.

    Args:
        secrets: Dictionary of secret name to value
        mask: Whether to mask secrets in logs

    Raises:
        RuntimeError: If GITHUB_OUTPUT is not set (not running in GitHub Actions)
    """
    github_output = os.getenv("GITHUB_OUTPUT")
    if not github_output:
        raise RuntimeError(
            "GITHUB_OUTPUT environment variable not set. "
            "This function must be called from within a GitHub Actions workflow."
        )

    formatter = GitHubOutputFormatter()
    content = formatter.format(secrets, mask=mask)

    with open(github_output, "a") as f:
        f.write(content)
        f.write("\n")
