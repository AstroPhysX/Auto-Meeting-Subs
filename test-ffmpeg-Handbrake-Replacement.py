import subprocess
import platform
import shutil
from better_ffmpeg_progress import FfmpegProcess, FfmpegProcessError

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
def compress_video_auto(input_file_path, output_file_path, dev=False):
    codec = detect_best_hwaccel()
    
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

input_file = "/home/aleluc/Videos/Meetings/2026-02-02 13-31-45.mkv"
output_file = "/home/aleluc/Videos/test.mkv"
compress_video_auto(input_file, output_file)