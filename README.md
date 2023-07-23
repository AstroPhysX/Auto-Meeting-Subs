# Auto-Meeting-Subs
## Description
Automatically converts meeting subs to WAV file which then runs through an instance of whisperx to create srt subtitles, then compresses the video using handbrakecli. Then moves and renames compressed video file and subtitles to output directory.
The goal behind this program was to simply create a transcript of what people said in a meeting to make my life easier to parse through the meeting and figure out when things were said, that way I can quickly skip to that part of the video or meeting. This prgoram does 3 things: it converts the audioto the WAV format from either and MKV video file or from a WMA audio file (WMA is the format that onenote records in), then the program uses the newly converted audio to run a command in whisperx which creates an SRT subtitle file with speech diarization, once the subtitiles have been created the program then runs handbrake which compress the video file, finally the program renames the video and subtitle file to "Meeting yy.mm.dd" where the date is creation date of the file.
# Install process
There are 3 prerequisite programs to run this program. These programs are ffmpeg, whisperX and Handbrakecli. we will start with the easiest thing to install and install the hardest thing last.
### Installing ffmpeg
Start by going to this website: [https://ffmpeg.org/download.html#build-windows](https://github.com/BtbN/FFmpeg-Builds/releases)
![image](https://github.com/AstroPhysX/Auto-Meeting-Subs/assets/67988361/d64fcdcc-9708-41f9-87ff-57981f6cb69b)
Once you have downloaded this extract it and move that folder to a safe location i.e. a location where you are not going to delete it meaning somewhere outside of your downloads folder. **Remeber this location you will be needing it later**<br />
You're now done with the first program installed.
### Installing Handbrake
Handbrake is going to be a little bit more complicated. If you feel very comfortable with the command line then all you need to download is the Handbrakecli. <br />
To make your life extremely easy I highly recommend downloading both Handbrake (Graphical User Interface GUI) and Handbrakecli.<br />
Handbrake (GUI): https://handbrake.fr/downloads.php <br />
Handbrakecli: https://handbrake.fr/downloads2.php <br />
When downloading you will have the option between a portable or an installer, you can choose either one. The portable version just means it is self contained and does not need to be installed on the machine (can run on just a usb). I would recommend sticking to the installed since whisperX will need to be installed on your machine.
Now run the installer and install handbrake anywhere you would like, but **Remeber where you install it for our next step**<br />
Extract the Handbrakecli, and copy what is inside to the folder where you just installed the Handbrake. This will allow to have everything Handbrake related in on place.
### Installing WhisperX
Now this is by far the hardest thing to install. We will be installing
