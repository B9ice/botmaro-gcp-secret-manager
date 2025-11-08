"""Command-line interface for secrets management."""

import os
import sys
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .core import SecretsManager
from .config import SecretsConfig

app = typer.Typer(
    name="secrets-manager",
    help="Botmaro Secrets Manager - Multi-environment secret management with Google Secret Manager",
    add_completion=False,
)
console = Console()


def parse_target(target: str) -> tuple[str, Optional[str], str]:
    """
    Parse target string into (env, project, secret).

    Examples:
        'staging.myproject' -> ('staging', 'myproject', None)
        'staging' -> ('staging', None, None)
        'staging.myproject.MY_SECRET' -> ('staging', 'myproject', 'MY_SECRET')
        'staging.MY_SECRET' -> ('staging', None, 'MY_SECRET')
    """
    parts = target.split(".")

    if len(parts) == 1:
        # Just environment
        return parts[0], None, None
    elif len(parts) == 2:
        # Could be env.project or env.secret
        # Heuristic: if second part is uppercase, it's a secret
        if parts[1].isupper() or "_" in parts[1]:
            return parts[0], None, parts[1]
        else:
            return parts[0], parts[1], None
    elif len(parts) >= 3:
        # env.project.secret
        return parts[0], parts[1], ".".join(parts[2:])
    else:
        raise ValueError(f"Invalid target format: {target}")


@app.command()
def bootstrap(
    env: str = typer.Argument(..., help="Environment name (e.g., staging, prod)"),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project name to scope secrets"
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to secrets config file"
    ),
    export: bool = typer.Option(
        True, "--export/--no-export", help="Export secrets to environment variables"
    ),
    runtime_sa: Optional[str] = typer.Option(
        None, "--runtime-sa", help="Runtime service account to grant access"
    ),
    deployer_sa: Optional[str] = typer.Option(
        None, "--deployer-sa", help="Deployer service account to grant access"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for .env format"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Bootstrap environment by loading all required secrets.

    This command loads all secrets defined in the configuration for the specified
    environment and optionally exports them to the current shell environment.

    Examples:
        \b
        # Bootstrap staging environment
        secrets-manager bootstrap staging

        \b
        # Bootstrap with project scope
        secrets-manager bootstrap staging --project myapp

        \b
        # Save to .env file
        secrets-manager bootstrap staging --output .env.staging
    """
    try:
        # Load config
        if config:
            os.environ["SECRETS_CONFIG_PATH"] = config

        manager = SecretsManager()

        with console.status(f"[bold green]Loading secrets for {env}..."):
            secrets = manager.bootstrap(
                env=env,
                project=project,
                export_to_env=export,
                runtime_sa=runtime_sa,
                deployer_sa=deployer_sa,
            )

        # Display results
        if verbose:
            table = Table(title=f"Loaded Secrets - {env}" + (f".{project}" if project else ""))
            table.add_column("Secret", style="cyan")
            table.add_column("Value", style="green")

            for key, value in secrets.items():
                # Mask value for security
                masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                table.add_row(key, masked)

            console.print(table)
        else:
            console.print(f"[green]✓[/green] Loaded {len(secrets)} secrets for [bold]{env}[/bold]")

        # Write to output file if specified
        if output:
            output_path = Path(output)
            with open(output_path, "w") as f:
                for key, value in secrets.items():
                    f.write(f"{key}={value}\n")
            console.print(f"[green]✓[/green] Secrets written to {output_path}")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def set(
    target: str = typer.Argument(..., help="Target in format 'env[.project].SECRET_NAME'"),
    value: Optional[str] = typer.Option(None, "--value", "-v", help="Secret value (or use stdin)"),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to secrets config file"
    ),
    grant: Optional[List[str]] = typer.Option(
        None, "--grant", "-g", help="Service accounts to grant access"
    ),
):
    """
    Set a secret value (create or update).

    Examples:
        \b
        # Set an environment-scoped secret
        secrets-manager set staging.API_KEY --value "sk-123456"

        \b
        # Set a project-scoped secret
        secrets-manager set staging.myapp.DATABASE_URL --value "postgres://..."

        \b
        # Read value from stdin
        echo "secret-value" | secrets-manager set staging.MY_SECRET

        \b
        # Grant access to service account
        secrets-manager set staging.API_KEY --value "sk-123" --grant bot@project.iam.gserviceaccount.com
    """
    try:
        # Load config
        if config:
            os.environ["SECRETS_CONFIG_PATH"] = config

        manager = SecretsManager()

        # Parse target
        env, project, secret = parse_target(target)

        if not secret:
            console.print("[red]✗ Error:[/red] Secret name required in target", style="bold red")
            raise typer.Exit(code=1)

        # Get value from stdin if not provided
        if value is None:
            if not sys.stdin.isatty():
                value = sys.stdin.read().strip()
            else:
                value = typer.prompt("Enter secret value", hide_input=True)

        # Set the secret
        with console.status(f"[bold green]Setting secret..."):
            result = manager.set_secret(
                env=env,
                secret=secret,
                value=value,
                project=project,
                grant_to=grant,
            )

        target_str = f"{env}.{project}.{secret}" if project else f"{env}.{secret}"
        console.print(f"[green]✓[/green] Secret [bold]{target_str}[/bold] {result['status']}")
        console.print(f"  Version: {result['version']}")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def get(
    target: str = typer.Argument(..., help="Target in format 'env[.project].SECRET_NAME'"),
    version: str = typer.Option("latest", "--version", help="Secret version to retrieve"),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to secrets config file"
    ),
    reveal: bool = typer.Option(False, "--reveal", help="Show the full secret value"),
):
    """
    Get a secret value.

    Examples:
        \b
        # Get latest version of a secret
        secrets-manager get staging.API_KEY --reveal

        \b
        # Get specific version
        secrets-manager get staging.API_KEY --version 2
    """
    try:
        # Load config
        if config:
            os.environ["SECRETS_CONFIG_PATH"] = config

        manager = SecretsManager()

        # Parse target
        env, project, secret = parse_target(target)

        if not secret:
            console.print("[red]✗ Error:[/red] Secret name required in target", style="bold red")
            raise typer.Exit(code=1)

        # Get the secret
        value = manager.get_secret(env=env, secret=secret, project=project, version=version)

        if value is None:
            console.print(f"[yellow]![/yellow] Secret not found", style="bold yellow")
            raise typer.Exit(code=1)

        if reveal:
            console.print(value)
        else:
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            console.print(f"Value: {masked} (use --reveal to show full value)")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def delete(
    target: str = typer.Argument(..., help="Target in format 'env[.project].SECRET_NAME'"),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to secrets config file"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """
    Delete a secret.

    Examples:
        \b
        # Delete a secret
        secrets-manager delete staging.OLD_API_KEY

        \b
        # Force delete without confirmation
        secrets-manager delete staging.OLD_API_KEY --force
    """
    try:
        # Load config
        if config:
            os.environ["SECRETS_CONFIG_PATH"] = config

        manager = SecretsManager()

        # Parse target
        env, project, secret = parse_target(target)

        if not secret:
            console.print("[red]✗ Error:[/red] Secret name required in target", style="bold red")
            raise typer.Exit(code=1)

        target_str = f"{env}.{project}.{secret}" if project else f"{env}.{secret}"

        # Confirm deletion
        if not force:
            confirm = typer.confirm(f"Delete secret '{target_str}'?")
            if not confirm:
                console.print("Cancelled")
                raise typer.Exit(code=0)

        # Delete the secret
        deleted = manager.delete_secret(env=env, secret=secret, project=project)

        if deleted:
            console.print(f"[green]✓[/green] Secret [bold]{target_str}[/bold] deleted")
        else:
            console.print(f"[yellow]![/yellow] Secret not found", style="bold yellow")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def list(
    env: str = typer.Argument(..., help="Environment name"),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project name to filter by"
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to secrets config file"
    ),
    reveal: bool = typer.Option(False, "--reveal", help="Show secret values"),
):
    """
    List all secrets for an environment.

    Examples:
        \b
        # List all secrets for staging
        secrets-manager list staging

        \b
        # List secrets for a specific project
        secrets-manager list staging --project myapp
    """
    try:
        # Load config
        if config:
            os.environ["SECRETS_CONFIG_PATH"] = config

        manager = SecretsManager()

        # List secrets
        with console.status(f"[bold green]Loading secrets..."):
            secrets = manager.list_secrets(env=env, project=project)

        # Display results
        table = Table(title=f"Secrets - {env}" + (f".{project}" if project else ""))
        table.add_column("Secret Name", style="cyan")
        table.add_column("Value", style="green")

        for name, value in secrets:
            if value and reveal:
                table.add_row(name, value)
            elif value:
                masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                table.add_row(name, masked)
            else:
                table.add_row(name, "[red]<not found>[/red]")

        console.print(table)
        console.print(f"\nTotal: {len(secrets)} secrets")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def grant_access(
    target: str = typer.Argument(
        ..., help="Target in format 'env' or 'env.project' to grant access to all secrets"
    ),
    service_account: List[str] = typer.Option(
        ..., "--sa", help="Service account email(s) to grant access (can be repeated)"
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to secrets config file"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """
    Grant access to all secrets in an environment or project.

    This grants secretAccessor role to the specified service account(s) for
    all secrets in the given scope.

    Examples:
        \b
        # Grant access to all staging secrets
        secrets-manager grant-access staging --sa bot@project.iam.gserviceaccount.com

        \b
        # Grant access to multiple service accounts
        secrets-manager grant-access staging \\
          --sa bot@project.iam.gserviceaccount.com \\
          --sa deployer@project.iam.gserviceaccount.com

        \b
        # Grant access to project-specific secrets
        secrets-manager grant-access staging.myapp --sa runtime@project.iam.gserviceaccount.com
    """
    try:
        # Load config
        if config:
            os.environ["SECRETS_CONFIG_PATH"] = config

        manager = SecretsManager()

        # Parse target
        env, project, secret = parse_target(target)

        if secret:
            console.print(
                "[red]✗ Error:[/red] grant-access works on environment or project level, not individual secrets",
                style="bold red",
            )
            console.print(
                "Use 'secrets-manager set <target> --value ... --grant ...' for individual secrets"
            )
            raise typer.Exit(code=1)

        # Show what will be affected
        target_str = f"{env}.{project}" if project else env
        scope = f"project '{project}' in environment '{env}'" if project else f"environment '{env}'"

        console.print(f"[bold]Will grant access to all secrets in {scope}[/bold]")
        console.print(f"Service accounts:")
        for sa in service_account:
            console.print(f"  - {sa}")

        # List affected secrets
        with console.status(f"[bold green]Finding secrets..."):
            secrets = manager.list_secrets(env=env, project=project)

        console.print(f"\nAffected secrets ({len(secrets)}):")
        for name, _ in secrets[:10]:  # Show first 10
            console.print(f"  - {name}")
        if len(secrets) > 10:
            console.print(f"  ... and {len(secrets) - 10} more")

        # Confirm
        if not force:
            console.print()
            confirm = typer.confirm(
                f"Grant access to {len(service_account)} service account(s) for {len(secrets)} secret(s)?"
            )
            if not confirm:
                console.print("Cancelled")
                raise typer.Exit(code=0)

        # Grant access
        with console.status(f"[bold green]Granting access..."):
            result = manager.grant_access_bulk(
                env=env, service_accounts=service_account, project=project
            )

        console.print(
            f"[green]✓[/green] Granted access to {result['secrets_updated']} secrets "
            f"for {result['service_accounts']} service account(s)"
        )

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show version information."""
    from . import __version__

    console.print(f"Botmaro Secrets Manager v{__version__}")


if __name__ == "__main__":
    app()
