import shutil
import subprocess
import platform
import requests
import time
import getpass

def is_ollama_installed():
    return shutil.which("ollama") is not None


def install_ollama():
    system = platform.system()

    print(">Installing Ollama...")

    if system == "Darwin" or system == "Linux":
        subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
    elif system == "Windows":
        subprocess.run(["powershell", "-Command", "irm https://ollama.com/install.ps1 | iex"])
    else:
        raise Exception("Unsupported OS")


def is_ollama_running():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        return r.status_code == 200
    except:
        return False

def start_ollama():
    print('>Starting ollama')
    system = platform.system()

    if system == "Linux":
        password = getpass.getpass("Enter your sudo password to start Ollama: ")
        cmd = ["sudo", "-S", "systemctl", "start", "ollama"]
        subprocess.run(cmd, input=(password + "\n").encode(), check=True)
        print(">Ollama service started.")
    else:
        # macOS and Windows
        subprocess.Popen(["ollama", "serve"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

def wait_for_ollama(timeout=30):
    start = time.time()

    while time.time() - start < timeout:
        if is_ollama_running():
            #print(">Ollama server is ready.")
            return
        time.sleep(1)

    raise RuntimeError(">Ollama did not start in time.")

def ollama_checks():
    if not is_ollama_installed():
        install_ollama()

    if not is_ollama_running():
        print(">Starting Ollama...")
        start_ollama()

    wait_for_ollama()

