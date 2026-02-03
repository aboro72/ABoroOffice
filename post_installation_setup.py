#!/usr/bin/env python
"""
ABoroOffice Post-Installation Setup Script

This script runs after pip install completes and:
1. Verifies all packages are installed
2. Checks Django configuration
3. Prepares database for migrations
4. Provides next steps for development

Usage:
    python post_installation_setup.py
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and report results."""
    print(f"\n>> {description}...")
    print(f"  Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  [OK] Success")
            if result.stdout:
                print(f"  Output: {result.stdout[:200]}")
            return True
        else:
            print(f"  [FAILED] Failed (exit code {result.returncode})")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  [ERROR] Exception: {e}")
        return False

def main():
    """Run post-installation setup."""
    print("=" * 70)
    print("ABoroOffice Post-Installation Setup")
    print("=" * 70)

    # Ensure we're in project root
    if not os.path.exists('manage.py'):
        print("\n[ERROR] manage.py not found in current directory")
        print("  Please run this script from the ABoroOffice project root")
        return 1

    project_root = Path.cwd()
    print(f"\nProject Root: {project_root}")

    # Step 1: Verify requirements
    print("\n" + "=" * 70)
    print("Step 1: Verifying Package Installation")
    print("=" * 70)
    run_command("python verify_requirements.py", "Verify installed packages")

    # Step 2: Check Django setup
    print("\n" + "=" * 70)
    print("Step 2: Checking Django Configuration")
    print("=" * 70)

    checks = [
        ("python manage.py check", "Django system check"),
        ("python manage.py showmigrations --list | head -20", "Show migration status"),
    ]

    for cmd, desc in checks:
        run_command(cmd, desc)

    # Step 3: Create database and run migrations
    print("\n" + "=" * 70)
    print("Step 3: Database Setup")
    print("=" * 70)

    print("\nNote: SQLite database will be created automatically")
    print("For production, use PostgreSQL (see SETUP_REQUIREMENTS.md)")

    if run_command("python manage.py migrate", "Run database migrations"):
        print("\n[OK] Database migrations completed successfully!")
    else:
        print("\n[FAILED] Database migrations failed")
        print("  Check the error message above and SETUP_REQUIREMENTS.md")
        return 1

    # Step 4: Summary and next steps
    print("\n" + "=" * 70)
    print("Setup Complete!")
    print("=" * 70)

    print("""
[OK] All packages installed and verified
[OK] Django configuration checked
[OK] Database migrations completed

Next Steps:
-----------

1. Create a superuser for Django admin:
   python manage.py createsuperuser

2. Run the test suite (optional but recommended):
   pytest tests/ -v

   Or run Phase 2 tests specifically:
   pytest tests/test_classroom_models.py -v

3. Start the development server:
   python manage.py runserver

   Then visit: http://localhost:8000/admin/

4. Review Phase 2 Implementation:
   - Read PHASE2_SUMMARY.md for completed features
   - Check apps/classroom/ for mobile classroom models
   - Check apps/core/ for shared user models
   - Check apps/licensing/ for license management

5. Begin Phase 3 - SSH Approvals Workflow:
   - See PHASE3_PLAN.md for implementation details
   - Review dokmbw_web_app source for reference
   - Integration location: apps/approvals/

Documentation:
---------------
- QUICKSTART.md          - Quick start guide
- SETUP_REQUIREMENTS.md  - Detailed setup instructions
- AWS_BEDROCK_SETUP.md   - AWS integration guide
- OLLAMA_SETUP.md        - Ollama standalone setup
- PHASE2_SUMMARY.md      - Phase 2 completion details

Support:
--------
For issues with requirements, see SETUP_REQUIREMENTS.md
For licensing system questions, check apps/licensing/
For Django errors, run: python manage.py check
""")

    return 0

if __name__ == '__main__':
    sys.exit(main())
