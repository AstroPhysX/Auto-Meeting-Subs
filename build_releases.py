#!/usr/bin/env python3
import shutil
import os
import stat
from pathlib import Path

# ----------------------
# Configuration
# ----------------------
REPO_ROOT = Path(__file__).parent.resolve()

CODE_DIR = REPO_ROOT / "code"
ICON_DIR = REPO_ROOT / "icons"

PLATFORMS = {
    "linux": {
        "folder_name": "Linux",
        "installers": ["install.sh", "uninstall.sh"],
        "zip_name": f"Auto-Meeting-Subs-linux.zip"
    },
    "mac": {
        "folder_name": "Mac",
        "installers": ["install.command", "uninstall.command"],
        "zip_name": f"Auto-Meeting-Subs-mac.zip"
    },
    "windows": {
        "folder_name": "Windows",
        "bat_files": ["install.bat", "uninstall.bat"],
        "ps1_files": ["install.ps1", "uninstall.ps1"],
        "zip_name": f"Auto-Meeting-Subs-windows.zip"
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

    platform_dir = REPO_ROOT / "install_scripts" / config["folder_name"]

    if platform == "windows":
        # Copy .bat files to root of zip
        for bat in config["bat_files"]:
            shutil.copy(platform_dir / bat, temp_dir / bat)

        # Create scripts folder
        scripts_dir = temp_dir / "scripts"
        scripts_dir.mkdir()

        # Copy .ps1 files into scripts/
        for ps1 in config["ps1_files"]:
            shutil.copy(platform_dir / ps1, scripts_dir / ps1)

    else:
        # Linux & Mac installers
        for installer in config["installers"]:
            src = platform_dir / installer
            dst = temp_dir / installer
            shutil.copy(src, dst)

            # Make executable for Linux and Mac
            current_mode = dst.stat().st_mode
            dst.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Copy code folder
    shutil.copytree(CODE_DIR, temp_dir / "code", ignore=lambda dir, contents: [item for item in contents if os.path.isdir(os.path.join(dir, item))])
    
    # Copy icons folder
    shutil.copytree(ICON_DIR, temp_dir / "icons")

    # Create zip
    zip_path = RELEASE_DIR / config["zip_name"]
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_path).replace(".zip",""), 'zip', temp_dir)

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