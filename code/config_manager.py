import os
import platform
import configparser
from pathlib import Path

# Function to create the config.ini file and save parameters
def create_config(config_file):
    print("Looks like this is the first time you are running this program. We are going set up some necessary things for the program to run.")
    config = configparser.ConfigParser()
    config['TOKEN'] = {
        'token': input("Enter the Hugging face API token: "),
    }
    config['OUTPUT'] = {
        'output_dir': input("Enter the output directory path: ").strip('"\''),
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
    
    token = config['TOKEN']['token']
    output_dir = config['OUTPUT'].get('output_dir')
    English = config['LANGUAGE']['English']
    subtitle_format = config['SUBTITLE']['Sub_format']
    compress = config['Compress']['Video_compression']
    batch_size = config['Batch_Size']['Batch_Size']
    developer = config['DEV']['Developer_debug']
    
    return token, output_dir, English, subtitle_format, compress, batch_size, developer

# GUI Functions
def save_config(config_file, data: dict):
    config = configparser.ConfigParser(interpolation=None)

    config['TOKEN'] = {
        'token': data['token']
    }

    config['OUTPUT'] = {
        'output_dir': data['output_dir'],
        'naming_convention': data['naming_convention'],
        'video_extension': data['video_ext'],
        'audio_extension': data['audio_ext']
    }

    config['LANGUAGE'] = {
        'English': data['language']
    }

    config['SUBTITLE'] = {
        'Sub_format': data['subtitle_format']
    }

    config['COMPRESSION'] = {
        'mode': data['compression_mode'],
        'value': str(data['compression_value'])
    }
    
    config['Batch_Size']={
        'Batch_Size': 8  # reduce if low on GPU mem
    }

    config['DEV'] = {
        'Developer_debug': 'n'
    }

    if platform.system() == "Linux":
        config['LINUX'] = {
            'sudo_password': data.get('sudo_password', '')
        }

    with open(config_file, 'w') as f:
        config.write(f)


def load_config(config_file):
    config = configparser.ConfigParser(interpolation=None)

    if not os.path.exists(config_file):
        return None

    config.read(config_file)

    return {
        "token": config['TOKEN'].get('token', ''),
        "output_dir": config['OUTPUT'].get('output_dir', ''),
        "naming_convention":config['OUTPUT'].get('naming_convention',''),
        "video_ext":config['OUTPUT'].get('video_extension',''),
        "audio_ext":config['OUTPUT'].get('audio_extension',''),
        "language": config['LANGUAGE'].get('English', 'n'),
        "subtitle_format": config['SUBTITLE'].get('Sub_format', 'srt'),
        "compression_mode": config['COMPRESSION'].get('mode', 'CQ'),
        "compression_value": int(config['COMPRESSION'].get('value', 18)),
        "sudo_password": config.get('LINUX', 'sudo_password', fallback='')
    }