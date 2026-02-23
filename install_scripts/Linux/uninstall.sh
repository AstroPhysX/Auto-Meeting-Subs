#!/usr/bin/env bash
set -e

APP_ID="auto-meeting-subs"

rm -rf "$HOME/.local/share/$APP_ID"
rm -f "$HOME/.local/bin/$APP_ID"
rm -f "$HOME/.local/share/applications/$APP_ID.desktop"

# Refresh desktop database to remove menu entry
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications
fi

echo "Uninstalled successfully."
echo "This did not uninstall python3.10 or ollama as other app might depend on them"