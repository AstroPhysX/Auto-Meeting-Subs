import os
import sys
import io
import gc
import torch
import whisperx

from contextlib import redirect_stdout, redirect_stderr
from whisperx.diarize import DiarizationPipeline

# Function supress warning message when running whisperx
def suppress_specific_warning(func, *args, **kwargs):
    f_stdout = io.StringIO()
    f_stderr = io.StringIO()
    with redirect_stdout(f_stdout), redirect_stderr(f_stderr):
        result = func(*args, **kwargs)
    stdout_output = f_stdout.getvalue()
    stderr_output = f_stderr.getvalue()
    for line in stdout_output.splitlines():
        if "Model was trained with pyannote.audio" not in line and "Model was trained with torch" not in line:
            print(line, file=sys.stdout)
    for line in stderr_output.splitlines():
        if "Model was trained with pyannote.audio" not in line and "Model was trained with torch" not in line:
            print(line, file=sys.stderr)
    return result

# Function runs whisperX
def whisper(file, output_loc, model_location, model, subformat, num_speakers, token, batch_size, dev):

    if torch.cuda.is_available():
        device = "cuda"
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    
    # reduce if low on GPU mem
    # 1. Transcribe with original whisper (batched)
    compute_types = ["float16","float32","int8"]
    num_fails = 0
    print(">>Constructing Model...")
    while True:
        try:
            if dev:
                print(f"Constructing model with {device} and {compute_types[num_fails]}")
                # Call the function with the current parameter value
                modload = whisperx.load_model(model, device, compute_type=compute_types[num_fails], download_root=model_location)
            else:
                modload = suppress_specific_warning(whisperx.load_model,model,device,compute_type=compute_types[num_fails],download_root=model_location)  
        except Exception as e:
            if dev:
                print(e)
            num_fails += 1
            if num_fails == 3:
                # Third failure, raise an error message
                raise RuntimeError("Function failed three times in a row")
        else:
            # If no exception occurs, break out of the loop
            break
    
    print(">>Performing transcription...")
    try:
        audio = whisperx.load_audio(file)
        if dev:
            print('Audio loaded')
    except Exception as e:
        if dev:
            print('Audio failed to load', e)
        raise RuntimeWarning('Audio failed to load')

    result = modload.transcribe(audio, batch_size=batch_size, print_progress=False, verbose=dev)
    if dev:
        print('Transcription completed')
    
    # Unload Whisper and VAD
    del model
    gc.collect()
    torch.cuda.empty_cache()
    
    # 2. Align whisper output
    print(">>Performing alignment...")
    if dev:
        print('Loading model')
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device,)
    if dev:
        print('Aligining')
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False, print_progress=False)
    
    # Unload align model
    del model_a
    gc.collect()
    torch.cuda.empty_cache()
    
    # 3. Diarize
    print(">>Performing diarization...")
    if dev:
        print('Loading Diarization model')
    diarize_model = DiarizationPipeline(token=token, device=device)
    if dev:
        print('Running diarization')
    diarize_segments = diarize_model(audio, num_speakers=num_speakers)
    
    if dev:
        print('Assigning speakers')
    result = whisperx.assign_word_speakers(diarize_segments, result)
    
    #writing file
    os.makedirs(output_loc, exist_ok=True)
    writer = whisperx.utils.get_writer(subformat, output_loc)
    result["language"] = "en"
    word_options = {"highlight_words":False,
                    "max_line_count":None,
                    "max_line_width":None}
    writer(result, file, word_options)