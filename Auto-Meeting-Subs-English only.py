import os
import subprocess
import time
import shutil
import configparser

# Function to create the config.ini file and save parameters
def create_config(config_file):
    print("Looks like this is the first time you are running this program. We are going set up some necessary things for the program to run.")
    config = configparser.ConfigParser()
    config['PATHS'] = {
        'ffmpeg_path': input("Enter the path to ffmpeg.exe: ").strip('"'),
        'handbrake_path': input("Enter the path to HandBrakeCLI.exe: ").strip('"'),
    }
    config['HAND_BRAKE'] = {
        'preset_name': input("Enter the HandBrake preset name: "),
    }
    config['TOKEN'] = {
        'token': input("Enter the Hugging face API token: "),
    }
    config['OUTPUT'] = {
        'output_dir': input("Enter the output directory path: ").strip('"'),
    }
    while True:
        nvidia_gpu = input("Do you have an NVIDIA GPU? (y/n): ").lower()
        if nvidia_gpu == 'y' or nvidia_gpu == 'n':
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

    config['GPU'] = {
        'nvidia_gpu': nvidia_gpu
    }
    print("\nFirst time configuration complete!!\n")
    with open(config_file, 'w') as cfgfile:
        config.write(cfgfile)

# Function to read parameters from the config.ini file
def read_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    
    paths = dict(config['PATHS'])
    token = config['TOKEN']['token']
    handbrake_preset = config['HAND_BRAKE']['preset_name']
    output_dir = config['OUTPUT'].get('output_dir')
    nvidia_gpu = config['GPU']['nvidia_gpu']
    return paths, token, handbrake_preset, output_dir, nvidia_gpu

def extract_audio_from_mkv(mkv_file_path, output_wav_file, ffmpeg_path):
    print("ffmpeg is extracting the audio from your video file...")
    # Use ffmpeg to extract audio from the MKV file and save it as WAV
    subprocess.run([ffmpeg_path, "-i", mkv_file_path, "-vn", "-acodec", "pcm_s16le", output_wav_file],stderr=subprocess.DEVNULL)
    print("ffmpeg has extracted the audio from", mkv_file_path,"\n")

def extract_audio_from_wma(wma_file_path, output_wav_file, ffmpeg_path):
    print("ffmpeg is extracting the audio from your WMA file...")
    # Use ffmpeg to extract audio from the WMA file and save it as WAV
    subprocess.run([ffmpeg_path, "-i", wma_file_path, "-vn", "-acodec", "pcm_s16le", output_wav_file], stderr=subprocess.DEVNULL)
    print("ffmpeg has extracted the audio from", wma_file_path,"\n")
    
def get_creation_date(mkv_file_path):
    # Get the creation date of the MKV file
    return os.path.getctime(mkv_file_path)

def compress_mkv_with_handbrake(mkv_file_path, output_compressed_mkv, handbrake_path, handbrake_preset):

    # Set the desired compression options using HandBrakeCLI
    # Here, we use the "Medium" preset, which provides a good balance between quality and file size.
    # You can explore other presets or customize the options as needed.
    handbrake_cmd = [
        handbrake_path,
        "-i", mkv_file_path,
        "-o", output_compressed_mkv,
        "--preset-import-gui", handbrake_preset,#<-----change the preset in the Handbrake GUI then save the preset and repace the "Meetings" with the name of your preset
    ]

    print("Compressing the MKV file with HandBrake...")
    subprocess.run(handbrake_cmd, stderr=subprocess.DEVNULL)
    print("MKV file compression completed.\n")

def main():
    # Check if config.ini exists, if not, create it and save default parameters
    config_file = 'config.ini'
    if not os.path.exists(config_file):
        create_config(config_file)

    # Read parameters from the config.ini file
    paths, token, handbrake_preset, output_dir, nvidia_gpu = read_config(config_file)  # Updated to unpack 'handbrake_preset'
    ffmpeg_path = paths['ffmpeg_path']
    handbrake_path = paths['handbrake_path']
    compute_type_otpions="--compute_type int8" if nvidia_gpu == "n" else ""
    
    # Prompt user for input
    input_file = input("Enter the file path of the MKV or WMA recording: ").strip('"')
    num_speakers = int(input("Enter the number of people talking: "))
    
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
        extract_audio_from_mkv(new_file_path, output_wav_file, ffmpeg_path)
    elif is_wma:
        # Convert the WMA file to WAV
        extract_audio_from_wma(new_file_path, output_wav_file, ffmpeg_path)
    
    # Run the commands using miniconda prompt
    activate_cmd = "conda activate whisperx"
    #CHANGE THIS COMMAND, WITH WHAT EVER SETTINGS YOU WOULD LIKE FOR WHISPERX, REFER TO WHISPERX COMMANDS
    whisperx_cmd = (
        f'whisperx "{output_wav_file}" -o "{output_dir}" -f srt --diarize --max_speakers {num_speakers} --hf_token {token} --model medium.en {compute_type_otpions}'
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
        compress_mkv_with_handbrake(new_file_path, os.path.join(output_dir, new_filename), handbrake_path, handbrake_preset)
    
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