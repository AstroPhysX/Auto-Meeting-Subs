#!/usr/bin/env bash
set -e
# ----------------------------
# Crash logging
# ----------------------------
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE}" )" && pwd )"
CRASH_LOG="$SCRIPT_DIR/crash.log"

# Function to log errors
log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$CRASH_LOG"
}

# Trap errors and log them
trap 'log_error "Script failed at line $LINENO with exit code $?"; exit 1' ERR
set -o pipefail

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
OPENSSL_VERSION="3.3.1"
OPENSSL_PREFIX="$APP_INSTALL_DIR/vendor/openssl"

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

    SRC_DIR="$APP_INSTALL_DIR/src"

    mkdir -p "$SRC_DIR"
    cd "$SRC_DIR"

    echo "Downloading OpenSSL $OPENSSL_VERSION..."
    curl -LO https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz
    tar -xzf openssl-$OPENSSL_VERSION.tar.gz
    cd openssl-$OPENSSL_VERSION

    echo "Building vendored OpenSSL..."
    ./Configure darwin64-$(uname -m)-cc shared no-tests \
        --prefix="$OPENSSL_PREFIX" \
        --openssldir="$OPENSSL_PREFIX/ssl"

    make -j$(sysctl -n hw.ncpu)
    make install_sw

    cd "$SRC_DIR"

    # Download Python source
    echo "Downloading Python $PYTHON_VERSION..."
    curl -LO https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz
    tar -xzf Python-$PYTHON_VERSION.tgz
    cd Python-$PYTHON_VERSION

    echo "Building Python against vendored OpenSSL..."
    export LDFLAGS="-L$OPENSSL_PREFIX/lib"
    export CPPFLAGS="-I$OPENSSL_PREFIX/include"
    export PKG_CONFIG_PATH="$OPENSSL_PREFIX/lib/pkgconfig"

    ./configure \
        --prefix="$PYTHON_PREFIX" \
        --enable-optimizations \
        --with-openssl="$OPENSSL_PREFIX"

    make -j$(sysctl -n hw.ncpu)
    make install
    install_name_tool -add_rpath "@executable_path/../lib" "$PYTHON_PREFIX/bin/python3"
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
exit 0