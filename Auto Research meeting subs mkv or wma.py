import os
import subprocess
import time
import shutil

def extract_audio_from_mkv(mkv_file_path, output_wav_file):
    # Replace with the appropriate path to ffmpeg executable if needed
    ffmpeg_path = "C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe"#<----- replace this with the directory to ffmpeg.exe
    
    
    print("ffmpeg is extracting the audio from your video file...")
    # Use ffmpeg to extract audio from the MKV file and save it as WAV
    subprocess.run([ffmpeg_path, "-i", mkv_file_path, "-vn", "-acodec", "pcm_s16le", output_wav_file],stderr=subprocess.DEVNULL)
    print("ffmpeg has extracted the audio from", mkv_file_path,"\n")

def extract_audio_from_wma(wma_file_path, output_wav_file):
    # Replace with the appropriate path to ffmpeg executable if needed
    ffmpeg_path = "C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe"#<----- replace this with the directory to ffmpeg.exe
    
    print("ffmpeg is extracting the audio from your WMA file...")
    # Use ffmpeg to extract audio from the WMA file and save it as WAV
    subprocess.run([ffmpeg_path, "-i", wma_file_path, "-vn", "-acodec", "pcm_s16le", output_wav_file], stderr=subprocess.DEVNULL)
    print("ffmpeg has extracted the audio from", wma_file_path,"\n")
    
def get_creation_date(mkv_file_path):
    # Get the creation date of the MKV file
    return os.path.getctime(mkv_file_path)

def compress_mkv_with_handbrake(mkv_file_path, output_compressed_mkv):
    handbrake_path = "A:\\Programs\\HandBrake\\HandBrakeCLI.exe"  #<------- Replace with the appropriate path to HandBrakeCLI executable

    # Set the desired compression options using HandBrakeCLI
    # Here, we use the "Medium" preset, which provides a good balance between quality and file size.
    # You can explore other presets or customize the options as needed.
    handbrake_cmd = [
        handbrake_path,
        "-i", mkv_file_path,
        "-o", output_compressed_mkv,
        "--preset-import-gui", "Meetings",#<-----change the preset in the Handbrake GUI then save the preset and repace the "Meetings" with the name of your preset
    ]

    print("Compressing the MKV file with HandBrake...")
    subprocess.run(handbrake_cmd, stderr=subprocess.DEVNULL)
    print("MKV file compression completed.\n")

def main():
    # Prompt user for input
    input_file = input("Enter the file path of the MKV or WMA recording: ").strip('"')
    num_speakers = int(input("Enter the number of people talking: "))
    output_dir=  "A:\\SynologyDrive\\School\\PHD\\Research\\Metting recordings" #<----Need to change this to the out put directory 
    # Get the directory of the input file
    file_directory = os.path.dirname(input_file)
    
    # Get the date from the metadata file
    date = get_creation_date(input_file)
    if not date:
        print("Date not found in the metadata.")
        return
    
    # Format the date as yy/mm/dd
    formatted_date = time.strftime("%Y.%m.%d", time.localtime(date))

    # Determine if the input file is MKV or WMA
    is_mkv = input_file.lower().endswith('.mkv')
    is_wma = input_file.lower().endswith('.wma')
    
    if is_mkv:
        # Construct the new filename with the date and rename the .mkv file
        filename = f"Meeting {formatted_date}"
        new_filename = f"{filename}.mkv"
        output_wav_file = os.path.join(file_directory, f"{filename}.wav")   
    elif is_wma:
        # Construct the new filename with the date and rename the .wma file
        filename = f"Meeting {formatted_date}"
        new_filename = f"{filename}.wma"
        output_wav_file = os.path.join(file_directory, f"{filename}.wav")
    else:
        print("Invalid file format. Only MKV and WMA formats are supported.")
        return
    
    new_file_path = os.path.join(file_directory, new_filename)
    os.rename(input_file, new_file_path)

    if is_mkv:
        # Convert the MKV file to WAV
        extract_audio_from_mkv(new_file_path, output_wav_file)
    elif is_wma:
        # Convert the WMA file to WAV
        extract_audio_from_wma(new_file_path, output_wav_file)
    
    # Run the commands using miniconda prompt
    activate_cmd = "conda activate whisperx"
    #CHANGE THIS COMMAND, WITH WHAT EVER SETTINGS YOU WOULD LIKE FOR WHISPERX, REFER TO WHISPERX COMMANDS
    whisperx_cmd = (
        f'whisperx "{output_wav_file}" -o "{output_dir}" -f srt --diarize --max_speakers {num_speakers} --hf_token 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 --model medium.en'
    )
    print("Running whisperx to convert audio to subtitles and seperating voices...")
    cmd = f"{activate_cmd} && {whisperx_cmd} && conda deactivate"
    subprocess.run(cmd, shell=True, check=True)
    print("\nSubtitles finished.\n")
    
    #Removing the WAV file that was created from MKV to produce subtitles
    print("Cleaning up and moving subtitles to:",output_dir)
    os.remove(output_wav_file)
    
    if is_mkv:
        #Compressing mkv file with handbrake
        compress_mkv_with_handbrake(new_file_path, os.path.join(output_dir, new_filename))
    
        # Ask the user if they want to remove the original MKV file
        while True:
            remove_original = input("Do you want to remove the original MKV file? (y/n): ").strip().lower()
            if remove_original == 'y':
                os.remove(new_file_path)
                print("\nOriginal MKV file removed.The subtitles and compressed video are in:",output_dir)
                break
            elif remove_original == 'n':
                print("Original MKV file will be kept.\n")
                print("Original MKV has been renamed and is in",new_file_path," The subtitles and compressed video are in:",output_dir)
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
    elif is_wma:
        print("\nMoving Audio recording to:",output_dir)
        shutil.move(new_file_path, os.path.join(output_dir, new_filename))

    
    
    input("Finished processing meeting.\nPress enter to close...")

if __name__ == "__main__":
    main()