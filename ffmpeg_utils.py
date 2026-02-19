import subprocess
import platform
import os
from pathlib import Path
from better_ffmpeg_progress import FfmpegProcess, FfmpegProcessError

def convert_to_wav(input_file, output_filename_path, dev=False):
    print('\n--------------------------------------------------------------ffmpeg---------------------------------------------------------------------------------------------')
    print(f"\nffmpeg is converting {input_file} to WAV...")
    null_device = "NUL" if os.name == "nt" else "/dev/null"
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
            process = FfmpegProcess(command, ffmpeg_log_file=Path(null_device))
            process.run()
        print(f"ffmpeg has converted {input_file} to {output_filename_path}\n")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred:\n{e.stderr.decode() if e.stderr else str(e)}")
    except FfmpegProcessError as e:
        print(f"An error occurred:\n{str(e)}")
    
    return output_filename_path

# Function to compress/convert the audio to mp3
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

# Detects hw for video compression 
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

# compresses video with ffmpeg 
def compress_video_auto(input_file_path, output_file_path, dev=False):
    """
    Compress a video using FFmpeg with hardware acceleration if available.
    Falls back to CPU if the hardware codec fails.
    Suppresses log file creation by redirecting logs to null device.
    """

    codec = detect_best_hwaccel()  # Your function to choose best codec
    print('--------------------------------------------------------------ffmpeg Compression---------------------------------------------------------------------------------------------')

    # Cross-platform null device for discarding FFmpeg logs
    null_device = "NUL" if os.name == "nt" else "/dev/null"

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
        if dev:
            # subprocess version (no wrapper)
            subprocess.run(cmd, check=True)
        else:
            print(f"Compressing video using {codec}...")
            process = FfmpegProcess(cmd, ffmpeg_log_file=Path(null_device))
            process.run()
    except subprocess.CalledProcessError:
        if codec.startswith("libx"):
            print(f"CPU fallback {codec} also failed. Cannot continue.")
            return
        # fallback to CPU encoder
        print(f"{codec} failed, falling back to CPU encoder libx265...")
        cmd[cmd.index(codec)] = "libx265"
        if dev:
            subprocess.run(cmd, check=True)
        else:
            print("Compressing video using libx265...")
            process = FfmpegProcess(cmd, ffmpeg_log_file=Path(null_device))
            process.run()

    print("Compression finished.\n")
    print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')