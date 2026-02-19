import re
import json
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
# -------------------------------------------------
# Hardware Detection
# -------------------------------------------------

def detect_hardware():
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        vram_gb = props.total_memory / (1024 ** 3)
        return {
            "device": "cuda",
            "vram_gb": vram_gb
        }

    if torch.backends.mps.is_available():
        return {
            "device": "mps",
            "vram_gb": 0
        }

    return {
        "device": "cpu",
        "vram_gb": 0
    }

# -------------------------------------------------
# Model Selection
# -------------------------------------------------

def select_model(hw):

    # 16GB+ GPU
    if hw["device"] == "cuda" and hw["vram_gb"] >= 14:
        return {
            "model_name": "mistralai/Mistral-7B-Instruct-v0.2",
            "quantize": True,
            "max_chunk_tokens": 6000
        }

    # 8–14GB GPU
    if hw["device"] == "cuda":
        return {
            "model_name": "mistralai/Mistral-7B-Instruct-v0.2",
            "quantize": True,
            "max_chunk_tokens": 3500
        }

    # CPU fallback
    return {
        "model_name": "google/flan-t5-base",
        "quantize": False,
        "max_chunk_tokens": 450
    }

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

# -------------------------------------------------
# Token Chunking
# -------------------------------------------------

def chunk_text(text, tokenizer, max_tokens):
    tokens = tokenizer.encode(text)
    chunks = []

    while len(tokens) > max_tokens:
        chunk = tokens[:max_tokens]
        chunks.append(tokenizer.decode(chunk, skip_special_tokens=True))
        tokens = tokens[max_tokens:]

    chunks.append(tokenizer.decode(tokens, skip_special_tokens=True))
    return chunks

# -------------------------------------------------
# Prompt Templates
# -------------------------------------------------

def chunk_prompt(text):
    return f"""
You are analyzing a technical research meeting transcript section.

Your goal is analytical compression, not paraphrasing.

For this section:

1. Identify the main scientific or technical problem being discussed.
2. Explain the core reasoning or argument in full sentences.
3. Extract any explicit decisions (only if clearly stated).
4. Extract unresolved technical uncertainties.
5. Extract concrete next steps (only if explicitly stated).

Rules:
- Avoid repeating transcript phrasing.
- Do NOT produce short topic lists.
- Do NOT invent decisions.
- Use precise technical language.
- Write in structured paragraphs.

Transcript:
{text}
"""

def final_prompt(text):
    return f"""
You are synthesizing summaries from a long research meeting.

IMPORTANT:
- Do NOT include any headings before Section 1.
- Do NOT include raw bullet dumps.
- Start directly with "1. Overall Topics Discussed".

Produce a detailed, clean, professional summary.

Strictly follow this exact structure:

1. Overall Topics Discussed
2. Key Technical Insights
3. Decisions Made
4. Open Questions / Challenges
5. Action Items

Write in clean paragraphs (not bullet fragments).
Do not repeat phrasing across sections.
Only list decisions if they were explicitly agreed upon.
Do not invent decisions.

Section summaries:
{text}
"""

# -------------------------------------------------
# Main Generator
# -------------------------------------------------

def build_pipeline(selection, hw):

    print(f"Loading model: {selection['model_name']}")
    print(f"Detected device: {hw['device']}")
    print(f"VRAM: {hw['vram_gb']:.1f} GB")

    if selection["quantize"] and hw["device"] == "cuda":
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        model = AutoModelForCausalLM.from_pretrained(
            selection["model_name"],
            quantization_config=quant_config,
            device_map="auto"
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            selection["model_name"],
            device_map="auto"
        )

    tokenizer = AutoTokenizer.from_pretrained(selection["model_name"])

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        pad_token_id=tokenizer.eos_token_id
    )

    return pipe, tokenizer

# -------------------------------------------------
# Summarization Logic
# -------------------------------------------------

def summarize_meeting(text, pipe, tokenizer, max_chunk_tokens):

    chunks = chunk_text(text, tokenizer, max_chunk_tokens)

    print(f"Transcript split into {len(chunks)} chunks")

    section_summaries = []

    for i, chunk in enumerate(chunks):
        print(f"Summarizing chunk {i+1}/{len(chunks)}")

        output = pipe(
            chunk_prompt(chunk),
            max_new_tokens=800,
            temperature=0.2,
            return_full_text=False
        )

        section_summaries.append(output[0]["generated_text"].strip())


    combined = "\n\n".join(section_summaries)

    combined_chunks = chunk_text(
        combined,
        tokenizer,
        max_chunk_tokens // 2   # safer
    )

    # Then synthesize in stages
    intermediate = []

    for chunk in combined_chunks:
        out = pipe(
            final_prompt(chunk),
            max_new_tokens=500,
            temperature=0.2,
            return_full_text=False
        )
        intermediate.append(out[0]["generated_text"])

    final_input = "\n\n".join(intermediate)

    final = pipe(
        final_prompt(final_input),
        max_new_tokens=600,
        temperature=0.2,
        return_full_text=False
    )


    return final[0]["generated_text"]

# -------------------------------------------------
# Entry Point
# -------------------------------------------------

def generate_summary(file_path):

    hw = detect_hardware()
    selection = select_model(hw)

    pipe, tokenizer = build_pipeline(selection, hw)

    text = extract_text(file_path)

    summary = summarize_meeting(
        text,
        pipe,
        tokenizer,
        selection["max_chunk_tokens"]
    )

    output_path = Path(file_path).with_suffix(".summary.txt")
    output_path.write_text(summary, encoding="utf-8")

    print(f"Summary saved to {output_path}")

# -------------------------------------------------

if __name__ == "__main__":
    test_file = "/home/aleluc/Videos/AutoMeetingSubsTesting/Meeting 2026.02.12.vtt"
    generate_summary(test_file)
