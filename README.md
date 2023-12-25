# Auto-Meeting-Subs
## Description
Automatically converts meeting subs to WAV file which then runs through an instance of whisperx to create srt subtitles, then compresses the video using handbrakecli. Then moves and renames compressed video file and subtitles to output directory.<br /><br />
The goal behind this program was to simply create a transcript of what people said in a meeting to make my life easier to parse through the meeting and figure out when things were said, that way I can quickly skip to that part of the video or meeting. This prgoram does 3 things: it converts the audioto the WAV format from either and MKV video file or from a WMA audio file (WMA is the format that onenote records in), then the program uses the newly converted audio to run a command in whisperx which creates a subtitle file with speech diarization, once the subtitiles have been created the program then runs handbrake which compress the video file, finally the program renames the video and subtitle file to "Meeting yy.mm.dd" where the date is creation date of the file.
# Install process
There are 3 prerequisite programs to run this program. These programs are ffmpeg, whisperX and Handbrakecli. We will start with the easiest thing to install and install the hardest thing last.
### Installing ffmpeg
Start by going to this website: [https://ffmpeg.org/download.html#build-windows](https://github.com/BtbN/FFmpeg-Builds/releases)
![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/d64fcdcc-9708-41f9-87ff-57981f6cb69b)
Once you have downloaded this extract it and move that folder to a safe location i.e. a location where you are not going to delete it meaning somewhere outside of your downloads folder. **Remeber this location, you will be needing it later**<br /> 
You're now done with the first program installation.
### Installing Handbrake and Setting up handrake
Handbrake is going to be a little bit more complicated.To make your life extremely easy I recommend downloading both Handbrake (Graphical User Interface GUI) and Handbrakecli.<br />
Handbrake (GUI): https://handbrake.fr/downloads.php <br />
**AND** <br />
Handbrakecli: https://handbrake.fr/downloads2.php <br />
When downloading you will have the option between a portable or an installer, you can choose either one. The portable version just means it is self contained and does not need to be installed on the machine (can run on just a usb). I would recommend sticking to the installer since whisperX will need to be installed on your machine anyways.<br />
Now run the installer and install handbrake anywhere you would like, but **Remeber where you install it, for our next steps**<br />
#### Setting up Handbrakecli
Extract the Handbrakecli, and copy what is inside to the folder where you just installed the Handbrake (typically located at `C:\Program Files\HandBrake`). This will allow you to have everything Handbrake related in one place.
#### Setting up Handbrake
Double click the Handbrake icon on your desktop or double click the HandBrake.exe file in the location you installed it and open handbrake.<br />
Using the GUI you can setup the compression however you would like. Everytime you open handbrake you will be greeted with this: ![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/a54d840e-1ea3-49d3-9af2-96d61891f9df) <br />
You will want to open any video you might have on your computer, it doesn't really matter what it is since we are mainly going to setup the handbrake preset that we will be using with Auto-Meeting-Subs.exe.<br />
There are various settings that you can change in handbrake.
I have found from running multiple tests that best settings for my use case has been the following:
* Summary Tab
  * Format :MKV
* Dimensions Tab
  * Cropping :Custom with top,Left,Right,Bottom=0 <br /> ![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/9d23cba2-a13c-4669-8e7c-7fc65f1bb992)
* Video Tab
  * Video Codec: nvenc H.265
  * Framerate (FPS): same as source Variable Framerate
  * Encoding Preset: Fast
  * Encoding Profile: Auto
  * Encoding Level: Auto
  * Avg Bitrate (kbps): 1500
* Audio Tab
  * Codec: Auto Passthru
Now click on "Save preset" and save it with the whatever name you would like, but **remeber the preset name since you will be needing it later**. I have it saved as "Meetings". See picture on how to save preset: ![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/937654ec-dfb6-4628-83af-a78d28cfcfc3) <br />
You can now exit Handbrake and move on to the next step.
### Installing Git
You may not need to install this if you already you already use git but just in case. Download git from [here](https://git-scm.com/downloads)
Now go through the install process and don't change any settings.
## Installing Conda and Setting Environment Variables
Now this is by far the hardest thing to install. We will be installing anaconda or miniconda first which is a virtual enironment where whisperx is going to live. If you don't know the differnece between miniconda and anaconda, the main difference is that anaconda comes with more data science packages. <br /> 
So if you don't plan on having any other use for anaconda/miniconda besides for this program, **I reccommend using miniconda.** <br />
Anaconda: https://www.anaconda.com/download <br/>
**OR** <br />
Miniconda: https://docs.conda.io/projects/miniconda/en/latest/miniconda-other-installer-links.html ![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/363d2ebc-46e3-4685-bfe6-58627fda3c69) <br/>
1. Download either anaconda or miniconda (see above description for the difference)<br/>
2. Run the .exe file you just downloaded and install anaconda with all the default settings.<br />
3. Once installed go to your start menu and type "anaconda prompt" ![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/d3ee4212-676d-4f95-87c9-07a53e923ae2) <br/>
4. Now type the following command `where conda` this will give you 3 directories on where conda is located. We are going to need this in the next step, so leave the anaconda prompt open.<br/>
5. Similarly we need to find the location of git, go to your start menu and type "git bash" ![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/a7617f3c-9ba2-4126-ba74-947fcc8ed4f6) <br />
6. Now type the following command `where git` this will give you 2 directories on where git is located. We are going to need this in the next step, so leave the gjit bash open.
7. Go back to the start menu and type "View advanced system settings"![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/e4a56773-95f2-45ef-b2a9-66670f1e08d8) <br/>
8. Click on "Environment Variables..." then select "Path" in the top list and click on "Edit...". Finally Click on "New" and copy each of the directories that the `where conda` command spit out and those from `where git` (You will have click New for each directory listed in the ananconda prompt and bash). When you have added each directory to the list click "OK" then "OK" then "Apply"<br />
The directories should look something like the following assuming you installed them in the default locations:
Miniconda
`C:\Users\Robert\miniconda3`<br />
`C:\Users\Robert\miniconda3\Scripts`<br />
`C:\Users\Robert\miniconda3\Library\bin`<br />
git
`C:\Program files\Git\mingw64\bin\`<br />
`C:\Program files\Git\cmd\`<br />
We also are going to want to add ffmpeg to the enviroment varibles so you will need to find out where you extracted ffmpeg.<br />
![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/46519a0d-d16f-4ce1-be9e-12ebd83fbf95) <br/>
10. You can now exit the anaconda command prompt and git bash. Open a normal command prompt by typing "cmd" in the start menu and run `conda --version`. If you get a result that says something like "conda xx.x.x" where the x's are the version number then you have installed conda successfully!
11. Similarly you want to test if git is installed properly by typing `git --version`. If you get a result saying something like "git version x.xx.x.windows.1" then you have successfully installed git!
12. Lastly we want to test if ffmpeg is installed correctly by typing `ffmpeg -version`. If you get a result saying something like "ffmpeg version N-111069-g41229ef705-20230615 Copyright (c) 2000-2023 the FFmpeg developers" then you have successfully installed ffmpeg!
### Installing WhisperX
1. Lets create the environment for where whisperx is going to live. For this part I am going to follow the installation guide from [m-bain/whisperx](https://github.com/m-bain/whisperX) <br />
Start by running the command `conda create --name whisperx python=3.10` <br />
Activate the environment `conda activate whisperx`<br />
(In the example below I called my environment "test" yours should be named whisperx
![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/f10e8f68-2db8-47d7-a916-92559b9eac83) <br />
2. Before installing whisperx in this environment we need to install all the tools that it uses with the following command if you have an nvidia:<br /> `conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia`<br /><br /> Unfortunately, if you are using an AMD graphics card you will have do some research if they have implemented pytorch recently otherwise you can use the following command if you are on AMD or if you don't have a GPU:<br /> `conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 cpuonly -c pytorch`
3. And finally we can install whisperx: `pip install git+https://github.com/m-bain/whisperx.git`
4. **Optional:** If you are going to modify the source code or python file and want to later convert eh modified python code you can compile the code using auto-py-to-exe. Run the following command: `pip install auto-py-to-exe` We will be using this later to compile our program, that way we can simply run a single .exe file. To compile your new python code you will need to run `conda activate whisperx && auto-py-to-exe` then you can select the "one file" option that way you have a single .exe file.
## Setting up whisperX
We now need to set up speaker Diarization for whisperX. You will need to generate a Hugging Face access token that you can generate here:<br /> [Hugging Face API Token](https://huggingface.co/settings/tokens) <br /> If you don't have an account go through the process to sign up for a free account. Then click on "New Token", the role can be set to read and name the token however you would like. **Copy the token somewhere safe, we will be using it later during the initial setup of Auto-Meeting-Subs.exe**<br />
![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/e32daa8e-594e-406b-b2fc-f2b073a35cf7)
**IMPORTANT:** You will now need to go to each of the following links and accept the user agreements for these models:<br />
Segmentation: https://huggingface.co/pyannote/segmentation <br />
Voice Activity Detection (VAD): https://huggingface.co/pyannote/voice-activity-detection <br />
Speaker Diariztion: https://huggingface.co/pyannote/speaker-diarization <br /><br />

**Optional for people that want more control on how to run whisperX** 
You can build a command for whisperx which you can implement into the python code, but you will need to compile it into an exe file using auto-py-to-exe. Here is a text document that has a table in it describing all the possible commands you may want to use: [WhisperX commands](https://github.com/AstroPhysX/Auto-Meeting-Subs/blob/main/WhisperX%20commands.txt)
I have found that the following command has worked quite well for my use case:<br/>
`whisperx "{output_wav_file}" -o "{output_dir}" -f srt --diarize --max_speakers {num_speakers} --hf_token {token} --model medium.en {compute_type_otpions}`
## Setting up Auto-Meeting-Subs
Start by downloading Auto-Meeting-Subs.exe from [here](https://github.com/AstroPhysX/Auto-Meeting-Subs/releases). See picture on where to click to download. ![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/d3d48cfe-ba05-48cc-976a-85a28ea58f1d) <br /><br />

I recommend you save the exe file in a safe place and somewhere where it is self contained i.e. in its own folder.<br />
When you are going to run the program for the first time it is going to prompt you for the initial set up.![intial setup](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/746e9a86-f1bf-4950-81e7-796c232b44af)

1. It is going to ask you for the location of ffmpeg which was the first program we downloaded and extracted. You go to that folder, then go into the bin folder and then you drag and drop the ffmpeg.exe file into the command prompt.
2. Next thing it is going to ask you is for the HandbrakeCLI.exe location. If you follwoed the instructions the HandbrakeCLI should be in the same location that Handbrake was installed to, otherwise it may be in your downloads directoy. Note handbrake normally installs to C:\Program Files\Handbrake\. Similarly to ffmpeg.exe you can drag and drop the HandBrakeCLI.exe file into the command prompt.
3. You will now be asked the name of the Handbrake preset you made in the Handbrake GUI. If you named it that the same thing as me then this should be "Meetings"
4. You are now going to be asked to for the Hugging Face Api token. You can get this token from [here](https://huggingface.co/settings/tokens) Make sure that you have followed the steps instructions for [Setting up WhisperX](#setting-up-whisperx) 
5. Now you are going to be asked where you would like the recording and subtitles to be outputed to. This is wherever you would like things to be saved. I suggest navigating in file explorer to the location on your computer that you would like the meetings to be saved, for example `C:\Users\Alvin Leluc\Videos\Meetings` and simply copy the directory in the adress bar of file explorer.![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/db7f140f-f85f-46aa-9bdf-c3de8552b276)
6. It is going to ask you for the initial configuration is if you have an NVIDIA GPU simply answer "y" or "n".<br />
    * If you do not know and used the command `conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia` while installing WhisperX then enter y. 
    * If instead you have an AMD GPU, no GPU, or even if you ran this command `conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 cpuonly -c pytorch` during the the WhisperX installation enter n.
<br />
7. If your meetings are going to be in english simply answer "y".
  If the meetings are in any other language than english answer"n" and the program will automatically detect the spoken language.
<br />
8. Finally you are going to asked wich subtitle format you would like to use.<br />
    * srt: (recommend) since it is a very light weight format that is commonly used for movie subtitles. Includes time stamps.
    * vtt: this is also fairly light weight subtitle format that is commonly used for online videos such as youtube. Includes time stamps.
    * txt: is more of a transcript and does not seperate people and no time stamps.
    * tsv: no seperations between people. Includes time stamps but unclear.
    * json: if you need json subtitles then you know who you are.
    * aud: seperates people and includes time stamps.
   You can see how the different files look in the [Example Subtitle files with video](https://github.com/AstroPhysX/Auto-Meeting-Subs/tree/main/Example%20Subtitle%20files%20with%20video)
<br /> 
You are done setting up Auto-Meeting-Subs!!!<br /> <br />

If at anytime you would like to change the settigns that you setup for Auto-Meeting-Subs.exe, you can simply delete the config.ini file that is in the same folder at Auto-Meeting-Subs.exe. This will reset all the configurations you madewhen you first ran the program, and the next time you run the program go through the initial setup process again. **Try doing this if you are running into any sort of issues**<br />

# Debuging
If you run the program and get the following message:
![debug](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/0b3d5dcb-7f2b-400d-8168-57497221797c)

You are going to want to go into the config.ini file to be able to turn on the debugging mode and see errors. You can do this by going to the location that Auto-Meeting-Subs.exe is saved and open up the config.ini file using notepad.
![config ini loc](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/6b9faf96-f1d7-47b1-8496-c06966e69e86)

Change the very last line where it says `developer_debug = n` to `developer_debug = y`
![developer_debug](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/62c9fe9c-5edc-41c7-937a-acc2fec903f3)

Now when you run the program you will see all the errors that may occur when running ffmpeg, Whisperx or even handbrake.
# Uninstalling Everything
1. Start by deleting both the Auto-Meeting-Subs.exe and the config.ini files.
2. Go to your command prompt, by going the start menu and typing cmd and open a command prompt and type the following command <br /> `conda remove --name whisperx --all`
3. Go back to the start menu, type "Control Panel", and click on "Control Panel". Once the control panel is open go to the top right and type in the search bar and type "Uninstall a program" and click on "Uninstall a program"<br /> ![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/ac7e3f2e-8136-4865-9838-6aa6bbea2191)
4. Now in the Uninstaller window go to the top right and type "Anaconda", right click the program and click "Uninstall/Change". You will then be guided through an uninstaller.
5. Still in the Control panel uninstaller window search "Handbrake" and right click on the program and click "Uninstall/Change". Similarly to anaconda you will be guided throguh an uninstaller.
6. Finally delete the ffmpeg folder from wherever you had extracted it.
The program is now completely uninstalled.
# Special Thanks to the following Projects
Without the work that m-bain and his team have put in this would not be possible.<br />
[m-bain/whisperX](https://github.com/m-bain/whisperX) <br />
As well as the work from the HandBrake team <br />
[HandBrake/HandBrake](https://github.com/HandBrake/HandBrake) <br />
And finally ffmpeg which allows us to convert audio and video with ease<br />
[FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) <br />

