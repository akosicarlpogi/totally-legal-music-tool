## DISCLAIMER

This project is intended for educational and personal use. Users are responsible for ensuring they have the necessary rights or permissions to download content. The developer does not encourage copyright infringement or violations of applicable platform terms.

## How to use:

1. open vscode terminal
2. git clone https://github.com/akosicarlpogi/totally-legal-music-tool.git
3. cd totally-legal-music-tool
4. py -m pip install -r requirements.txt
5. winget install Gyan.FFmpeg
   verify installation:

   ```
   ffmpeg -version
   ffprobe -version
   ```
7. create the main txt file on the same folder:

   ```
   main.txt
   ```
8. copy and paste one or multiple YT links on "main.txt", for example:

   ```
   https://ytdotcom//link1
   https://ytdotcom//link2
   https://ytdotcom//link3
   ```
9. save, then open vscode terminal
10. run "py download.py"

## NOTES:

1. on line 17, it is currently set at "SONGS_DIR = Path("D:/Songs")", if you want to download mp3s to a different directory, just change this line, 
2. do not put the whole folder on somewhere that onedrive touches, it might cause errors and problems, just put the folder on drive C, 
3. history of success and failed downloads are recorded on two(2) txt files that are automatically created once the python script has been run
