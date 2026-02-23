#!/usr/bin/env bash
set -e

APP_NAME="Auto-Meeting-Subs"
APP_ID="Auto-Meeting-Subs"
APP_INSTALL_DIR="$HOME/.local/share/$APP_ID"
APP_BUNDLE="$HOME/Applications/$APP_NAME.app"

echo "Uninstalling $APP_NAME..."

rm -rf "$APP_INSTALL_DIR"
rm -rf "$APP_BUNDLE"

echo "Uninstalled successfully."