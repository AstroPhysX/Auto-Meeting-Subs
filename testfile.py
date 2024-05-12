#test file for ffmpeg

import ffmpeg

def convert_to_wav(input_file, output_filename):
    print(f"Converting {input_file} to WAV...")
    stream = ffmpeg.input(input_file)
    stream = ffmpeg.output(stream, f"{output_filename}.wav", acodec="pcm_s16le", ar=44100)
    ffmpeg.run(stream)
    print(f"Conversion complete. WAV file saved as {output_filename}.wav")

# Example usage
input_file = input('Video file:')
output_filename = "output"
convert_to_wav(input_file, output_filename)