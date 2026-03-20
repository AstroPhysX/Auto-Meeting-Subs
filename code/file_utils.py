import os
import platform
import shutil
import subprocess
import filetype
import json
import ssl, certifi
from pathlib import Path
from datetime import datetime
from ffmpeg_utils import install_ffmpeg

def setup_app_environment():
    if platform.system() == "Windows":
        base_dir = Path(os.getenv("LOCALAPPDATA"))
    else:
        base_dir = Path.home() / ".local" / "share"

    #turns on urllib.requests used to download ffmpeg
    ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

    appdata_dir = base_dir / "auto-meeting-subs"
    appdata_dir.mkdir(parents=True, exist_ok=True)

    # Create subfolders
    nltk_dir = appdata_dir / "nltk_data"
    torch_dir = appdata_dir / "torch_cache"
    hf_dir = appdata_dir / "huggingface"
    pyannote_dir = appdata_dir / "pyannote"

    import torch
    torch.hub.set_dir(str(torch_dir))

    for d in [nltk_dir, torch_dir, hf_dir, pyannote_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Set environment variables
    os.environ["NLTK_DATA"] = str(nltk_dir)
    os.environ["TORCH_HOME"] = str(torch_dir)
    os.environ["HF_HOME"] = str(hf_dir)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(hf_dir / "hub")
    os.environ["DATASETS_CACHE"] = str(hf_dir / "datasets")
    os.environ["PYANNOTE_CACHE"] = str(pyannote_dir)
    

    jit_kernel_dir = torch_dir / "kernels"
    jit_kernel_dir.mkdir(parents=True, exist_ok=True)

    system = platform.system()
    if system in ["Linux", "Darwin"]:
        default_jit_cache = Path.home() / ".cache/torch/kernels"
        if default_jit_cache.exists():
            if default_jit_cache.is_dir() and not default_jit_cache.is_symlink():
                shutil.rmtree(default_jit_cache)
            else:
                default_jit_cache.unlink()
        default_jit_cache.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(jit_kernel_dir, default_jit_cache)  # symlink for Linux/mac
    elif system == "Windows":
        # Windows: use a directory junction
        import subprocess
        default_jit_cache = Path(os.getenv("LOCALAPPDATA")) / "torch" / "kernels"
        if default_jit_cache.exists():
            if default_jit_cache.is_dir():
                subprocess.run(["powershell", "-Command", f"Remove-Item -Path '{default_jit_cache}' -Recurse -Force"], shell=True)
            else:
                print("The path exists but is not a directory or symlink.")
        default_jit_cache.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cmd", "/c", "mklink", "/J", str(default_jit_cache), str(jit_kernel_dir)], shell=True)
        
    # Install FFmpeg inside the same function
    ffmpeg_path = install_ffmpeg(appdata_dir)

    # Make it globally accessible in this session
    os.environ["FFMPEG_PATH"] = str(ffmpeg_path)
    os.environ["FFPROBE_PATH"] = str(ffmpeg_path.parent / "ffprobe")
    os.environ["PATH"] = str(ffmpeg_path.parent) + os.pathsep + os.environ.get("PATH", "")

    return appdata_dir

# Function to determine if file is Audio or Video
def audio_or_video(file):
    kind = filetype.guess(file)
    if kind is None:
        return 'unknown'
    elif kind.mime.startswith('video'):
        return 'video'
    elif kind.mime.startswith('audio'):
        return 'audio'
    else:
        return 'unknown'
"""    
# Function to get the file's date from its metadata
def get_creation_date(file_path):
    
    Returns the creation datetime from file metadata if available,
    otherwise falls back to filesystem modification time.
    
    try:
        probe = ffmpeg.probe(file_path)
        # Most containers store this under 'format' -> 'tags' -> 'creation_time'
        creation_time = probe['format']['tags'].get('creation_time')
        if creation_time:
            # ffmpeg gives ISO 8601 format, convert to timestamp
            from datetime import datetime
            dt = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
            return dt.timestamp()
    except Exception as e:
        print(f"Warning: Could not read creation_time from metadata: {e}")
    
    # Fallback
    return os.path.getmtime(file_path)
"""

# Function to get the file's date from its metadata without ffmpeg-python
def get_creation_date(file_path):
    """
    Returns the creation datetime from file metadata if available,
    otherwise falls back to filesystem modification time.
    """

    try:
        cmd = ["ffprobe","-v", "quiet","-print_format", "json","-show_format",file_path]

        result = subprocess.run(cmd,capture_output=True,text=True,check=True)

        metadata = json.loads(result.stdout)

        creation_time = (metadata
            .get("format", {})
            .get("tags", {})
            .get("creation_time")
        )

        if creation_time:
            dt = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
            return dt.timestamp()

    except Exception as e:
        print(f"Warning: Could not read creation_time from metadata: {e}")

    # Fallback
    return os.path.getmtime(file_path)

def generate_filename(config_path, date_obj):
    config = configparser.ConfigParser()
    config.read(config_path)

    template = config["format"]["filename"]
    return date_obj.strftime(template)
    