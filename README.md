# YouTube to MP3 Downloader

A lightweight, automated Python script to batch-download YouTube audio streams into MP3 format with built-in duplicate detection and duration validation.

---

## Tech Stack

- **Language:** Python 3.8+
- **Stream Extractor:** yt-dlp
- **Audio Processor:** FFmpeg / ffprobe
- **Core Standard Libraries:** pathlib, subprocess, urllib.parse, tempfile

---

## Project Structure

```text
totally-legal-music-tool/
├── download.py             # Main execution and processing script
├── requirements.txt        # Python package dependencies
├── main.txt                # Input queue (paste YouTube links here)
├── historySuccess.txt      # Log of completed downloads (prevents re-downloading)
├── historyFailed.txt       # Log of failed URLs for retry
└── README.md               # Project documentation
```

---

## Quick Start

```cmd
# 1. Clone repository and navigate inside
git clone https://github.com/akosicarlpogi/totally-legal-music-tool.git
cd totally-legal-music-tool

# 2. Install FFmpeg and Python dependencies
winget install Gyan.FFmpeg
py -m pip install -r requirements.txt

# 3. Add URLs into main.txt, then run
py download.py
```

> **Note:** Restart your terminal or editor after installing FFmpeg so Windows recognizes the updated PATH variable.

---

## How It Works

1. Add YouTube URLs into `main.txt` (one link per line).
2. Execute `py download.py`.
3. The script verifies files, ignores duplicates, and exports `.mp3` tracks to `D:/Songs`.
4. `main.txt` clears automatically once the batch completes safely.

---

<details>
<summary><b>Configuration and Important Notes</b></summary>

- **Change Output Path:** Modify line 17 of `download.py`:
  ```python
  SONGS_DIR = Path("D:/Songs")
  ```
- **File Locks:** Keep the project and target folder outside OneDrive or Google Drive synced directories to avoid file-locking errors.
- **Deduplication:** Tracks are compared against existing filenames and audio duration to prevent redundant downloads.

</details>

<details>
<summary><b>Disclaimer</b></summary>

This tool is created for educational and personal workflow evaluation. Ensure you have the rights or permission from content owners before downloading media.

</details>