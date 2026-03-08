#include <unistd.h>

int main() {
    execl(
        "PYTHON_BIN_PLACEHOLDER",
        "python",
        "APP_INSTALL_DIR_PLACEHOLDER/main.py",
        NULL
    );

    return 1;
}