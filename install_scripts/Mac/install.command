#!/usr/bin/env bash
set -e

APP_NAME="Auto-Meeting-Subs"
APP_ID="Auto-Meeting-Subs"
APP_INSTALL_DIR="$HOME/.local/share/$APP_ID"
APP_BUNDLE="$HOME/Applications/$APP_NAME.app"
PYTHON_BIN="python3.10"

echo "Installing $APP_NAME..."

install_python() {
    echo "Attempting to install Python 3.10..."
    if command -v brew &> /dev/null; then
        brew install python@3.10
    else
        echo "Homebrew not found. Please install Python 3.10 manually:"
        echo "https://www.python.org/downloads/release/python-310/"
        exit 1
    fi
}

# Check Python
if ! command -v $PYTHON_BIN &> /dev/null; then
    install_python
fi

if ! command -v $PYTHON_BIN &> /dev/null; then
    echo "Python 3.10 installation failed."
    exit 1
fi

# Create app directories
mkdir -p "$APP_INSTALL_DIR"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Copy code and icon
cp -r code/* "$APP_INSTALL_DIR/"
cp "$INSTALL_DIR/icons/mac.icns" "$APP_BUNDLE/Contents/Resources/AppIcon.icns"

# Create virtual environment
cd "$APP_INSTALL_DIR"
$PYTHON_BIN -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Create launcher script inside the .app bundle
LAUNCHER="$APP_BUNDLE/Contents/MacOS/launch.sh"
cat > "$LAUNCHER" << EOF
#!/usr/bin/env bash
osascript -e 'tell application "Terminal" to do script "source \"$APP_INSTALL_DIR/venv/bin/activate\" && python \"$APP_INSTALL_DIR/main.py\" "'
EOF

chmod +x "$LAUNCHER"

# Create Info.plist
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
    <string>launch.sh</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon.icns</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

echo "Installation complete!"
echo "You can now launch $APP_NAME from Applications or Finder."