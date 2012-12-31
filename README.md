Warp
====

Warp is an automatic audio file metadata tagger which uses the MusicBrainz Python library musicbrainzngs. Warp is free and open-source, and is released under the GPL license. Warp should work on any platform that runs Python 2.7.

Key Features
------------

* Able to automatically tag any MP3, Ogg Vorbis or FLAC file, that as already been tagged in Picard.
* Able to run recursively on a set of directories - update your whole music library in one command!
* Configurable options file to allow for customization of the tagging process.
* Can save either ID3v2.3 or v2.4 tags, and can remove APEv2 tags from MP3 files.
* Can download cover art from the Cover Art Archive and add to all supported filetypes.
* Can ignore certain directories, if the user creates an empty "warp-ignore" file in the target directory.

Manual
------
**Installation (Dependencies)**

The first thing to do is install the required dependencies, if you don't already have them. These dependencies are:
* Python 2.7
* musicbrainzngs
* mutagen

If you already have all of these, skip to *Installation (Warp)*. Otherwise, read on.

Hopefully in the future, Warp will have a nice installer that'll do all of this for you. But for now, it's a short manual process, varying depending on OS:

**Windows**
* To get Python, please visit http://www.python.org/
* Follow these instructions to get PIP: http://stackoverflow.com/questions/4750806/how-to-install-pip-on-windows
* Open up the command prompt, and type "pip install musicbrainzngs"
* In the same command prompt, type "pip install mutagen"

**Linux and Unix-based OSes**

* First of all, attempt to get everything from your Linux package manager.
 * You'll probably be able to find python easily. On Ubuntu 12.10, you can get it by typing "sudo apt-get install python" in the terminal.
 * On Ubuntu 12.10, musicbrainzngs is available by typing "sudo apt-get install python-musicbrainzngs"
 * On Ubuntu 12.10, mutagen is available as "sudo apt-get install python-mutagen"
* If you can't find all of the packages in your package repository, follow some of these alternative instructions:
 * Get Python from http://www.python.org/
 * Follow these instructions to get PIP: http://www.pip-installer.org/en/latest/installing.html
 * Open the terminal and type "pip install musicbrainzngs"
 * Type "pip install mutagen"

**Installation (Warp)**

* First of all, visit https://github.com/LordSputnik/mb-masstagger and download the entire repository as a zip file.
* Extract the zip file to your preferred location.
* In the new folder, copy "options.default" and rename it to "options", with no extension.
* Edit the file in Notepad or an equivalent text editor (see [[User:LordSputnik/Warp#Editing_the_Options_file|Editing the Options file]]).
* Open the command prompt or terminal in the directory you extracted the files to and type "python warp.py".

**Editing the Options file**

The most important line in the options file is:

''library_folder="xxx"''

You must edit this line to the directory you want to update. The name can be relative to the folder containing warp.py, or an absolute file name (beginning with a drive letter on windows or / on linux).

For example, these are all acceptable:

* *library_folder="C:\Users\My_Username\Music\FLACs"* (scans the absolute directory in Windows)
* *library_folder="/home/my_username/Music/FLACs"* (scans the absolute directory in Linux)
* *library_folder="./"* (scans the relative directory ./)
* *library_folder="temp"* (scans the relative directory ./temp)
