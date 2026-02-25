# Auto-Meeting-Subs
## Description
Automatically generates subtitles and summaries for your meeting recordings. The program **works with any video and audio files**.

The workflow now does the following:

  1. **Generate subtitles** – Uses WhisperX to create an SRT subtitle file with speech diarization from the recording.

  2. **Compress recording** – Uses FFmpeg to compress the video or audio file.

  3. **Rename and organize** – Moves the compressed file and subtitles to the output directory, renaming them to Meeting yy.mm.dd based on the creation date.

  4. **Summarize the meeting** – Uses Ollama to generate a text summary, giving a quick overview of key points.

Goal: Make it faster and easier to review meetings, locate specific parts of the conversation, and get summaries without watching or listening to the entire recording.
# Install process

## Obtaining Hugging Face API key for Auto-Meeting-Subs to work
**IMPORTANT:** You will now need to go to each of the following link and accept the user agreement and obtain a api token for the model:<br />
Speaker Diariztion: https://huggingface.co/pyannote/speaker-diarization-community-1<br /><br />
You will need to generate a Hugging Face access token that you can generate here:<br /> [Hugging Face API Token](https://huggingface.co/settings/tokens) <br /> If you don't have an account go through the process to sign up for a free account. Then click on "New Token", the role can be set to read and name the token however you would like. **Copy the token somewhere safe, we will be using it later during the initial setup of Auto-Meeting-Subs**<br />
![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/e32daa8e-594e-406b-b2fc-f2b073a35cf7)

## Installing Auto-Meeting-Subs
Start by downloading Auto-Meeting-Subs.zip for your operating system from [here](https://github.com/AstroPhysX/Auto-Meeting-Subs/releases). See picture on where to click to download. ![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/d3d48cfe-ba05-48cc-976a-85a28ea58f1d) <br /><br />

### Linux
Now unzip the file and save the unzipped folder in a safe place. 
Open a terminal window in that directory (this can usually be done by right clicking inside the directory with an option like "Open Terminal Here") and run the following command ```./install.sh```.<br/>
If for some reason this gives you an error try running ```chmod +x install.sh``` then run ```./install.sh``` again.
It will now go through the process of installing python3.10, creating a virtual python environment and installing the required python packages in that python enviroment, and finally making a start menu shortcut.

### Windows
Now unzip the file you downloaded and go inside the folder. Double click on the ```install.bat``` file, this will give you a warning since the program isn't signed click on "More info" then click on "Run Anyway". It will now go through the process of installing python3.10, creating a virtual python environment and installing the required python packages in that python enviroment, and finally making a start menu shortcut.<br />
If you have fears of malaware (rightfully so) due to this program you can use [virustotal](https://www.virustotal.com/gui/home/upload) to check the .zip file or read through the code folder.
### Mac
Double click the .zip file you just downloaded, resulting in a folder with the same name appearing. Click into the folder then hit ```Command + Space``` on your keyboard, this will open a terminal window now run ```./install.command```<br/>
If for some reason this gives you an error try running ```chmod +x install.command``` then run ```./install.command``` again.
The installer will check if you python3.10 installed, if you don't it will attempt to install it via Homebrew. If Homebrew is not installed on your Mac, you will need to manually install python3.10. You can download it [here](https://www.python.org/downloads/release/python-31011/) and go through the basic install process for it then run the ```./install.command``` again. The installer create a virtual python environment, install the required python packages, and create a Auto-Meeting-Subs.app in the applications folder allowing it to be found via Finder or Spotlight.

## Initial Set Up for Auto-Meeting-Subs
When you are going to run the program for the first time it will start by installing other dependencies it needs such as ffmpeg (for video and audio compression) and ollama (for Local AI summaries). This make take a few minutes and may ask you for sudo permissions when installing ollama.<br/>
It will then prompt you for the initial set up.![intial setup](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/746e9a86-f1bf-4950-81e7-796c232b44af)

1. You are now going to be asked to for the Hugging Face Api token. You can get this token from [here](https://huggingface.co/settings/tokens) Make sure that you have followed the steps instructions for [Setting up WhisperX](#setting-up-whisperx) 
2. Now you are going to be asked where you would like the recording and subtitles to be outputed to. This is wherever you would like things to be saved. I suggest navigating in file explorer to the location on your computer that you would like the meetings to be saved, for example `C:\Users\Alvin Leluc\Videos\Meetings` and simply copy the directory in the adress bar of file explorer. Do not stress about this too much as it will prompt you if you would like to change it everytime it runs.![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/db7f140f-f85f-46aa-9bdf-c3de8552b276)
3. If your meetings are going to be in english simply answer "y".
  If the meetings are in any other language than english answer"n" and the program will automatically detect the spoken language.
<br />
4. Finally you are going to asked wich subtitle format you would like to use.<br />
    * srt: (recommend) since it is a very light weight format that is commonly used for movie subtitles. Includes time stamps.
    * vtt: this is also fairly light weight subtitle format that is commonly used for online videos such as youtube. Includes time stamps.
    * txt: is more of a transcript and does not seperate people and no time stamps.
    * tsv: no seperations between people. Includes time stamps but unclear.
    * json: if you need json subtitles then you know who you are.
    * aud: seperates people and includes time stamps.
   You can see how the different files look in the [Example Subtitle files with video](https://github.com/AstroPhysX/Auto-Meeting-Subs/tree/main/Example%20Subtitle%20files%20with%20video)
<br /> 
You are done setting up Auto-Meeting-Subs!!!<br /> <br />

If at anytime you would like to change the settigns that you setup for Auto-Meeting-Subs, you can simply delete the config.ini file in 
  - Linux: ```"$HOME/.local/share/auto-meeting-subs```
  - Windows: ```C:\Users\<YourUsername>\AppData\Local\Auto-Meeting-Subs```
  - Mac: ```/home/your-username/.local/share/Auto-Meeting-Subs```

This will reset all the configurations you made when you first ran the program, and the next time you run the program you will go through the initial setup process again. **Try doing this if you are running into any sort of issues**<br />

# Debuging
If you run the program and get the Errors or crashes such as the following:
![debug](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/0b3d5dcb-7f2b-400d-8168-57497221797c)

You are going to want to go into the config.ini file found in:
  - Linux: ```"$HOME/.local/share/auto-meeting-subs```
  - Windows: ```C:\Users\<YourUsername>\AppData\Local\Auto-Meeting-Subs```
  - Mac: ```/home/your-username/.local/share/Auto-Meeting-Subs```<br/>
to be able to turn on the debugging mode and see errors. You can do this by going to the location that Auto-Meeting-Subs.exe is saved and open up the config.ini file using using your favorite text editor (try to avoid using word use something more lightweight like notepad).

![config ini loc](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/6b9faf96-f1d7-47b1-8496-c06966e69e86)

Change the very last line where it says `developer_debug = n` to `developer_debug = y`
![developer_debug](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/62c9fe9c-5edc-41c7-937a-acc2fec903f3)

Now when you run the program you will see all the errors that may occur when running ffmpeg, Whisperx or even handbrake.
# Upcoming feature/changes
- [x] Implement Whisperx directly into the code without needing to use CLI version
    - [x] use num_speakers in the diarize.py file instead of the min and max speakers since speaker-diarization-3.1 does not work well with those arguments
- [x] Allow user to input any video or audio file type
- [ ] Fix date issue if date is already in the name of the file and does not correspond with the date of the file
- [x] implement a way to disable compression of video if requested (done via config.ini)
- [x] Updated to newer whisperx version
- [x] Include local Summarizer for meetings
- [x] Make cross platform compatible
- [ ] Make Graphical User Interface for application
    - [ ] Single processing
    - [ ] Batch processing
- [ ] User inputs transcript in any format skips to Summarizer automatically
# Uninstalling Everything
### Linux
1. Navigate to ```"$HOME/.local/share/auto-meeting-subs``` either via file manager (may require enabling seeing hidden files) or console
2. Open a terminal in this location and run ```./uninstall.sh```
3. The program should now be deleted. Although some of dependencies won't be deleted such as **ollama which may be used by other programs that you have installed in the meantime**. If you are sure that no other programs are using you can uninstall
  * Ollama
    1. Remove ollama services: 
      ```
      sudo systemctl stop ollama
      sudo systemctl disable ollama
      sudo rm /etc/systemd/system/ollama.service
      ```
    2. Remove binaries and libraries:
      ```
      sudo rm -r $(which ollama | tr 'bin' 'lib')
      sudo rm $(which ollama)
      ```
    3. Remove models and service users:
      ```
      sudo userdel ollama
      sudo groupdel ollama
      sudo rm -r /usr/share/ollama
      ```
### Windows
1. Navigate to ```C:\Users\<YourUsername>\AppData\Local\Auto-Meeting-Subs``` via file explorer
2. Double click on ```uninstall.bat```
3. The program should now be deleted. Although some of dependencies won't be deleted such as **ollama which may be used by other programs that you have installed in the meantime**. If you are sure that no other programs are using you can uninstall
  * Ollama
    - Uninstall via the control panel
### Mac
1. Navigate to ```/home/your-username/.local/share/Auto-Meeting-Subs``` either via file manager (may require enabling seeing hidden files) or terminal
2. Open a terminal if not opened already and run ```./uninstall.command```
3. The program should now be deleted. Although some of dependencies won't be deleted such as 
**ollama which may be used by other programs that you have installed in the meantime**. If you are sure that no other programs are using you can uninstall
  * Ollama
    - In terminal run 
      ```
      sudo rm -rf /Applications/Ollama.app
      sudo rm /usr/local/bin/ollama
      rm -rf "~/Library/Application Support/Ollama"
      rm -rf "~/Library/Saved Application State/com.electron.ollama.savedState"
      rm -rf ~/Library/Caches/com.electron.ollama/
      rm -rf ~/Library/Caches/ollama
      rm -rf ~/Library/WebKit/com.electron.ollama
      rm -rf ~/.ollama  
      ```
# Special Thanks to the following Projects
Without the work that m-bain and his team have put in this would not be possible.<br />
[m-bain/whisperX](https://github.com/m-bain/whisperX) <br />
As well as the work from the Ollama team <br />
[ollama/ollama](https://github.com/ollama/ollama) <br />
And finally ffmpeg which allows us to convert audio and video with ease<br />
[FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) <br />

