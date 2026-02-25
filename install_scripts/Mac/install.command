#!/usr/bin/env bash
set -e

# ----------------------------
# Configuration
# ----------------------------
APP_NAME="Auto-Meeting-Subs"
APP_ID="auto-meeting-subs"
APP_INSTALL_DIR="$HOME/.local/share/$APP_ID"
APP_BUNDLE="$HOME/Applications/$APP_NAME.app"
PYTHON_VERSION="3.10.11"
PYTHON_PREFIX="$APP_INSTALL_DIR/python"
PYTHON_BIN="$PYTHON_PREFIX/bin/python3.10"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Paths inside the .app bundle
APP_MACOS_DIR="$APP_BUNDLE/Contents/MacOS"
APP_RESOURCES_DIR="$APP_BUNDLE/Contents/Resources"
DESKTOP_ICON="$APP_RESOURCES_DIR/AppIcon.icns"

echo "Installing $APP_NAME..."

# ----------------------------
# Install isolated Python if missing
# ----------------------------
install_python() {
    echo "Installing isolated Python $PYTHON_VERSION..."

    # Ensure build tools exist
    if ! xcode-select -p &>/dev/null; then
        echo "Xcode Command Line Tools not found. Installing..."
        xcode-select --install || true
    fi

    mkdir -p "$APP_INSTALL_DIR/src"
    cd "$APP_INSTALL_DIR/src"

    # Download Python source
    curl -LO https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz
    tar -xzf Python-$PYTHON_VERSION.tgz
    cd Python-$PYTHON_VERSION

    # Build and install to isolated prefix
    ./configure --prefix="$PYTHON_PREFIX" --enable-optimizations
    make -j$(sysctl -n hw.ncpu)
    make install

    echo "Python installed at $PYTHON_PREFIX"
}

if [ ! -x "$PYTHON_BIN" ]; then
    install_python
fi

# Ensure pip exists and upgrade
"$PYTHON_BIN" -m ensurepip --upgrade
"$PYTHON_BIN" -m pip install --upgrade pip

# ----------------------------
# Prepare app directories
# ----------------------------
mkdir -p "$APP_INSTALL_DIR" "$APP_MACOS_DIR" "$APP_RESOURCES_DIR"

# Copy code and icons
cp -r "$SCRIPT_DIR/code/"* "$APP_INSTALL_DIR/"
cp "$SCRIPT_DIR/icons/mac.icns" "$DESKTOP_ICON"
if [ -f "$SCRIPT_DIR/uninstall.command" ]; then
    cp "$SCRIPT_DIR/uninstall.command" "$APP_INSTALL_DIR/"
    chmod +x "$APP_INSTALL_DIR/uninstall.command"
fi


# ----------------------------
# Install Python dependencies
# ----------------------------
"$PYTHON_BIN" -m pip install -r "$APP_INSTALL_DIR/requirements.txt"

# ----------------------------
# Create launcher script inside .app
# ----------------------------
LAUNCHER="$APP_MACOS_DIR/launch.command"
cat > "$LAUNCHER" << EOF
#!/usr/bin/env bash
"$PYTHON_BIN" "$APP_INSTALL_DIR/main.py" "\$@"
EOF
chmod +x "$LAUNCHER"

# ----------------------------
# Create Info.plist
# ----------------------------
cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.$APP_ID</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>launch.command</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon.icns</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

echo "Installation complete!"
echo "You can now launch $APP_NAME from Applications or Finder."
echo "To uninstall, remove '$APP_INSTALL_DIR' and '$APP_BUNDLE'."