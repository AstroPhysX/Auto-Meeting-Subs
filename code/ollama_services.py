import shutil
import subprocess
import platform
import requests
import time
import getpass
import json

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

def get_loaded_models() -> list:
    """Get all models currently loaded in VRAM."""
    try:
        response = requests.get("http://localhost:11434/api/ps")
        data = response.json()
        
        # Extract model names
        models = [model["name"] for model in data.get("models", [])]
        return models
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def start_ollama(password=None):
    system = platform.system()
    if system == "Linux":
        if password is None:
            password = getpass.getpass("[sudo] Enter your sudo password to allow ollama to be restarted: ")
        cmd = ["sudo", "-S", "systemctl", "start", "ollama"]
        subprocess.run(cmd, input=(password + "\n").encode(), check=True)
        print(">Ollama service started.")
        return password
    else:
        # macOS and Windows
        subprocess.Popen(["ollama", "serve"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return None

def kill_ollama(password=None):
    print(">Stopping ollama")
    system = platform.system()

    try:
        if system == "Linux":
            if password is None:
                password = getpass.getpass("[sudo] Enter your sudo password to allow ollama to be restarted: ")
            cmd = ["sudo", "-S", "systemctl", "stop", "ollama"]
            subprocess.run(cmd, input=(password + "\n").encode(), check=True)
            print(">Ollama service stopped.")
            return password

        elif system == "Darwin":  # macOS
            subprocess.run(["pkill", "-f", "ollama"], check=False)
            print(">Ollama process killed (macOS).")

        elif system == "Windows":
            subprocess.run(["taskkill", "/IM", "ollama.exe", "/F"], check=False)
            print(">Ollama process killed (Windows).")

        else:
            print(">Unsupported OS:", system)

    except Exception as e:
        print(">Failed to stop Ollama:", e)
    return None

def reload_models(model_list: list, password) -> None:
    """Load multiple models into VRAM."""
    start_ollama(password)
    try:
        for model in model_list:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": " ",
                    "stream": False,
                    "keep_alive": 3600  # Keep loaded for 1 hour
                }
            )
            response.raise_for_status()
            print(f"Model '{model}' loaded into VRAM")
    except Exception as e:
        print(f"Error loading models: {e}")

def wait_for_ollama(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        if is_ollama_running():
            #print(">Ollama server is ready.")
            return
        time.sleep(1)

    raise RuntimeError(">Ollama did not start in time.")

def ollama_checks():
    #Checks if ollama is installed
    if not is_ollama_installed():
        install_ollama()
        wait_for_ollama()
    

    # Ollama is NOT already running
    if is_ollama_running():
        print(">Starting Ollama...")
        password = start_ollama()
        ollama_starting_state = "off"
        models = None
    else: # ollama is already running; save running models, and restart
        models = get_loaded_models()
        password = kill_ollama()
        start_ollama(password)
        ollama_starting_state = "on"
    return models, password,ollama_starting_state

