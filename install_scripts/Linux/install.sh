#!/usr/bin/env bash
set -e

APP_NAME="Auto-Meeting-Subs"
APP_ID="auto-meeting-subs"
INSTALL_DIR="$HOME/.local/share/$APP_ID"
BIN_DIR="$HOME/.local/bin"
DESKTOP_FILE="$HOME/.local/share/applications/$APP_ID.desktop"
PYTHON_VERSION="3.10.11"
PYTHON_PREFIX="$INSTALL_DIR/python"
PYTHON_BIN="$PYTHON_PREFIX/bin/python3.10"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing $APP_NAME..."

install_python() {
    echo "Installing isolated Python $PYTHON_VERSION..."

    # Install build dependencies
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y build-essential libssl-dev zlib1g-dev \
            libncurses5-dev libffi-dev libsqlite3-dev \
            libbz2-dev libreadline-dev wget curl

    elif command -v dnf &> /dev/null; then
        sudo dnf install -y gcc make bzip2 bzip2-devel zlib-devel libffi-devel readline-devel sqlite-devel wget xz-devel

    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm base-devel openssl zlib \
            bzip2 libffi readline sqlite wget

    else
        echo "Unsupported distro for automatic build."
        exit 1
    fi

    mkdir -p "$INSTALL_DIR/src"
    cd "$INSTALL_DIR/src"

    wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz
    tar -xzf Python-$PYTHON_VERSION.tgz
    cd Python-$PYTHON_VERSION

    ./configure --prefix="$PYTHON_PREFIX" --enable-optimizations
    make -j$(nproc)
    make install

    echo "Python installed at $PYTHON_PREFIX"
}

# Install Python if missing
if [ ! -x "$PYTHON_BIN" ]; then
    install_python
fi

# Ensure pip exists
"$PYTHON_BIN" -m ensurepip --upgrade
"$PYTHON_BIN" -m pip install --upgrade pip

# Create install directory
mkdir -p "$INSTALL_DIR"

# Copy code folder into install dir
cp -r "$SCRIPT_DIR/code/"* "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/icons/" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/uninstall.sh" "$INSTALL_DIR/"

cd "$INSTALL_DIR"
# Ensure directories exist
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$HOME/.local/share/applications"

# Installing Dependencies
"$PYTHON_BIN" -m pip install -r "$INSTALL_DIR/requirements.txt"

# Create launcher script in ~/.local/bin
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/$APP_ID" << EOF
#!/usr/bin/env bash
"$PYTHON_BIN" "$INSTALL_DIR/main.py" "\$@"
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