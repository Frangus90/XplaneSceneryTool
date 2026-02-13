#!/usr/bin/env python3
"""
Build script for X-Plane Scenery Tool.

Features:
- Automatic version bumping (major, minor, patch)
- Changelog parsing for release notes
- PyInstaller executable building
- Optional GitHub release creation

Usage:
    python scripts/build.py                    # Build with current version
    python scripts/build.py --bump patch       # Bump patch version and build
    python scripts/build.py --bump minor       # Bump minor version and build
    python scripts/build.py --bump major       # Bump major version and build
    python scripts/build.py --release          # Build and create GitHub release
    python scripts/build.py --bump patch --release  # Bump, build, and release
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
VERSION_FILE = SRC_DIR / "version.py"
CHANGELOG_FILE = PROJECT_ROOT / "CHANGELOG.md"


def get_current_version() -> str:
    """Read current version from version.py."""
    content = VERSION_FILE.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Could not find __version__ in version.py")
    return match.group(1)


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse version string into tuple of (major, minor, patch)."""
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")
    return tuple(int(p) for p in parts)


def bump_version(current: str, bump_type: str) -> str:
    """Bump version according to bump type."""
    major, minor, patch = parse_version(current)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def update_version_file(new_version: str):
    """Update version.py with new version."""
    content = VERSION_FILE.read_text()

    # Update __version__
    content = re.sub(
        r'__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{new_version}"',
        content
    )

    VERSION_FILE.write_text(content)
    print(f"Updated version.py to {new_version}")


def update_changelog_for_release(version: str):
    """Update CHANGELOG.md: move Unreleased to new version section."""
    content = CHANGELOG_FILE.read_text()
    today = datetime.now().strftime("%Y-%m-%d")

    # Check if there's content under [Unreleased]
    unreleased_pattern = r'## \[Unreleased\]\n(.*?)(?=\n## \[|$)'
    match = re.search(unreleased_pattern, content, re.DOTALL)

    if match:
        unreleased_content = match.group(1).strip()

        if unreleased_content:
            # Replace [Unreleased] section and add new version
            new_section = f"## [Unreleased]\n\n## [{version}] - {today}\n{unreleased_content}"
            content = re.sub(unreleased_pattern, new_section + "\n\n", content, flags=re.DOTALL)
        else:
            # No unreleased changes, just add version header
            content = content.replace(
                "## [Unreleased]",
                f"## [Unreleased]\n\n## [{version}] - {today}"
            )

    CHANGELOG_FILE.write_text(content)
    print(f"Updated CHANGELOG.md for version {version}")


def get_changelog_for_version(version: str) -> str:
    """Extract changelog content for a specific version."""
    content = CHANGELOG_FILE.read_text()

    # Pattern to match version section
    pattern = rf'## \[{re.escape(version)}\][^\n]*\n(.*?)(?=\n## \[|$)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        return match.group(1).strip()

    return "No changelog entry found for this version."


def get_unreleased_changes() -> str:
    """Get changes from Unreleased section."""
    content = CHANGELOG_FILE.read_text()

    pattern = r'## \[Unreleased\]\n(.*?)(?=\n## \[|$)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        changes = match.group(1).strip()
        if changes:
            return changes

    return ""


def clean_build_dirs():
    """Clean previous build artifacts."""
    for dir_path in [DIST_DIR, BUILD_DIR]:
        if dir_path.exists():
            print(f"Cleaning {dir_path}...")
            shutil.rmtree(dir_path)


def build_executable(version: str) -> Path:
    """Build executable using PyInstaller."""
    print("\nBuilding executable with PyInstaller...")

    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # PyInstaller command
    exe_name = f"XPlaneSceneryTool-{version}"
    main_script = SRC_DIR / "main.py"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", exe_name,
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(BUILD_DIR),
        # Add icon if exists
        # "--icon", str(PROJECT_ROOT / "assets" / "icon.ico"),
        # Include data files
        "--add-data", f"{SRC_DIR / 'version.py'};.",
        str(main_script)
    ]

    # Add icon if it exists
    icon_path = PROJECT_ROOT / "assets" / "icon.ico"
    if icon_path.exists():
        cmd.insert(-1, "--icon")
        cmd.insert(-1, str(icon_path))

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        raise RuntimeError("PyInstaller build failed")

    exe_path = DIST_DIR / f"{exe_name}.exe"
    if not exe_path.exists():
        # Try without version in name
        exe_path = DIST_DIR / "XPlaneSceneryTool.exe"

    print(f"\nBuild complete: {exe_path}")
    return exe_path


def create_git_tag(version: str):
    """Create git tag for version."""
    tag = f"v{version}"

    # Check if tag already exists
    result = subprocess.run(
        ["git", "tag", "-l", tag],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )

    if tag in result.stdout:
        print(f"Git tag {tag} already exists")
        return

    # Create tag
    subprocess.run(
        ["git", "tag", "-a", tag, "-m", f"Release {version}"],
        check=True, cwd=PROJECT_ROOT
    )
    print(f"Created git tag: {tag}")


def create_github_release(version: str, exe_path: Path, changelog: str):
    """Create GitHub release using gh CLI."""
    tag = f"v{version}"

    # Check if gh is available
    result = subprocess.run(["gh", "--version"], capture_output=True)
    if result.returncode != 0:
        print("GitHub CLI (gh) not found. Skipping release creation.")
        print("Install from: https://cli.github.com/")
        return

    # Create release notes file
    notes_file = BUILD_DIR / "release_notes.md"
    notes_file.parent.mkdir(parents=True, exist_ok=True)
    notes_file.write_text(f"# X-Plane Scenery Tool v{version}\n\n{changelog}")

    # Push tag first
    print("Pushing git tag...")
    subprocess.run(["git", "push", "origin", tag], cwd=PROJECT_ROOT)

    # Create release
    print(f"Creating GitHub release {tag}...")
    cmd = [
        "gh", "release", "create", tag,
        str(exe_path),
        "--title", f"X-Plane Scenery Tool v{version}",
        "--notes-file", str(notes_file)
    ]

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode == 0:
        print(f"GitHub release created: {tag}")
    else:
        print("Failed to create GitHub release")


def commit_version_changes(version: str):
    """Commit version bump changes."""
    subprocess.run(["git", "add", str(VERSION_FILE), str(CHANGELOG_FILE)], cwd=PROJECT_ROOT)
    subprocess.run(
        ["git", "commit", "-m", f"Bump version to {version}"],
        cwd=PROJECT_ROOT
    )
    print(f"Committed version changes")


def main():
    parser = argparse.ArgumentParser(
        description="Build X-Plane Scenery Tool executable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        help="Bump version before building"
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Create GitHub release after building"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directories before building"
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip building executable (useful for version bump only)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )

    args = parser.parse_args()

    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")

    # Determine new version
    if args.bump:
        new_version = bump_version(current_version, args.bump)
        print(f"New version: {new_version}")

        if args.dry_run:
            print("\n[DRY RUN] Would update version and changelog")
        else:
            # Check for unreleased changes
            unreleased = get_unreleased_changes()
            if not unreleased:
                print("\nWarning: No unreleased changes in CHANGELOG.md")
                response = input("Continue anyway? [y/N]: ")
                if response.lower() != 'y':
                    sys.exit(1)

            update_version_file(new_version)
            update_changelog_for_release(new_version)
            commit_version_changes(new_version)
    else:
        new_version = current_version

    # Clean if requested
    if args.clean:
        if args.dry_run:
            print("\n[DRY RUN] Would clean build directories")
        else:
            clean_build_dirs()

    # Build executable
    if not args.no_build:
        if args.dry_run:
            print(f"\n[DRY RUN] Would build executable for version {new_version}")
            exe_path = DIST_DIR / f"XPlaneSceneryTool-{new_version}.exe"
        else:
            exe_path = build_executable(new_version)
    else:
        exe_path = None

    # Create release
    if args.release:
        changelog = get_changelog_for_version(new_version)

        if args.dry_run:
            print(f"\n[DRY RUN] Would create git tag v{new_version}")
            print(f"[DRY RUN] Would create GitHub release with changelog:")
            print(changelog[:200] + "..." if len(changelog) > 200 else changelog)
        else:
            create_git_tag(new_version)
            if exe_path and exe_path.exists():
                create_github_release(new_version, exe_path, changelog)
            else:
                print("No executable found, skipping GitHub release")

    print("\nDone!")

    # Print summary
    print("\n" + "=" * 50)
    print("BUILD SUMMARY")
    print("=" * 50)
    print(f"Version: {new_version}")
    if exe_path:
        print(f"Executable: {exe_path}")
    if args.release:
        print(f"Git tag: v{new_version}")
        print(f"GitHub release: {'Created' if not args.dry_run else 'Would be created'}")


if __name__ == "__main__":
    main()
