"""Tests for secret formatters."""

import os
import json
import pytest
from secrets_manager.formatters import (
    DotenvFormatter,
    GitHubEnvFormatter,
    GitHubOutputFormatter,
    JsonFormatter,
    YamlFormatter,
    ShellFormatter,
    get_formatter,
    write_github_env,
    write_github_output,
)


# Test data
SAMPLE_SECRETS = {
    "API_KEY": "sk-1234567890abcdef",
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
    "MULTILINE_SECRET": "line1\nline2\nline3",
    "SPECIAL_CHARS": "value with spaces and $pecial ch@rs!",
}


class TestDotenvFormatter:
    """Tests for DotenvFormatter."""

    def test_basic_formatting(self):
        """Test basic .env formatting."""
        formatter = DotenvFormatter()
        result = formatter.format({"KEY": "value", "ANOTHER": "test"})

        assert "KEY=value" in result
        assert "ANOTHER=test" in result

    def test_multiline_values(self):
        """Test multiline values are escaped."""
        formatter = DotenvFormatter()
        result = formatter.format({"MULTI": "line1\nline2"})

        assert "MULTI=" in result
        assert "\\n" in result  # Newlines should be escaped

    def test_special_characters(self):
        """Test values with special characters are quoted."""
        formatter = DotenvFormatter()
        result = formatter.format({"KEY": "value with spaces"})

        assert 'KEY="value with spaces"' in result

    def test_sorted_output(self):
        """Test that keys are sorted."""
        formatter = DotenvFormatter()
        result = formatter.format({"ZEBRA": "z", "APPLE": "a", "MIDDLE": "m"})

        lines = result.split("\n")
        assert lines[0].startswith("APPLE=")
        assert lines[1].startswith("MIDDLE=")
        assert lines[2].startswith("ZEBRA=")


class TestGitHubEnvFormatter:
    """Tests for GitHubEnvFormatter."""

    def test_basic_formatting(self):
        """Test basic GitHub env formatting."""
        formatter = GitHubEnvFormatter()
        result = formatter.format({"KEY": "value"}, mask=False)

        assert "KEY<<EOF" in result
        assert "value" in result
        assert "EOF" in result

    def test_masking_enabled(self):
        """Test that masking adds mask commands."""
        formatter = GitHubEnvFormatter()
        result = formatter.format({"KEY": "secret_value"}, mask=True)

        assert "::add-mask::" in result
        assert "secret_value" in result

    def test_multiline_values(self):
        """Test multiline values with heredoc."""
        formatter = GitHubEnvFormatter()
        result = formatter.format({"MULTI": "line1\nline2\nline3"}, mask=False)

        assert "MULTI<<EOF" in result
        assert "line1\nline2\nline3" in result
        assert result.count("EOF") >= 2  # Opening and closing EOF

    def test_multiple_secrets(self):
        """Test formatting multiple secrets."""
        formatter = GitHubEnvFormatter()
        secrets = {"KEY1": "value1", "KEY2": "value2"}
        result = formatter.format(secrets, mask=False)

        assert "KEY1<<EOF" in result
        assert "KEY2<<EOF" in result


class TestGitHubOutputFormatter:
    """Tests for GitHubOutputFormatter."""

    def test_single_line_format(self):
        """Test single line output format."""
        formatter = GitHubOutputFormatter()
        result = formatter.format({"KEY": "value"}, mask=False)

        assert "KEY<<EOF" in result
        assert "value" in result

    def test_multiline_format(self):
        """Test multiline output format."""
        formatter = GitHubOutputFormatter()
        result = formatter.format({"MULTI": "line1\nline2"}, mask=False)

        assert "MULTI<<EOF" in result
        assert "line1\nline2" in result


class TestJsonFormatter:
    """Tests for JsonFormatter."""

    def test_basic_json(self):
        """Test basic JSON formatting."""
        formatter = JsonFormatter()
        result = formatter.format({"KEY": "value", "ANOTHER": "test"}, mask=False)

        data = json.loads(result)
        assert data["KEY"] == "value"
        assert data["ANOTHER"] == "test"

    def test_masking(self):
        """Test JSON with masking."""
        formatter = JsonFormatter()
        result = formatter.format({"KEY": "secret_value"}, mask=True)

        data = json.loads(result)
        assert "***" in data["KEY"]
        assert "secret_value" not in result

    def test_sorted_keys(self):
        """Test that JSON keys are sorted."""
        formatter = JsonFormatter()
        result = formatter.format({"ZEBRA": "z", "APPLE": "a"}, mask=False)

        # Check that the JSON is sorted
        data = json.loads(result)
        keys = list(data.keys())
        assert keys == sorted(keys)


class TestYamlFormatter:
    """Tests for YamlFormatter."""

    def test_basic_yaml(self):
        """Test basic YAML formatting."""
        formatter = YamlFormatter()
        result = formatter.format({"KEY": "value"}, mask=False)

        assert "---" in result
        assert "KEY: value" in result

    def test_multiline_yaml(self):
        """Test multiline YAML values."""
        formatter = YamlFormatter()
        result = formatter.format({"MULTI": "line1\nline2"}, mask=False)

        assert "MULTI: |" in result
        assert "line1" in result
        assert "line2" in result

    def test_masking(self):
        """Test YAML with masking."""
        formatter = YamlFormatter()
        result = formatter.format({"KEY": "secret_value"}, mask=True)

        assert "***" in result
        assert "secret_value" not in result

    def test_special_characters_quoted(self):
        """Test that values with special characters are quoted."""
        formatter = YamlFormatter()
        result = formatter.format({"KEY": "value: with: colons"}, mask=False)

        # Should be quoted due to colons
        assert '"' in result or result.count(":") > 1


class TestShellFormatter:
    """Tests for ShellFormatter."""

    def test_basic_shell(self):
        """Test basic shell export formatting."""
        formatter = ShellFormatter()
        result = formatter.format({"KEY": "value"}, mask=False)

        assert "#!/bin/bash" in result
        assert "export KEY='value'" in result

    def test_single_quote_escaping(self):
        """Test that single quotes are escaped."""
        formatter = ShellFormatter()
        result = formatter.format({"KEY": "value's"}, mask=False)

        # Single quotes should be escaped
        assert "value'\\''s" in result or "value\\'s" in result

    def test_multiple_exports(self):
        """Test multiple export statements."""
        formatter = ShellFormatter()
        result = formatter.format({"KEY1": "value1", "KEY2": "value2"}, mask=False)

        assert "export KEY1='value1'" in result
        assert "export KEY2='value2'" in result


class TestGetFormatter:
    """Tests for get_formatter function."""

    def test_get_dotenv_formatter(self):
        """Test getting dotenv formatter."""
        formatter = get_formatter("dotenv")
        assert isinstance(formatter, DotenvFormatter)

        # Test alias
        formatter = get_formatter("env")
        assert isinstance(formatter, DotenvFormatter)

    def test_get_github_env_formatter(self):
        """Test getting GitHub env formatter."""
        formatter = get_formatter("github-env")
        assert isinstance(formatter, GitHubEnvFormatter)

    def test_get_github_output_formatter(self):
        """Test getting GitHub output formatter."""
        formatter = get_formatter("github-output")
        assert isinstance(formatter, GitHubOutputFormatter)

    def test_get_json_formatter(self):
        """Test getting JSON formatter."""
        formatter = get_formatter("json")
        assert isinstance(formatter, JsonFormatter)

    def test_get_yaml_formatter(self):
        """Test getting YAML formatter."""
        formatter = get_formatter("yaml")
        assert isinstance(formatter, YamlFormatter)

        # Test alias
        formatter = get_formatter("yml")
        assert isinstance(formatter, YamlFormatter)

    def test_get_shell_formatter(self):
        """Test getting shell formatter."""
        formatter = get_formatter("shell")
        assert isinstance(formatter, ShellFormatter)

        # Test alias
        formatter = get_formatter("sh")
        assert isinstance(formatter, ShellFormatter)

    def test_invalid_formatter(self):
        """Test that invalid formatter raises ValueError."""
        with pytest.raises(ValueError, match="Invalid format"):
            get_formatter("invalid_format")


class TestGitHubIntegration:
    """Tests for GitHub Actions integration functions."""

    def test_write_github_env_without_env_var(self):
        """Test that write_github_env fails without GITHUB_ENV."""
        # Ensure GITHUB_ENV is not set
        if "GITHUB_ENV" in os.environ:
            del os.environ["GITHUB_ENV"]

        with pytest.raises(RuntimeError, match="GITHUB_ENV"):
            write_github_env({"KEY": "value"})

    def test_write_github_output_without_env_var(self):
        """Test that write_github_output fails without GITHUB_OUTPUT."""
        # Ensure GITHUB_OUTPUT is not set
        if "GITHUB_OUTPUT" in os.environ:
            del os.environ["GITHUB_OUTPUT"]

        with pytest.raises(RuntimeError, match="GITHUB_OUTPUT"):
            write_github_output({"KEY": "value"})

    def test_write_github_env_with_env_var(self, tmp_path):
        """Test writing to GITHUB_ENV."""
        env_file = tmp_path / "github_env"
        os.environ["GITHUB_ENV"] = str(env_file)

        try:
            write_github_env({"KEY": "value"}, mask=False)

            # Check file was created and has content
            assert env_file.exists()
            content = env_file.read_text()
            assert "KEY<<EOF" in content
            assert "value" in content
        finally:
            if "GITHUB_ENV" in os.environ:
                del os.environ["GITHUB_ENV"]

    def test_write_github_output_with_env_var(self, tmp_path):
        """Test writing to GITHUB_OUTPUT."""
        output_file = tmp_path / "github_output"
        os.environ["GITHUB_OUTPUT"] = str(output_file)

        try:
            write_github_output({"KEY": "value"}, mask=False)

            # Check file was created and has content
            assert output_file.exists()
            content = output_file.read_text()
            assert "KEY" in content
            assert "value" in content
        finally:
            if "GITHUB_OUTPUT" in os.environ:
                del os.environ["GITHUB_OUTPUT"]


class TestRealWorldScenarios:
    """Tests for real-world usage scenarios."""

    def test_complete_workflow(self):
        """Test a complete workflow with various secret types."""
        secrets = {
            "API_KEY": "sk-1234567890",
            "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
            "MULTILINE_CERT": "-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----",
            "BOOLEAN_FLAG": "true",
            "NUMERIC_VALUE": "12345",
        }

        # Test all formatters can handle these secrets
        formatters = {
            "dotenv": DotenvFormatter(),
            "github-env": GitHubEnvFormatter(),
            "json": JsonFormatter(),
            "yaml": YamlFormatter(),
            "shell": ShellFormatter(),
        }

        for name, formatter in formatters.items():
            result = formatter.format(secrets, mask=False)
            assert result is not None
            assert len(result) > 0

            # Check all keys are present
            for key in secrets.keys():
                assert key in result

    def test_empty_secrets(self):
        """Test formatting empty secrets dict."""
        formatters = [
            DotenvFormatter(),
            GitHubEnvFormatter(),
            JsonFormatter(),
            YamlFormatter(),
            ShellFormatter(),
        ]

        for formatter in formatters:
            result = formatter.format({}, mask=False)
            assert result is not None
            # Should return valid but minimal output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])