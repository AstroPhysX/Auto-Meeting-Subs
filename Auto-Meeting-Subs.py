print('Loading...')
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

# Function to read parameters from the config.ini file
def read_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    
    paths = dict(config['PATHS'])
    token = config['TOKEN']['token']
    handbrake_preset = config['HAND_BRAKE']['preset_name']
    output_dir = config['OUTPUT'].get('output_dir')
    English = config['LANGUAGE']['English']
    subtitle_format = config['SUBTITLE']['Sub_format']
    compress = config['Compress']['Video_compression']
    batch_size = config['Batch_Size']['Batch_Size']
    developer = config['DEV']['Developer_debug']
    
    return paths, token, handbrake_preset, output_dir, English, subtitle_format, compress, batch_size, developer

# Function to convert any file type to audio
def convert_to_wav(input_file, ouput_filname, ffmpeg_path, dev=False):
    print('\n--------------------------------------------------------------ffmpeg---------------------------------------------------------------------------------------------')
    print(f"\nffmpeg is converting {input_file} to WAV...")
    # Get the directory of the current Python script
    script_directory = os.path.dirname(__file__)

    # Construct the output WAV file path
    output_wav_file = os.path.join(script_directory, f'{ouput_filname}.wav')

    # Use ffmpeg to convert the input file to WAV
    if dev:
        subprocess.run([ffmpeg_path,"-y", "-i", input_file, "-vn", "-acodec", "pcm_s16le", output_wav_file])
    else:
        subprocess.run([ffmpeg_path,"-y", "-i", input_file, "-vn", "-acodec", "pcm_s16le", output_wav_file], stderr=subprocess.DEVNULL)

    print(f"ffmpeg has converted {input_file} to {output_wav_file}\n")
    return output_wav_file

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
def get_creation_date(mkv_file_path):
    # Get the creation date of the MKV file
    return os.path.getctime(mkv_file_path)

# Function to compress/convert the audio to mp3
def compressing_wma_to_mp3(wma_file_path, output_mp3_file, ffmpeg_path):
    print('--------------------------------------------------------------ffmpeg---------------------------------------------------------------------------------------------')
    print("ffmpeg is extracting the audio from your WMA file and converting it to MP3...")
    # Use ffmpeg to extract audio from the WMA file and save it as MP3
    subprocess.run([ffmpeg_path, "-i", wma_file_path, "-vn", "-acodec", "libmp3lame", output_mp3_file], stderr=subprocess.DEVNULL)
    print("ffmpeg has extracted and converted the audio to MP3 from", wma_file_path, "\n")
    print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')

# Function to compress the orginal video using handbrake
def compress_video_with_handbrake(video_file_path, output_compressed_mkv, handbrake_path, handbrake_preset):

    # Set the desired compression options using HandBrakeCLI
    # Here, we use the "Medium" preset, which provides a good balance between quality and file size.
    # You can explore other presets or customize the options as needed.
    handbrake_cmd = [
        handbrake_path,
        "-i", video_file_path,
        "-o", output_compressed_mkv,
        "--preset-import-gui", handbrake_preset,#<-----change the preset in the Handbrake GUI then save the preset and repace the "Meetings" with the name of your preset
    ]
    print('-------------------------------------------------------------Handbrake------------------------------------------------------------------------------------------')
    print("Compressing the MKV file with HandBrake...")
    subprocess.run(handbrake_cmd, stderr=subprocess.DEVNULL)
    print("MKV file compression completed.\n")
    print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')

def get_correct_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def whisper(file, output_loc, model, subformat, num_speakers, token, batch_size, dev):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # reduce if low on GPU mem
    # 1. Transcribe with original whisper (batched)
    compute_types = ["float16","float32","int8"]
    num_fails = 0
    while True:
        try:
            print(f"Constructing model with {device} and {compute_types[num_fails]}")
            # Call the function with the current parameter value
            modload = whisperx.load_model(model, device, compute_type=compute_types[num_fails], download_root=get_correct_path('Model'))
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
        audio = whisperx.load_audio(get_correct_path(file))
        if dev:
            print('Audio loaded', audio)
    except Exception as e:
        if dev:
            print(e)
        raise RuntimeWarning('Audio failed to load')

    try:
        result = modload.transcribe(audio, batch_size=batch_size, print_progress=False)
        if dev:
            print('Transcription completed')
    except:
        if dev:
            print(e)
        raise RuntimeWarning('Transcription Failed')
    
    # Unload Whisper and VAD
    del model
    gc.collect()
    torch.cuda.empty_cache()
    
    # 2. Align whisper output
    print(">>Performing alignment...")
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False, print_progress=False)
    
    # Unload align model
    del model_a
    gc.collect()
    torch.cuda.empty_cache()
    
    # 3. Diarize
    print(">>Performing diarization...")
    diarize_model = whisperx.DiarizationPipeline(use_auth_token=token, device=device)
    diarize_segments = diarize_model(audio, num_speakers=num_speakers)
    
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
    config_file = 'config.ini'
    if not os.path.exists(config_file):
        create_config(config_file)

    # Read parameters from the config.ini file
    paths, token, handbrake_preset, output_dir, English, sub_format, compression,batch_size, developer = read_config(config_file)  #extracts the settings from the config file
    ffmpeg_path = paths['ffmpeg_path']
    handbrake_path = paths['handbrake_path']
    model_language = ".en" if English == 'y' else ''
    compression = True if compression == 'y' else False
    batchsiz = int(batch_size)
    dev = False if developer == 'n' else True
   
    
    while True:
        # Prompt user for input
        input_file = input("Enter the file path of the MKV or WMA recording: ").strip('"')
        max_num_speakers = int(input("Enter the number of people talking in the meeting: "))
        if max_num_speakers == 0:
            max_num_speakers = None
        
        A_or_V = audio_or_video(input_file)
        print(f'The file you have provided is a/an {A_or_V}')
        # Get the directory of the input file
        file_directory = os.path.dirname(input_file)
    
        # Get the date from the metadata file
        date = get_creation_date(input_file)
        if not date:
            print("Date not found in the metadata.")
            return
    
        # Format the date as yy/mm/dd
        formatted_date = time.strftime("%Y.%m.%d", time.localtime(date))

        #Creating WAV file
        new_filename = f"Meeting {formatted_date}"
        wav_file = convert_to_wav(input_file, new_filename, ffmpeg_path,dev)
        
        print('--------------------------------------------------------------WhisperX-------------------------------------------------------------------------------------------')
        #WhisperX
        try:
            whisper(wav_file, output_loc=output_dir, subformat=sub_format, num_speakers=max_num_speakers, token=token, model=f"medium{model_language}", batch_size=batchsiz, dev=dev)
        except:
            input('\n***A fatal error happpened with WhisperX, please go into the config.ini file and set developer_debug to y to see the errors.***')
            return
            
        print("\nSubtitles finished.\n")

        #Removing the WAV file that was created from MKV to produce subtitles
        print("Cleaning up and moving subtitles to:",output_dir)
        os.remove(wav_file)
        if compression:
            if A_or_V == 'video':
                #Compressing mkv file with handbrake
                compress_video_with_handbrake(input_file, os.path.join(output_dir, f"{new_filename}.mkv"), handbrake_path, handbrake_preset)
                
                # Ask the user if they want to remove the original MKV file
                while True:
                    remove_original = input("Do you want to remove the original video file? (y/n): ").strip().lower()
                    if remove_original == 'y':
                        os.remove(input_file)
                        print("\nOriginal MKV file removed.The subtitles and compressed video are in:",output_dir)
                        break
                    elif remove_original == 'n':
                        print("Original video file will be kept.\n")
                        print("Original video is still located in:",input_file,"\nThe subtitles and compressed video are in:",output_dir)
                        break
                    else:
                        print("Invalid input. Please enter 'y' or 'n'.")
            elif A_or_V == 'audio':
                print("\nCompressing Audio to:",output_dir)
                compressing_wma_to_mp3(input_file, os.path.join(output_dir, f"{new_filename}.mp3"), ffmpeg_path)

                # Ask the user if they want to remove the original WMA file
                while True:
                    remove_original = input("Do you want to remove the original audio file? (y/n): ").strip().lower()
                    if remove_original == 'y':
                        os.remove(input_file)
                        print("\nOriginal audio file removed.The subtitles and compressed audio are in:",output_dir)
                        break
                    elif remove_original == 'n':
                        print("Original audio file will be kept.\n")
                        print("Original audio is still located in:",input_file,"\nThe subtitles and compressed audio are in:",output_dir)
                        break
                    else:
                        print("Invalid input. Please enter 'y' or 'n'.")
        else:
            shutil.copy2(input_file, output_dir)
            file_dir, filename = os.path.split(input_file)
            file_extension = os.path.splitext(filename)[1]
            output_file = os.path.join(output_dir, filename)
            os.rename(output_file, os.path.join(output_dir, f"{new_filename}{file_extension}"))
            while True:
                    remove_original = input(f"Do you want to remove the original {A_or_V} file? (y/n): ").strip().lower()
                    if remove_original == 'y':
                        os.remove(input_file)
                        print(f"\nOriginal {A_or_V} file removed.The subtitles and compressed video are in:",output_dir)
                        break
                    elif remove_original == 'n':
                        print(f"Original {A_or_V} file will be kept.\n")
                        print(f"Original {A_or_V} is still located in:",input_file,f"\nThe subtitles and compressed {A_or_V} are in:",output_dir)
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