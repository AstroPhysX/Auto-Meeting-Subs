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
from ollama_services import ollama_checks, kill_ollama, start_ollama, is_ollama_running, wait_for_ollama
models_before_ams, password, ollama_starting_state = ollama_checks()
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
            raise ValueError(">Unrecognized JSON transcript format")

    else:
        raise ValueError(f">Unsupported file type: {suffix}")

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
def summarize_pipeline(transcript, model):
    chunks = chunk_by_sentences(transcript)

    summaries = []

    for chunk in tqdm(chunks, desc="Summarizing", unit="chunk"):

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
# MAIN Summarizing function
# -------------------------
def summarize_transcript(transcript_path, dev=False):
    if not is_ollama_running():
        start_ollama(password)
        wait_for_ollama()
    
    model = select_model()
    print(f">Selected model: {model}")

    model = ensure_model(model)

    transcript = extract_text(transcript_path, keep_speakers=True)

    final_summary = summarize_pipeline(transcript, model)

    output_path = Path(transcript_path).with_suffix(".summary.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Remeber that this is an AI summary and it may have made major mistakes in its output.")
        f.write(final_summary)
    
    kill_ollama(password)
    print("ollama killed")
    print(f"\n>Summary saved to: {output_path}")
    #print(f"previous models {models_before_ams}, password {password}, previous sate {ollama_starting_state}")
    return models_before_ams, password, ollama_starting_state

"""
if __name__ == "__main__":
    transcript_path='/home/aleluc/Videos/AutoMeetingSubsTesting/Meeting 2026.01.29.vtt'
    summarize_transcript(transcript_path)
"""