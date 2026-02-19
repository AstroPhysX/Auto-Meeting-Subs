import os
import filetype
from datetime import datetime

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


# Function to get the file's date from its metadata without ffmpeg-python
def get_creation_date(file_path):
    """
    Returns the creation datetime from file metadata if available,
    otherwise falls back to filesystem modification time.
    """

    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            file_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        metadata = json.loads(result.stdout)

        creation_time = (metadata
            .get("format", {})
            .get("tags", {})
            .get("creation_time")
        )

        if creation_time:
            dt = datetime.fromisoformat(
                creation_time.replace("Z", "+00:00")
            )
            return dt.timestamp()

    except Exception as e:
        print(f"Warning: Could not read creation_time from metadata: {e}")

    # Fallback
    return os.path.getmtime(file_path)
