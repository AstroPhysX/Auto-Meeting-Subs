import re
from pathlib import Path
from transformers import pipeline
import torch
import json
from transformers import AutoTokenizer

def get_best_device():
    # NVIDIA GPU (Windows/Linux)
    if torch.cuda.is_available():
        print("Using CUDA GPU")
        return 0  # transformers expects device index for CUDA

    # Apple Silicon GPU (macOS)
    if torch.backends.mps.is_available():
        print("Using Apple Silicon GPU (MPS)")
        return "mps"

    # CPU fallback
    print("Using CPU")
    return -1

DEVICE = get_best_device()

summarizer = pipeline(
    "text2text-generation",
    model="google/flan-t5-large",
    device=DEVICE
)

def extract_text(file_path, keep_speakers=False):
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

    # ---- Remove subtitle artifacts (only for VTT/SRT) ----
    if suffix in [".vtt", ".srt"]:
        content = re.sub(r"WEBVTT", "", content)
        content = re.sub(
            r"\d{2}:\d{2}:\d{2}[.,]\d{3} --> \d{2}:\d{2}:\d{2}[.,]\d{3}",
            "",
            content
        )
        content = re.sub(r"\n\d+\n", "\n", content)

    # ---- Remove diarization tags if requested ----
    if not keep_speakers:
        content = re.sub(r"\[speaker_\d+\]", "", content)

    # ---- Normalize whitespace ----
    content = re.sub(r"\n\s*\n", "\n", content)
    content = re.sub(r"[ \t]+", " ", content)

    return content.strip()



tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")

def chunk_text(text, max_tokens=450):
    tokens = tokenizer.encode(text)
    chunks = []

    while len(tokens) > max_tokens:
        chunk_tokens = tokens[:max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)
        tokens = tokens[max_tokens:]

    chunks.append(tokenizer.decode(tokens, skip_special_tokens=True))
    return chunks

def summarize_chunks(chunks):
    summaries = []

    for chunk in chunks:
        result = summarizer(
            chunk,
            max_length=200,
            min_length=60,
            do_sample=False
        )
        summaries.append(result[0]["generated_text"])

    return summaries


def structured_summary(text):
    chunks = chunk_text(text)
    partial_summaries = summarize_chunks(chunks)

    combined = "\n".join(partial_summaries)

    prompt = f"""
    You are analyzing a technical research meeting transcript.

    Write a detailed structured summary.

    Include:

    1. Main Research Topics Discussed
    2. Key Technical Insights
    3. Decisions Made
    4. Open Questions
    5. Action Items (with owner if mentioned)

    Be specific. Avoid generic statements.
    Do not invent content.
    
    Transcript:
    {combined}
    """

    # Tokenize and truncate to safe length
    max_input_tokens = 900  # leave room for generation
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_input_tokens
    ).to("cuda" if torch.cuda.is_available() else "cpu")

    with torch.no_grad():
        output_ids = summarizer.model.generate(
            **inputs,
            max_length=300,
            min_length=100,
            do_sample=False
        )

    return tokenizer.decode(output_ids[0], skip_special_tokens=True)



def save_summary(summary, subs_path):
    summary_path = Path(subs_path).with_suffix(".summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"Summary saved to {summary_path}")


def generate_summary(subs_path, keep_speakers=False):
    print("Extracting transcript text...")
    text = extract_text(subs_path, keep_speakers=keep_speakers)

    print("Generating summary (this may take a few minutes on CPU/GPU)...")
    summary = structured_summary(text)

    save_summary(summary, subs_path)

test_subs = "/home/aleluc/Videos/AutoMeetingSubsTesting/Meeting 2026.02.12.vtt"
generate_summary(test_subs)