#!/usr/bin/env bash
{
# ----------------------------
# Configuration
# ----------------------------
APP_NAME="Auto-Meeting-Subs"
APP_ID="auto-meeting-subs"
APP_INSTALL_DIR="$HOME/.local/share/$APP_ID"
PYTHON_VERSION="3.10.19"
PYTHON_PREFIX="$APP_INSTALL_DIR/python"
PYTHON_BIN="$PYTHON_PREFIX/bin/Python${PYTHON_VERSION%.*}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENSSL_VERSION="3.3.1"
OPENSSL_PREFIX="$APP_INSTALL_DIR/vendor/openssl"

# Paths inside the .app bundle
APP_BUNDLE="$HOME/Applications/$APP_NAME.app"
APP_MACOS_DIR="$APP_BUNDLE/Contents/MacOS"
APP_RESOURCES_DIR="$APP_BUNDLE/Contents/Resources"
DESKTOP_ICON="$APP_RESOURCES_DIR/AppIcon.icns"

LOG_FILE="$SCRIPT_DIR/install.log"
mkdir -p "$(dirname "$LOG_FILE")"
: > "$LOG_FILE"   # clear old log

spinner() {
  local pid=$1
  local spin='-\|/'
  local i=0

  while kill -0 "$pid" 2>/dev/null; do
    i=$(( (i + 1) % 4 ))
    printf "\r⏳ Working... %s" "${spin:$i:1}"
    sleep 0.1
  done

  printf "\r"
}

run_step() {
  local label="$1"
  shift

  echo "▶ $label..."

  # Run command in background, log everything
  "$@" >>"$LOG_FILE" 2>&1 &
  local pid=$!

  spinner "$pid"

  wait "$pid"
  local status=$?
  
  printf "\r\033[K"

  if [ $status -ne 0 ]; then
    if [ $status -ge 128 ]; then
      echo "❌ Failed: $label (crashed: signal $((status - 128)))"
    else
      echo "❌ Failed: $label (exit code: $status)"
    fi
    echo "   See log: $LOG_FILE"
    exit 1
  fi

  echo "✅ Done"
}
echo "Installing $APP_NAME..."

# ----------------------------
# Install isolated Python if missing
# ----------------------------
install_python() {
    # Ensure build tools exist
    if ! xcode-select -p &>/dev/null; then
        echo "Xcode Command Line Tools not found. Installing..."
        xcode-select --install || true
        read -rsn1 -p "Press any key to continue once xcode-select has been installed..."   
    fi

    SRC_DIR="$APP_INSTALL_DIR/src"

    mkdir -p "$SRC_DIR"
    cd "$SRC_DIR"

    run_step "Downloading OpenSSL $OPENSSL_VERSION..." curl -LO https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz
    tar -xzf openssl-$OPENSSL_VERSION.tar.gz
    cd openssl-$OPENSSL_VERSION

    run_step "Configuring OpenSSL" ./Configure darwin64-$(uname -m)-cc shared no-tests \
        --prefix="$OPENSSL_PREFIX" \
        --openssldir="$OPENSSL_PREFIX/ssl"

    run_step "Building OpenSSL" make -j$(sysctl -n hw.ncpu)
    run_step "Installing isolated OpennSSL" make install_sw

    cd "$SRC_DIR"

    # Download Python source
    run_step "Downloading Python $PYTHON_VERSION..." curl -LO https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz
    tar -xzf Python-$PYTHON_VERSION.tgz
    cd Python-$PYTHON_VERSION

    #Building Python against vendored OpenSSL...
    export LDFLAGS="-L$OPENSSL_PREFIX/lib"
    export CPPFLAGS="-I$OPENSSL_PREFIX/include"
    export PKG_CONFIG_PATH="$OPENSSL_PREFIX/lib/pkgconfig"

    run_step "Configuring Python" ./configure \
        --prefix="$PYTHON_PREFIX" \
        --enable-optimizations \
        --with-openssl="$OPENSSL_PREFIX"

    run_step "Building Python" make -j$(sysctl -n hw.ncpu)
    run_step "Installing Python" make install
    install_name_tool -add_rpath "@executable_path/../lib" "$PYTHON_PREFIX/bin/python3"
    echo "Python installed at $PYTHON_PREFIX"
}

if [ ! -x "$PYTHON_BIN" ]; then
    install_python
fi

# Ensure pip exists and upgrade
run_step "Checking pip installed" "$PYTHON_BIN" -m ensurepip --upgrade
run_step "Updating pip..." "$PYTHON_BIN" -m pip install --upgrade pip

# ----------------------------
# Prepare app directories
# ----------------------------
mkdir -p "$APP_INSTALL_DIR" "$APP_MACOS_DIR" "$APP_RESOURCES_DIR"

# Copy code and icons
cp -r "$SCRIPT_DIR/code/"* "$APP_INSTALL_DIR/"
cp "$SCRIPT_DIR/icons/mac.icns" "$DESKTOP_ICON"

# Moving the uninstall script
if [ -f "$SCRIPT_DIR/uninstall.command" ]; then
    cp "$SCRIPT_DIR/uninstall.command" "$APP_INSTALL_DIR/"
    chmod +x "$APP_INSTALL_DIR/uninstall.command"
fi


# ----------------------------
# Install Python dependencies
# ----------------------------
run_step "Downloading and Installing Python Modules" "$PYTHON_BIN" -m pip install -r "$APP_INSTALL_DIR/requirements.txt"

# ----------------------------
# Create launcher script inside .app
# ----------------------------
EXECUTABLE="$APP_MACOS_DIR/$APP_NAME"
cat > "$EXECUTABLE" << EOF
#!/usr/bin/env bash
exec "$PYTHON_BIN" "$APP_INSTALL_DIR/main.py" "\$@"
EOF

chmod +x "$EXECUTABLE"

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
    <string>$APP_NAME</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon.icns</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

echo "Installation complete!"
echo "To uninstall, navigate to '$APP_INSTALL_DIR' and run the uninstall script in there. Otherwise you can simply run the uninstaller in the zip."
echo "You can now launch $APP_NAME from Applications or Finder."
} || {
  echo " ❌ Failed, some error occurred during installation"
  echo "   See log: $LOG_FILE"
  echo "   If you want to reattempt to install the program after a fix, I highly recommend that you run the uninstall script prior to attempting to run the install script again."
}
exit 0