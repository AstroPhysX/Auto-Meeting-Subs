import re
from pathlib import Path
import os
import sys
import shutil
import subprocess
import getpass
import platform
import psutil
import json
import time
from tqdm import tqdm
import requests


# -------------------------
# CONFIG
# -------------------------

CHUNK_SIZE = 4000  # characters per chunk (safe approx)

# -------------------------
# OLLAMA INSTALL CHECK and RUNNING
# -------------------------

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
    print('Starting ollama')
    system = platform.system()

    if system == "Linux":
        password = getpass.getpass("Enter your sudo password to start Ollama: ")
        cmd = ["sudo", "-S", "systemctl", "start", "ollama"]
        subprocess.run(cmd, input=(password + "\n").encode(), check=True)
        print("Ollama service started.")
    else:
        # macOS and Windows
        subprocess.Popen(["ollama", "serve"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

def wait_for_ollama(timeout=30):
    start = time.time()

    while time.time() - start < timeout:
        if is_ollama_running():
            print(">Ollama server is ready.")
            return
        time.sleep(1)

    raise RuntimeError("Ollama did not start in time.")

if not is_ollama_installed():
    install_ollama()

if not is_ollama_running():
    print(">Starting Ollama...")
    start_ollama()

wait_for_ollama()

import ollama

# -------------------------
# HARDWARE DETECTION
# -------------------------

def select_model():
    ram_gb = psutil.virtual_memory().total / (1024**3)

    if ram_gb < 12:
        return "phi3:mini"
    else:
        return "llama3:8b"


# -------------------------
# MODEL CHECK / DOWNLOAD
# -------------------------

def ensure_model(model):
    try:
        ollama.show(model)
        return model
    except ollama.ResponseError as e:
        if e.status_code == 404:
            print(f">Downloading model: {model}")
            progress_bar = None

            for event in ollama.pull(model, stream=True):
                total = event.get("total")
                completed = event.get("completed")
                if total and completed:
                    if progress_bar is None:
                        progress_bar = tqdm(total=total, unit="B", unit_scale=True)
                    progress_bar.n = completed
                    progress_bar.refresh()
                elif "status" in event:
                    print(event["status"])

            if progress_bar:
                progress_bar.close()

    try:
        ollama.show(model)
        return model
    except ollama.ResponseError as e:
        print('Error:', e.error)
    raise RuntimeError(f"Model {model} not found after pull")

# -------------------------------------------------
# Transcript Cleaning
# -------------------------------------------------

def extract_text(file_path, keep_speakers=False, clean_disfluency=True):
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    # ---- Read raw content ----
    if suffix in [".vtt", ".srt", ".txt"]:
        content = file_path.read_text(encoding="utf-8")

    elif suffix == ".tsv":
        lines = file_path.read_text(encoding="utf-8").splitlines()
        content = "\n".join(
            line.split("\t")[-1]
            for line in lines
            if "\t" in line
        )

    elif suffix == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if "segments" in data:
            content = "\n".join(seg.get("text", "") for seg in data["segments"])
        elif "text" in data:
            content = data["text"]
        else:
            raise ValueError("Unrecognized JSON transcript format")

    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    # -------------------------------------------------
    # Remove subtitle artifacts (format-agnostic)
    # -------------------------------------------------
    # Remove WEBVTT header
    content = re.sub(r"WEBVTT", "", content, flags=re.IGNORECASE)

    # Remove timestamps like:
    # 00:00:00.000 --> 00:00:02.000
    # 00:00:00,000 --> 00:00:02,000
    # 00:00.000 --> 00:02.000
    # 00:00 --> 00:02
    content = re.sub(
        r"\d{1,2}:\d{2}(?::\d{2})?[.,]?\d*\s*-->\s*\d{1,2}:\d{2}(?::\d{2})?[.,]?\d*",
        "",
        content
    )

    # Remove standalone timestamps
    content = re.sub(
        r"\b\d{1,2}:\d{2}(?::\d{2})?[.,]?\d*\b",
        "",
        content
    )

    # Remove arrow fragments (broken timestamps)
    content = re.sub(r"-->\s*\d{1,2}:\d{2}(?::\d{2})?[.,]?\d*", "", content)

    # Remove subtitle index numbers (lines that contain only digits)
    content = re.sub(r"^\d+\s*$", "", content, flags=re.MULTILINE)

    # -------------------------------------------------
    # Remove speaker labels if requested
    # -------------------------------------------------
    if not keep_speakers:
        content = re.sub(
            r"\[?speaker[_\s]?\d+\]?:?", 
            "", 
            content, 
            flags=re.IGNORECASE
        )

    # -------------------------------------------------
    # Optional: Clean common stutters / repeated words
    # -------------------------------------------------
    if clean_disfluency:
        # Remove repetitive fillers like "the, uh, the, uh..."
        content = re.sub(r"\b(\w+),?\s+(\1,?\s+)+", r"\1 ", content, flags=re.IGNORECASE)
        # Remove multiple "uh" / "um" sequences
        content = re.sub(r"\b(uh|um|er|ah)(,\s*)+", "", content, flags=re.IGNORECASE)

    # -------------------------------------------------
    # Normalize whitespace
    # -------------------------------------------------
    content = re.sub(r"\n\s*\n", "\n", content)  # remove repeated blank lines
    content = re.sub(r"[ \t]+", " ", content)   # normalize spaces

    return content.strip()
# -------------------------
# CHUNKING
# -------------------------

def chunk_text(text, size=CHUNK_SIZE):
    return [text[i:i+size] for i in range(0, len(text), size)]

def chunk_by_speakers(transcript, turns_per_chunk=10):
    chunks = []
    current = []
    for i, (speaker, text) in enumerate(transcript):
        current.append(f"{speaker}: {text}")
        if (i + 1) % turns_per_chunk == 0:
            chunks.append("\n".join(current))
            current = []
    if current:
        chunks.append("\n".join(current))
    return chunks

def chunk_by_sentences(text, max_chars=2000):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""

    for s in sentences:
        if len(current) + len(s) + 1 > max_chars:
            chunks.append(current.strip())
            current = s
        else:
            current += " " + s

    if current:
        chunks.append(current.strip())

    return chunks
# -------------------------
# OLLAMA CALL
# -------------------------

def generate(model, prompt):
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert meeting summarizer."},
            {"role": "user", "content": prompt}
        ],
        stream=False
    )
    return response["message"]["content"]


# -------------------------
# SUMMARIZATION PIPELINE
# -------------------------

def summarize_transcript(transcript, model):
    chunks = chunk_by_sentences(transcript)

    summaries = []

    for i, chunk in enumerate(chunks):
        print(f"Summarizing chunk {i+1}/{len(chunks)}")

        prompt = f"""
Summarize the following transcript section clearly and concisely.
Extract:
- Key decisions
- Action items
- Important discussion points

Transcript:
{chunk}
"""
        summary = generate(model, prompt)
        summaries.append(summary)

    combined = "\n\n".join(summaries)

    final_prompt = f"""
Combine the following section summaries into a cohesive meeting summary.
Provide:
- Executive summary
- Notes/Important Discussion Points
- Decisions made (if any)
- Action items
- Open questions (if any)

Section Summaries:
{combined}
"""

    final_summary = generate(model, final_prompt)
    return final_summary


# -------------------------
# MAIN
# -------------------------

def main(transcript_path):

    model = select_model()
    print(f">Selected model: {model}")

    model = ensure_model(model)

    transcript = extract_text(transcript_path, keep_speakers=True)

    final_summary = summarize_transcript(transcript, model)

    output_path = Path(transcript_path).with_suffix(".summary.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_summary)

    print(f"\n>Summary saved to: {output_path}")

Trandscript_Path="/home/aleluc/Videos/AutoMeetingSubsTesting/Meeting 2026.01.29.vtt"
main(Trandscript_Path)