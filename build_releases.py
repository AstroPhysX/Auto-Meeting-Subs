#!/usr/bin/env python3
import shutil
import os
from pathlib import Path

# ----------------------
# Configuration
# ----------------------
VERSION = "1.0"  # Update this for each release
REPO_ROOT = Path(__file__).parent.resolve()

CODE_DIR = REPO_ROOT / "code"
ICON_DIR = REPO_ROOT / "icons"

PLATFORMS = {
    "linux": {
        "folder_name": "Linux",
        "installers": ["install.sh", "uninstall.sh"],
        "zip_name": f"Auto-Meeting-Subs-linux-v{VERSION}.zip"
    },
    "mac": {
        "folder_name": "Mac",
        "installers": ["install.command", "uninstall.command"],
        "zip_name": f"Auto-Meeting-Subs-mac-v{VERSION}.zip"
    },
    "windows": {
        "folder_name": "Windows",
        "installers": ["install.ps1", "uninstall.ps1"],
        "zip_name": f"Auto-Meeting-Subs-windows-v{VERSION}.zip"
    }
}

RELEASE_DIR = REPO_ROOT / "release_zips"
RELEASE_DIR.mkdir(exist_ok=True)

# ----------------------
# Function to build zip
# ----------------------
def build_zip(platform, config):
    temp_dir = REPO_ROOT / f"temp_{platform}"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    # Copy installers
    platform_dir = REPO_ROOT / "install_scripts" / config["folder_name"]
    for installer in config["installers"]:
        shutil.copy(platform_dir / installer, temp_dir)

    # Copy code folder
    shutil.copytree(CODE_DIR, temp_dir / "code")

    shutil.copytree(ICON_DIR, temp_dir/ "icons")

    # Create zip
    zip_path = RELEASE_DIR / config["zip_name"]
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_path).replace(".zip",""), 'zip', temp_dir)

    # Clean up temp dir
    shutil.rmtree(temp_dir)

    print(f"[+] {platform} zip created: {zip_path}")

# ----------------------
# Main
# ----------------------
def main():
    print("Building release zips for all platforms...\n")
    for platform, config in PLATFORMS.items():
        build_zip(platform, config)
    print("\nAll zips built successfully in 'release_zips/' folder.")

if __name__ == "__main__":
    main()