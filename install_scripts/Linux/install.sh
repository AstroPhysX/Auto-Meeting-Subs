#!/usr/bin/env bash
set -e

APP_NAME="Auto-Meeting-Subs"
APP_ID="auto-meeting-subs"
INSTALL_DIR="$HOME/.local/share/$APP_ID"
BIN_DIR="$HOME/.local/bin"
DESKTOP_FILE="$HOME/.local/share/applications/$APP_ID.desktop"
PYTHON_BIN=$(command -v python3.10 || command -v python3 || true)

echo "Installing $APP_NAME..."

install_python() {
    echo "Attempting to install Python 3.10..."

    if command -v dnf &> /dev/null; then
        sudo dnf install -y python3.10

    elif command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y python3.10

    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm python310

    elif command -v zypper &> /dev/null; then
        sudo zypper install -y python310 

    elif command -v apk &> /dev/null; then
        sudo apk add --no-cache python3=3.10*

    else
        echo "Unsupported distribution."
        echo "Please install Python 3.10 manually."
        exit 1
    fi
}
# Check Python
PY_VER=$($PYTHON_BIN -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo "0.0.0")

if [[ "$PY_VER" != 3.10* ]]; then
    echo "Python 3.10 not found. Installing..."
    install_python

    # Recheck after installation
    PYTHON_BIN=$(command -v python3.10 || command -v python3 || true)
    PY_VER=$($PYTHON_BIN -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo "0.0.0")

    if [[ "$PY_VER" != 3.10* ]]; then
        echo "Python 3.10 installation failed."
        exit 1
    fi
fi

# Create install directory
mkdir -p "$INSTALL_DIR"

# Copy code folder into install dir
cp -r code/* "$INSTALL_DIR/"
cp -r icons/* "$INSTALL_DIR/"

# Copy uninstall script to install directory
if [ -f "../uninstall.sh" ]; then
    cp ../uninstall.sh "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/uninstall.sh"
else
    echo "Warning: uninstall.sh not found in install_scripts folder."
fi

cd "$INSTALL_DIR"
# Ensure directories exist
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$HOME/.local/share/applications"

# Create virtual environment
$PYTHON_BIN -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Create launcher script in ~/.local/bin
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/$APP_ID" << EOF
#!/usr/bin/env bash
source "$INSTALL_DIR/venv/bin/activate"
python "$INSTALL_DIR/main.py" "\$@"
EOF

chmod +x "$BIN_DIR/$APP_ID"

# Create desktop entry
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=$APP_NAME
Exec=$BIN_DIR/$APP_ID
Icon=$INSTALL_DIR/icons/linux.png
Type=Application
Categories=Utility;
Terminal=true
EOF

# Refresh desktop database so it appears in menus immediately
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications || true
fi

echo "Installation complete!"
echo "You can now launch $APP_NAME from your application menu or with the command '$APP_ID'."