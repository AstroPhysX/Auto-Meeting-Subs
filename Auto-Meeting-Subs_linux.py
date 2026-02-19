import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pyannote.audio")
import os
import subprocess
import time
import shutil
import configparser
import whisperx
import gc
import torch
import filetype
import sys
import sys
import io
from pathlib import Path
import platform
from contextlib import redirect_stdout, redirect_stderr
from whisperx.diarize import DiarizationPipeline
from better_ffmpeg_progress import FfmpegProcess, FfmpegProcessError
#Function to create dir in appdata (saved in config_manger)
def mkdir_localdata():
    if platform.system() == "Windows":
        base_dir = Path(os.getenv("LOCALAPPDATA"))
    else:
        # Linux / macOS
        base_dir = Path.home() / ".local" / "share"

    appdata_dir = base_dir / "Auto-Meeting-Subs"
    appdata_dir.mkdir(parents=True, exist_ok=True)
    return str(appdata_dir)

# Function to create the config.ini file and save parameters (saved in config_manger)
def create_config(config_file):
    print("Looks like this is the first time you are running this program. We are going set up some necessary things for the program to run.")
    config = configparser.ConfigParser()
    config['TOKEN'] = {
        'token': input("Enter the Hugging face API token: "),
    }
    config['OUTPUT'] = {
        'output_dir': input("Enter the output directory path: ").strip('"'),
    }
    while True:
        english = input("Are the meetings in english? (y/n): ").lower()
        if english == 'y' or english == 'n':
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
    config['LANGUAGE'] = {
        'English': english
    }
    while True:
        sub_format = input("What subtitle format would like to use? (srt, vtt, txt, tsv, json, aud) choose SRT if you don't know what this is: ").lower()
        if sub_format == 'srt' or sub_format == 'vtt' or sub_format == 'txt' or sub_format == 'tsv' or sub_format == 'json' or sub_format == 'aud':
            break
        else:
            print("Invalid input. Please enter srt or vtt or txt or tsv or json or aud.")
    config['SUBTITLE'] = {
        'Sub_format': sub_format
    }
    config['Compress'] = {
        'Video_compression': 'y'
    }
    config['Batch_Size']={
        'Batch_Size': 8  # reduce if low on GPU mem
    }
    config['DEV'] = {
        'Developer_debug': 'n'
    }
    print("\nFirst time configuration complete!!\n")
    
    with open(config_file, 'w') as cfgfile:
        config.write(cfgfile)

# Function to read parameters from the config.ini file (saved in config_manger)
def read_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    
    token = config['TOKEN']['token']
    output_dir = config['OUTPUT'].get('output_dir')
    English = config['LANGUAGE']['English']
    subtitle_format = config['SUBTITLE']['Sub_format']
    compress = config['Compress']['Video_compression']
    batch_size = config['Batch_Size']['Batch_Size']
    developer = config['DEV']['Developer_debug']
    
    return token, output_dir, English, subtitle_format, compress, batch_size, developer

# Function to convert any file type to audio  (now in ffmpeg_utils)  
def convert_to_wav(input_file, output_filename_path, dev=False):
    print('\n--------------------------------------------------------------ffmpeg---------------------------------------------------------------------------------------------')
    print(f"\nffmpeg is converting {input_file} to WAV...")
    
    # Use ffmpeg to convert the input file to WAV
    command = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-vn",                 # no video
        "-c:a", "pcm_s16le",   # WAV PCM encoding
        output_filename_path
    ]
    try:
        if dev:
            subprocess.run(command, check=True)
        else:
            process = FfmpegProcess(command)
            process.run()
        print(f"ffmpeg has converted {input_file} to {output_filename_path}\n")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred:\n{e.stderr.decode() if e.stderr else str(e)}")
    except FfmpegProcessError as e:
        print(f"An error occurred:\n{str(e)}")
    
    return output_filename_path

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
    
# Function to get the file's date from its metadata
def get_creation_date(file_path):
    """
    Returns the creation datetime from file metadata if available,
    otherwise falls back to filesystem modification time.
    """
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

# Function to compress/convert the audio to mp3 (now in ffmpeg_utils.py)
def compressing_audio_to_mp3(Audio_file_path, output_mp3_file, dev=False):
    print('--------------------------------------------------------------ffmpeg---------------------------------------------------------------------------------------------')
    print("ffmpeg is extracting the audio from your WMA file and converting it to MP3...")
    # Use ffmpeg to extract audio from the WMA file and save it as MP3
    command = [
        "ffmpeg",
        "-y",
        "-i", Audio_file_path,
        "-c:a", "libmp3lame",
        output_mp3_file
    ]
    try:
        if dev:
            subprocess.run(command, check=True)
        else:
            process = FfmpegProcess(command)
            process.run()
        print(f"ffmpeg has converted {Audio_file_path} to {output_mp3_file}\n")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr.decode()}")
    except FfmpegProcessError as e:
        print(f"An error occurred: {str(e)}")

    print("ffmpeg has extracted and converted the audio to MP3 from", Audio_file_path, "\n")
    print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')

# Detects hw for video compression (now in ffmpeg_utils)
def detect_best_hwaccel():
    """
    Detect the best available hardware video encoder on the system.
    Returns the codec name for ffmpeg.
    """

    # Run `ffmpeg -encoders` to list available encoders
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True
        )
        encoders = result.stdout
    except Exception:
        encoders = ""

    # Order by preference (fastest first)
    preferred_encoders = []

    # NVIDIA GPU
    if "hevc_nvenc" in encoders:
        preferred_encoders.append("hevc_nvenc")
    if "h264_nvenc" in encoders:
        preferred_encoders.append("h264_nvenc")

    # Intel QuickSync
    if "hevc_qsv" in encoders:
        preferred_encoders.append("hevc_qsv")
    if "h264_qsv" in encoders:
        preferred_encoders.append("h264_qsv")

    # AMD VCE / AMF
    if "hevc_amf" in encoders:
        preferred_encoders.append("hevc_amf")
    if "h264_amf" in encoders:
        preferred_encoders.append("h264_amf")

    # Apple VideoToolbox (macOS)
    if platform.system() == "Darwin":
        if "hevc_videotoolbox" in encoders:
            preferred_encoders.append("hevc_videotoolbox")
        if "h264_videotoolbox" in encoders:
            preferred_encoders.append("h264_videotoolbox")

    # Fallback CPU software encoder
    preferred_encoders.append("libx265")  # H.265 CPU fallback
    preferred_encoders.append("libx264")  # H.264 CPU fallback

    # Return the first available encoder from the preferred list
    for codec in preferred_encoders:
        if codec in encoders or codec.startswith("libx"):  # libx always present if ffmpeg installed
            return codec

    # Default fallback
    return "libx265"

# compresses video with ffmpeg (now in ffmpeg_utlis.py)
def compress_video_auto(input_file_path, output_file_path, dev=False):
    codec = detect_best_hwaccel()
    print('--------------------------------------------------------------ffmpeg Compression---------------------------------------------------------------------------------------------')
    
    cmd = [
        "ffmpeg",
        "-y",
        "-hwaccel", "auto",     # allow GPU decoding if available
        "-i", input_file_path,
        "-c:v", codec,
        "-b:v", "1500k",
        "-preset", "fast",
        "-c:a", "copy",
        output_file_path
    ]

    try:
        print(f"Compressing video using {codec}...")
        process = FfmpegProcess(cmd)
        process.run()
    except subprocess.CalledProcessError:
        if codec.startswith("libx"):
            print(f"CPU fallback {codec} also failed. Cannot continue.")
            return
        # fallback to CPU encoder
        print(f"{codec} failed, falling back to CPU encoder libx265...")
        cmd[cmd.index(codec)] = "libx265"
        process = FfmpegProcess(cmd)
        process.run()

    print("Compression finished.\n")
    print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')


# Function supress warning message when running whisperx (now in whisperx_pipeline.py)
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

# Function runs whisperX (now in whisperx_pipeline.py)
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


    result = modload.transcribe(audio, batch_size=batch_size, print_progress=True, verbose=dev)
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
        
def main():
    # Check if config.ini exists, if not, create it and save default parameters
    appdata_dir = mkdir_localdata()
    config_dir = os.path.join(appdata_dir,'config.ini')
    
    if not os.path.exists(config_dir):
        create_config(config_dir)

    # Read parameters from the config.ini file
    token, output_dir, English, sub_format, compression,batch_size, developer = read_config(config_dir)  #extracts the settings from the config file
    model_language = ".en" if English == 'y' else ''
    compression = True if compression == 'y' else False
    batchsiz = int(batch_size)
    dev = False if developer == 'n' else True

    
    while True:
        # Prompt user for input
        input_file = input("Enter the file path of video or audio recording: ").strip('"')
        max_num_speakers = int(input("Enter the number of people talking in the meeting: "))
        if max_num_speakers == 0:
            max_num_speakers = None
        
        A_or_V = audio_or_video(input_file)
        print(f'The file you have provided is a/an {A_or_V}')
        # Get the directory of the input file
        file_directory = Path(input_file).parent
    
        # Get the date from the metadata file
        date = get_creation_date(input_file)
        if not date:
            print("Date not found in the metadata.")
            return
    
        # Format the date as yy/mm/dd
        formatted_date = time.strftime("%Y.%m.%d", time.localtime(date))

        #Creating WAV file
        new_filename = f"Meeting {formatted_date}"
        new_file_path = os.path.join(appdata_dir ,new_filename + ".wav")
        wav_file = convert_to_wav(input_file, new_file_path, dev)
        
        print('--------------------------------------------------------------WhisperX-------------------------------------------------------------------------------------------')
        #WhisperX
        whisper(wav_file, 
                output_loc=output_dir, 
                subformat=sub_format, 
                num_speakers=max_num_speakers, 
                token=token, 
                model_location=str(Path(appdata_dir)), 
                model=f"medium{model_language}", 
                batch_size=batchsiz, 
                dev=dev)
            
        print("\nSubtitles finished.\n")

        #Removing the WAV file that was created from MKV to produce subtitles
        print("Cleaning up and moving subtitles to:",output_dir)
        os.remove(wav_file)
        if compression:
            if A_or_V == 'video':
                #Compressing mkv file with ffmpeg
                destination = os.path.join(output_dir, f"{new_filename}.mkv")
                if os.path.exists(destination):
                    while True:
                        overwrite = input(f"File '{destination}' already exists. Do you want to overwrite it? (y/n): ").strip().lower()
                        if overwrite == 'y':
                            compress_video_auto(input_file, os.path.join(output_dir, f"{new_filename}.mkv"), dev)
                            break
                        elif overwrite == 'n':
                            print("File was not overwritten. Operation aborted.")
                            break
                        else:
                            print("Please enter 'y' for yes or 'n' for no.")
                else:
                    compress_video_auto(input_file, os.path.join(output_dir, f"{new_filename}.mkv"), dev)
            elif A_or_V == 'audio':
                print("\nCompressing Audio to:",output_dir)
                if os.path.exists(destination):
                    while True:
                        overwrite = input(f"File '{destination}' already exists. Do you want to overwrite it? (y/n): ").strip().lower()
                        if overwrite == 'y':
                            compressing_audio_to_mp3(input_file, os.path.join(output_dir, f"{new_filename}.mp3"), dev)
                            break
                        elif overwrite == 'n':
                            print("File was not overwritten. Operation aborted.")
                            break
                        else:
                            print("Please enter 'y' for yes or 'n' for no.")
                else:
                    compressing_audio_to_mp3(input_file, os.path.join(output_dir, f"{new_filename}.mp3"), dev)
        else:
            file_dir, filename = os.path.split(input_file)
            file_extension = os.path.splitext(filename)[1]
            output_file = os.path.join(output_dir, filename)
            destination = os.path.join(output_dir, f"{new_filename}{file_extension}")
            if os.path.exists(destination):
                while True:
                    overwrite = input(f"File '{destination}' already exists. Do you want to overwrite it? (y/n): ").strip().lower()
                    if overwrite == 'y':
                        os.remove(destination)
                        shutil.copy2(input_file, output_dir)
                        os.rename(output_file, destination)
                        break
                    elif overwrite == 'n':
                        print("File was not overwritten. Operation aborted.")
                        break
                    else:
                        print("Please enter 'y' for yes or 'n' for no.")
            else:
                shutil.copy2(input_file, output_dir)
                os.rename(output_file, destination)
        
        while True:
                remove_original = input("Do you want to remove the original video file? (y/n): ").strip().lower()
                if remove_original == 'y':
                    os.remove(input_file)
                    print(f"\nOriginal {A_or_V} file removed.The subtitles and compressed video are in: {output_dir}")
                    break
                elif remove_original == 'n':
                    print(f"Original {A_or_V} file will be kept.\n")
                    print(f"Original {A_or_V} is still located in:{input_file} \nThe subtitles and compressed video are in:{output_dir}")
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
        print('Finished processing meeting.')
        print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
        more_meetings = input("Do you have more meetings to transcribe? (y/n): ").lower()
        while True:
            if more_meetings == 'n':
                return
            elif more_meetings == 'y':
                print('****************************************************************************************************************************************************************************')
                break
        

if __name__ == "__main__":
    main()