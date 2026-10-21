
How to use:

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

6. create three(3) txt files:

   ```
   main.txt
   historySuccess.txt
   historyFailed.txt
   ```

7. copy and paste one or multiple YT links on "main.txt", for example:

   ```
   https://ytdotcom//link1
   https://ytdotcom//link2
   https://ytdotcom//link3
   ```

8. save, then open vscode terminal

9. run "py download.py"

NOTE:

on line 17, it is currently set at "SONGS_DIR = Path("D:/Songs")", if you want to download mp3s to a different directory, just change this line,

also, do not put the whole folder on somewhere that onedrive touches, it might cause errors and problems, just put the folder on drive C
