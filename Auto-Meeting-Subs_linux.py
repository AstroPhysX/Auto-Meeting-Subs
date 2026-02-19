import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pyannote.audio")

import os
import time
import shutil
from pathlib import Path

# Import only the functions needed from your modules
from config_manager import mkdir_localdata, create_config, read_config
from file_utils import audio_or_video, get_creation_date
from ffmpeg_utils import convert_to_wav, compressing_audio_to_mp3, compress_video_auto
from whisperx_pipeline import whisper
#Function to create dir in appdata (mkdir_localdata saved in config_manger)

# Function to create the config.ini file and save parameters (create_config(config_file) saved in config_manger)

# Function to read parameters from the config.ini file (read_config(config_file) saved in config_manger)

# Function to convert any file type to audio  (convert_to_wav(input_file, output_filename_path, dev=False) now in ffmpeg_utils)  


# Function to determine if file is Audio or Video (audio_or_video(file) now in file_utils.py)

    
# Function to get the file's date from its metadata (get_creation_date(file_path) now in file_utils.py)


# Function to compress/convert the audio to mp3 (compressing_audio_to_mp3(Audio_file_path, output_mp3_file, dev=False) now in ffmpeg_utils.py)

# Detects hw for video compression (detect_best_hwaccel() now in ffmpeg_utils)

# compresses video with ffmpeg (compress_video_auto(input_file_path, output_file_path, dev=False) now in ffmpeg_utlis.py)


# Function supress warning message when running whisperx (suppress_specific_warning(func, *args, **kwargs) now in whisperx_pipeline.py)


# Function runs whisperX (whisper(file, output_loc, model_location, model, subformat, num_speakers, token, batch_size, dev) now in whisperx_pipeline.py)

        
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