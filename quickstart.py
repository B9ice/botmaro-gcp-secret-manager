#!/usr/bin/env python3
"""
Quick start script for Botmaro Secrets Manager.
This script helps you get started with the secrets manager.
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and display its output."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}\n")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    return result.returncode == 0


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         Botmaro Secrets Manager - Quick Start            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")

    # Check if already installed
    result = subprocess.run(
        "secrets-manager version",
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("⚠️  Secrets Manager not installed. Installing now...")
        if not run_command("pip install -e .", "Installing Botmaro Secrets Manager"):
            print("❌ Installation failed. Please check errors above.")
            sys.exit(1)
    else:
        print("✅ Secrets Manager already installed")
        print(f"   {result.stdout.strip()}")

    # Check for secrets.yml
    if not Path("secrets.yml").exists():
        if Path("secrets.example.yml").exists():
            print("\n📝 Creating secrets.yml from example...")
            subprocess.run("cp secrets.example.yml secrets.yml", shell=True)
            print("✅ Created secrets.yml")
            print("   Please edit this file with your configuration")
        else:
            print("\n⚠️  secrets.example.yml not found")
            print("   Please create a secrets.yml configuration file")

    # Check GCP authentication
    print("\n🔑 Checking Google Cloud authentication...")
    result = subprocess.run(
        "gcloud auth application-default print-access-token",
        shell=True,
        capture_output=True
    )

    if result.returncode != 0:
        print("⚠️  Not authenticated to Google Cloud")
        print("\nRun: gcloud auth application-default login")
    else:
        print("✅ Authenticated to Google Cloud")

    # Show next steps
    print(f"""
{'='*60}
  Next Steps
{'='*60}

1. Edit secrets.yml with your configuration:
   - Set your GCP project IDs
   - Define your environments
   - List required secrets

2. Set your first secret:
   secrets-manager set staging.API_KEY --value "your-key-here"

3. Bootstrap an environment:
   secrets-manager bootstrap staging --verbose

4. Check the documentation:
   - README: README.secrets-manager.md
   - Setup Guide: SETUP.secrets-manager.md

5. Run 'secrets-manager --help' for more commands

{'='*60}
""")


if __name__ == "__main__":
    main()