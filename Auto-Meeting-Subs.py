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
        nvidia_gpu = input("Do you have a 10 series or above NVIDIA GPU ? (y/n): ").lower()
        if nvidia_gpu == 'y' or nvidia_gpu == 'n':
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

    config['GPU'] = {
        'nvidia_gpu': nvidia_gpu
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
    config['DEV'] = {
        'Developer_debug': 'n'
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
    English = config['LANGUAGE']['English']
    subtitle_format = config['SUBTITLE']['Sub_format']
    developer = config['DEV']['Developer_debug']
    return paths, token, handbrake_preset, output_dir, nvidia_gpu , English, subtitle_format,developer

#Function to extract audio from MKV file
def extract_audio_from_mkv(mkv_file_path, output_wav_file, ffmpeg_path,dev):
    print('\n--------------------------------------------------------------ffmpeg---------------------------------------------------------------------------------------------')
    print("ffmpeg is extracting the audio from your video file...")
    # Use ffmpeg to extract audio from the MKV file and save it as WAV
    if dev:
        subprocess.run([ffmpeg_path, "-i", mkv_file_path, "-vn", "-acodec", "pcm_s16le", output_wav_file])
    else:
        subprocess.run([ffmpeg_path, "-i", mkv_file_path, "-vn", "-acodec", "pcm_s16le", output_wav_file], stderr=subprocess.DEVNULL)

    print("ffmpeg has extracted the audio from", mkv_file_path,"\n")    

#Function to convert WMA audio to WAV
def extract_audio_from_wma(wma_file_path, output_wav_file, ffmpeg_path,dev):
    print('\n--------------------------------------------------------------ffmpeg---------------------------------------------------------------------------------------------')
    print("\nffmpeg is extracting the audio from your WMA file...")
    # Use ffmpeg to extract audio from the WMA file and save it as WAV
    if dev:
        subprocess.run([ffmpeg_path, "-i", wma_file_path, "-vn", "-acodec", "pcm_s16le", output_wav_file])
    else:
        subprocess.run([ffmpeg_path, "-i", wma_file_path, "-vn", "-acodec", "pcm_s16le", output_wav_file], stderr=subprocess.DEVNULL)
    
    print("ffmpeg has extracted the audio from", wma_file_path,"\n")

#Function to get the file's date from its metadata
def get_creation_date(mkv_file_path):
    # Get the creation date of the MKV file
    return os.path.getctime(mkv_file_path)

#Function to compress/convert the audio to mp3
def compressing_wma_to_mp3(wma_file_path, output_mp3_file, ffmpeg_path):
    print('--------------------------------------------------------------ffmpeg---------------------------------------------------------------------------------------------')
    print("ffmpeg is extracting the audio from your WMA file and converting it to MP3...")
    # Use ffmpeg to extract audio from the WMA file and save it as MP3
    subprocess.run([ffmpeg_path, "-i", wma_file_path, "-vn", "-acodec", "libmp3lame", output_mp3_file], stderr=subprocess.DEVNULL)
    print("ffmpeg has extracted and converted the audio to MP3 from", wma_file_path, "\n")
    print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')

#Function to compress the orginal video using handbrake
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
    print('-------------------------------------------------------------Handbrake------------------------------------------------------------------------------------------')
    print("Compressing the MKV file with HandBrake...")
    subprocess.run(handbrake_cmd, stderr=subprocess.DEVNULL)
    print("MKV file compression completed.\n")
    print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
    
def main():
    # Check if config.ini exists, if not, create it and save default parameters
    config_file = 'config.ini'
    if not os.path.exists(config_file):
        create_config(config_file)

    # Read parameters from the config.ini file
    paths, token, handbrake_preset, output_dir, nvidia_gpu, English, sub_format,developer = read_config(config_file)  #extracts the settings from the config file
    ffmpeg_path = paths['ffmpeg_path']
    handbrake_path = paths['handbrake_path']
    compute_type_otpions="--compute_type int8" if nvidia_gpu == "n" else ""
    model_language=".en" if English == 'y' else ''
    dev=False if developer == 'n' else True
    
    while True:
        # Prompt user for input
        input_file = input("Enter the file path of the MKV or WMA recording: ").strip('"')
        min_num_speakers = int(input("Enter the min number of people talking: "))
        max_num_speakers = int(input("Enter the max number of people talking: "))
        
    
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
            output_mp3_file = os.path.join(file_directory, f"{filename}.mp3")
        else:
            print("Invalid file format. Only MKV and WMA formats are supported.")
            return
    
        new_file_path = os.path.join(file_directory, new_filename)
        os.rename(input_file, new_file_path)

        if is_mkv:
            # Convert the MKV file to WAV
            extract_audio_from_mkv(new_file_path, output_wav_file, ffmpeg_path,dev)
        elif is_wma:
            # Convert the WMA file to WAV
            extract_audio_from_wma(new_file_path, output_wav_file, ffmpeg_path,dev)
        
        print('--------------------------------------------------------------WhisperX-------------------------------------------------------------------------------------------')
        #WHISPERX
        # Run the commands using miniconda prompt
        activate_cmd = "conda activate whisperx"
    
        #CHANGE THIS COMMAND, WITH WHAT EVER SETTINGS YOU WOULD LIKE FOR WHISPERX, REFER TO WHISPERX COMMANDS
        whisperx_cmd = (
            f'whisperx "{output_wav_file}" -o "{output_dir}" -f {sub_format} --diarize --max_speakers {max_num_speakers} --min_speakers {min_num_speakers} --hf_token {token} --model medium{model_language} {compute_type_otpions}'
        )
        print("Running whisperx to convert audio to subtitles and seperating voices this may take a while...")
        
        cmd = f"{activate_cmd} && {whisperx_cmd} && conda deactivate"
        
        try:
            if dev:
                print(whisperx_cmd,'\n')
                print('\n--WhisperX Output--')
                subprocess.run(cmd, shell=True, check=True)
                print('----------------------')
            else:
                print('\n--WhisperX Output--')
                subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL,check=True)
                print('----------------------')
        except subprocess.CalledProcessError as e:
            input('\n***A fatal error happpened with WhisperX, please go into the config.ini file and set developer_debug to y to see the errors.***')
            return
            
            
        print("\nSubtitles finished.\n")

        #Removing the WAV file that was created from MKV to produce subtitles
        print("Cleaning up and moving subtitles to:",output_dir)
        if is_mkv:
            #Compressing mkv file with handbrake
            compress_mkv_with_handbrake(new_file_path, os.path.join(output_dir, new_filename), handbrake_path, handbrake_preset)
            os.remove(output_wav_file)
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
            os.remove(output_wav_file)
            compressing_wma_to_mp3(new_file_path, output_mp3_file, ffmpeg_path)
        
            print("\nMoving Audio recording to:",output_dir)
            shutil.move(output_mp3_file, os.path.join(output_dir, f"{filename}.mp3"))
        
            # Ask the user if they want to remove the original WMA file
            while True:
                remove_original = input("Do you want to remove the original WMA file? (y/n): ").strip().lower()
                if remove_original == 'y':
                    os.remove(new_file_path)
                    print("\nOriginal WMA file removed.The subtitles and compressed video are in:",output_dir)
                    break
                elif remove_original == 'n':
                    print("Original WMA file will be kept.\n")
                    print("Original WMA has been renamed and is in",new_file_path," The subtitles and compressed video are in:",output_dir)
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