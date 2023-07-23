# Auto-Meeting-Subs
## Description
Automatically converts meeting subs to WAV file which then runs through an instance of whisperx to create srt subtitles, then compresses the video using handbrakecli. Then moves and renames compressed video file and subtitles to output directory.
The goal behind this program was to simply create a transcript of what people said in a meeting to make my life easier to parse through the meeting and figure out when things were said, that way I can quickly skip to that part of the video or meeting. This prgoram does 3 things: it converts the audioto the WAV format from either and MKV video file or from a WMA audio file (WMA is the format that onenote records in), then the program uses the newly converted audio to run a command in whisperx which creates an SRT subtitle file with speech diarization, once the subtitiles have been created the program then runs handbrake which compress the video file, finally the program renames the video and subtitle file to "Meeting yy.mm.dd" where the date is creation date of the file.
# Install process
There are 3 prerequisite programs to run this program. These programs are ffmpeg, whisperX and Handbrakecli. we will start with the easiest thing to install and install the hardest thing last.
## Installing ffmpeg
Start by going to this website: [https://ffmpeg.org/download.html#build-windows](https://github.com/BtbN/FFmpeg-Builds/releases)
![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/d64fcdcc-9708-41f9-87ff-57981f6cb69b)
Once you have downloaded this extract it and move that folder to a safe location i.e. a location where you are not going to delete it meaning somewhere outside of your downloads folder. **Remeber this location you will be needing it later**<br />
You're now done with the first program installed.
## Installing Handbrake and Setting up handrake
Handbrake is going to be a little bit more complicated. If you feel very comfortable with the command line then all you need to download is the Handbrakecli. <br />
To make your life extremely easy I highly recommend downloading both Handbrake (Graphical User Interface GUI) and Handbrakecli.<br />
Handbrake (GUI): https://handbrake.fr/downloads.php <br />
Handbrakecli: https://handbrake.fr/downloads2.php <br />
When downloading you will have the option between a portable or an installer, you can choose either one. The portable version just means it is self contained and does not need to be installed on the machine (can run on just a usb). I would recommend sticking to the installed since whisperX will need to be installed on your machine.
Now run the installer and install handbrake anywhere you would like, but **Remeber where you install it for our next step**<br />
Extract the Handbrakecli, and copy what is inside to the folder where you just installed the Handbrake. This will allow to have everything Handbrake related in on place.
### Setting up Handbrake
If you decided on only installing the Handbrakecli and not the GUI then you can look at the commands online here:[Handbrakecli commands](https://handbrake.fr/docs/en/latest/cli/command-line-reference.html)<br />
Assuming that you have installed the GUI you can setup the compression however you would like. I have found from running multiple tests that best settings for my use case has been the following:
* File Container:MKV
* Keep the resolution the same as original
* Encoding: nvenc H.265
* FPS: same as source
* Encoding speed: Fast
* Encoding level: Auto
* Average bitrate: 1500 kb/s
* Audio: Passthrough
## Installing WhisperX
Now this is by far the hardest thing to install. We will be installing anaconda or miniconda first which is a virtual enironment where whisperx is going to live. If you don't know the differnece between miniconda and anaconda, the main difference is that anaconda comes with more data science packages. <br /> 
So if you don't plan on having any other use for anaconda/miniconda besides for this program, **I reccommend using miniconda.** <br />
Anaconda: https://www.anaconda.com/download <br/>
Miniconda: https://docs.conda.io/en/latest/miniconda.html ![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/363d2ebc-46e3-4685-bfe6-58627fda3c69) <br/>
1. Download either anaconda or miniconda (see above description for the difference)<br/>
2. Run the .exe file you just downloaded and install anaconda with all the default settings.<br />
3. Once installed go to your start menu and type "anaconda prompt" ![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/d3ee4212-676d-4f95-87c9-07a53e923ae2) <br/>
4. Now type the following command `where conda` this will give you 3 directories on where conda is located. We are going to need this in the next step, so leave the prompt open.<br/>
5. Go back to the start menu and type "View advanced system settings"![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/e4a56773-95f2-45ef-b2a9-66670f1e08d8) <br/>
6. Click on "Environment Variables..." then select "Path" in the top list and click on "Edit...". Finally Click on "New" and copy each of the directories that the `where conda` command spit out (You will have click New for each directory listed in the ananconda prompt). When you have added each directory to the list click "OK" then "OK" then "Apply"![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/46519a0d-d16f-4ce1-be9e-12ebd83fbf95) <br/>
7. You can now exit the anaconda command prompt. And open a normal command prompt by typing "cmd" in the start menu and run `conda --version`. If you get a result that says something like "conda xx.x.x" where the x's are the version number then you have installed conda successfully!
8. Lets create the environment ofr where whisperx is going to live. for this part I am going to follow the installation guide from https://github.com/m-bain/whisperX <br />
Start by running the command `conda create --name whisperx python=3.10` <br />
Activate the environment `conda activate whisperx`<br />
(In the example below I called my environment "test"
![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/f10e8f68-2db8-47d7-a916-92559b9eac83) <br />
9. Before installing whisperx we need to install all the tools that it uses with the following command if you have an nvidia:<br /> `conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia`<br /><br /> Unfortunately if you are using an AMD graphics card you will have do some research if they have implemented pytorch recently otherwise you can use the following command if you are on AMD:<br /> `conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 cpuonly -c pytorch`
10. And finally we can install whisperx: `pip install git+https://github.com/m-bain/whisperx.git`
11. Finally run the following command: `pip install auto-py-to-exe` We will be using this later to compile our program, that way we can simply run a single .exe file.
# Setting up whisperX
For speaker Diarization you will need to generate a Hugging Face access token that you can generate here: [https://huggingface.co/join?next=%2Fsettings%2Ftokens](https://huggingface.co/settings/tokens)https://huggingface.co/settings/tokens <br /> If you don't have an account go through the process to sign up for a free account. Then click on "New Token", the role can be set to read and name the token however you would like. **Copy the token we will be using it to create our whisperx command**<br />
You will now need to go to each of the following links and accept the user agreements for these models:<br />
Segmentation: https://huggingface.co/pyannote/segmentation <br />
Voice Activity Detection (VAD): https://huggingface.co/pyannote/voice-activity-detection <br />
Speaker Diariztion: https://huggingface.co/pyannote/speaker-diarization <br /><br />

We can now build a command for whisperx which we will be using later on when we setup the python code. Here is a text document that has a table in it describing all the possible commands you may want to use: [WhisperX commands](https://github.com/AstroPhysX/Auto-Meeting-Subs/blob/main/WhisperX%20commands.txt)
I have found that the followingcommand has worked quite well for my use case:<br/>
`whisperx "{output_wav_file}" -o "{output_dir}" -f srt --diarize --max_speakers {num_speakers} --hf_token {token_here} --model medium.en`
## Setting up the Python code to work for you
Start by downloading the python code from my repo: [Python file](https://github.com/AstroPhysX/Auto-Meeting-Subs/blob/main/Auto%20Research%20meeting%20subs%20mkv%20or%20wma.py)<br />
There are alot of things that you will be needing to setup in this python code prior to being able to use it.<br />
1. Open the python file in some form of text editor either notepad++ or in my case I am using VScode
2. Starting from the top of the code, we need to change the install location for ffmpeg. Find the directory or location of where you installed ffmpeg, copy and paste this location into the python code where it says "ffpeg_path=". See image below if confused.![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/709e4727-c683-45d3-b9c3-47bbc315f536)
3. 
