from file_utils import setup_app_environment, audio_or_video, get_creation_date
APPDATA_DIR = setup_app_environment()
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pyannote.audio")
import os
import time
import shutil
from pathlib import Path
from config_manager import create_config, read_config
from ffmpeg_utils import convert_to_wav, compressing_audio_to_mp3, compress_video_auto
from whisperx_pipeline import whisper
from summarization_via_ollama import summarize_transcript

def main():
    # Check if config.ini exists, if not, create it and save default parameters
    appdata_dir = APPDATA_DIR
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
        
        input_file = input("Enter the file path of video or audio recording: ").strip('"\'')
        max_num_speakers = int(input("Enter the number of people talking in the meeting: "))
        if max_num_speakers == 0:
            max_num_speakers = None
        
        while True:
            change_dir = input(f"The ouput directory is {output_dir}. Is this where you want it to be save? (y/n): ").lower()
            if change_dir == "y":
                break
            elif change_dir == "n":
                output_dir = input(f"Enter the output directory path for this operation: ").strip('"\'')
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
        
        A_or_V = audio_or_video(input_file)
        print(f'The file you have provided is a/an {A_or_V}')
        # Get the directory of the input file
        file_directory = Path(input_file).parent
    
        # Get the date from the metadata file or user
        date = get_creation_date(input_file)
        if not date:
            print("Date not found in the metadata.")
            while True:
                try:
                    dt = datetime.strptime(input("Enter date (yyyy/mm/dd): ").strip(),"%Y/%m/%d")
                    break
                except ValueError:
                    print("Invalid date. Please use yyyy/mm/dd.")
            formatted_date = dt.strftime("%Y.%m.%d")
        else:
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
        transcript_path = os.path.join(output_dir, new_filename + f".{sub_format}")
        print("\nSubtitles finished.\n")

        #Removing the WAV file that was created from MKV to produce subtitles
        print("Cleaning up and moving subtitles to:",output_dir)
        proceed = True
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
                            proceed = False
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
                            proceed = False
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
                        proceed = False
                        break
                    else:
                        print("Please enter 'y' for yes or 'n' for no.")
            else:
                shutil.copy2(input_file, output_dir)
                os.rename(output_file, destination)
        
        while proceed:
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
        print('--------------------------------------------------------------Ollama-------------------------------------------------------------------------------------------')
        while True:
            summarize = input("Would like to use ollama to summarize this meeting? (y/n): ").lower()
            if summarize == "y":
                summarize_transcript(transcript_path)
                break
            elif summarize == "n":
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

        print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
        more_meetings = input("Do you have more meetings to transcribe? (y/n): ").lower()
        while True:
            if more_meetings == 'n':
                return
            elif more_meetings == 'y':
                print('****************************************************************************************************************************************************************************')
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
        

if __name__ == "__main__":
    main()