from pathlib import Path
from urllib.parse import urlparse, parse_qs
from tempfile import TemporaryDirectory
import json
import os
import re
import shutil
import subprocess
import time
import yt_dlp

BASE_DIR = Path(__file__).resolve().parent

SUCCESS_FILE = BASE_DIR / "historySuccess.txt"
FAILED_FILE = BASE_DIR / "historyFailed.txt"
MAIN_FILE = BASE_DIR / "main.txt"
SONGS_DIR = Path("D:/Songs")

SONGS_DIR.mkdir(parents=True, exist_ok=True)

DURATION_TOLERANCE = 2
SIZE_TOLERANCE = 0.02

def video_key(url):
    url = url.strip()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    video_id = None

    if host in (
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com"
    ):
        if parsed.path == "/watch":
            video_id = parse_qs(
                parsed.query
            ).get("v", [None])[0]

        elif parsed.path.startswith(("/shorts/", "/live/")):
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                video_id = parts[1]

    elif host in ("youtu.be", "www.youtu.be"):
        video_id = parsed.path.strip("/").split("/")[0]

    return "youtube:" + video_id if video_id else url

def read_links(path):
    if not path.exists():
        return []

    links = []
    seen = set()

    for line in path.read_text(
        encoding="utf-8-sig"
    ).splitlines():
        url = line.strip()

        if not url or url.startswith("#"):
            continue

        key = video_key(url)

        if key not in seen:
            seen.add(key)
            links.append(url)

    return links

def write_links(path, links):
    content = "\n".join(links)
    if content:
        content += "\n"

    temporary = path.with_name(path.name + ".tmp")

    for attempt in range(10):
        try:
            temporary.write_text(
                content,
                encoding="utf-8"
            )
            os.replace(temporary, path)
            return

        except PermissionError:
            if attempt == 9:
                raise

            print(f"File busy: {path.name}. Retrying...")
            time.sleep(2)

def remove_link(links, key):
    return [
        url for url in links
        if video_key(url) != key
    ]

def clean_title(title):
    title = re.sub(
        r'[<>:"/\\|?*\x00-\x1f]',
        "_",
        title
    )

    title = title.strip().rstrip(". ")
    title = title[:180].rstrip(". ")

    if not title:
        title = "Untitled"

    if re.match(
        r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)",
        title,
        re.IGNORECASE
    ):
        title = "_" + title

    return title

def get_unique_filename(title):
    name = clean_title(title)
    existing = {
        file.name.casefold()
        for file in SONGS_DIR.glob("*.mp3")
    }

    counter = 0

    while True:
        suffix = f"({counter})" if counter else ""
        filename = f"{name}{suffix}.mp3"

        if filename.casefold() not in existing:
            return SONGS_DIR / filename

        counter += 1

def get_audio_duration(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries",
            "stream=codec_name:format=duration",
            "-of", "json",
            str(path)
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=True
    )

    data = json.loads(result.stdout)

    streams = data.get("streams", [])

    if not streams:
        raise RuntimeError("No audio stream found")

    if streams[0].get("codec_name") != "mp3":
        raise RuntimeError("Audio is not MP3")

    duration = float(
        data.get("format", {}).get("duration", 0)
    )

    if duration <= 0:
        raise RuntimeError("Invalid MP3 duration")

    return duration

def verify_audio(path, expected_duration):
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("MP3 is missing or empty")

    duration = get_audio_duration(path)

    if expected_duration:
        expected = float(expected_duration)
        tolerance = max(10, expected * 0.03)

        if abs(duration - expected) > tolerance:
            raise RuntimeError(
                f"Duration mismatch: "
                f"expected {expected:.1f}s, "
                f"received {duration:.1f}s"
            )

    return duration

def matching_title(path, title):
    expected = clean_title(title).casefold()
    existing = path.stem.casefold()

    if existing == expected:
        return True

    pattern = re.escape(expected) + r"\(\d+\)"

    return re.fullmatch(pattern, existing) is not None

def find_duplicate(title, new_file, new_duration):
    new_size = new_file.stat().st_size

    for existing in SONGS_DIR.glob("*.mp3"):
        if not matching_title(existing, title):
            continue

        try:
            old_duration = get_audio_duration(existing)
            old_size = existing.stat().st_size

            duration_matches = (
                abs(new_duration - old_duration)
                <= DURATION_TOLERANCE
            )

            size_difference = (
                abs(new_size - old_size)
                / max(new_size, old_size)
            )

            size_matches = (
                size_difference <= SIZE_TOLERANCE
            )

            if duration_matches and size_matches:
                return existing

        except (OSError, ValueError, RuntimeError,
                subprocess.SubprocessError):
            continue

    return None

def download_options(folder):
    return {
        "format": "bestaudio/best",
        "outtmpl": str(folder / "%(id)s.%(ext)s"),
        "windowsfilenames": True,
        "noplaylist": True,
        "ignoreerrors": False,
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 5,
        "continuedl": True,
        "overwrites": False,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "0"
        }]
    }

for file in (SUCCESS_FILE, FAILED_FILE, MAIN_FILE):
    if not file.exists():
        file.touch()

if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
    raise SystemExit(
        "ERROR: FFmpeg or FFprobe is missing."
    )

main_links = read_links(MAIN_FILE)
success_links = read_links(SUCCESS_FILE)
failed_links = read_links(FAILED_FILE)

success_keys = {
    video_key(url) for url in success_links
}

failed_keys = {
    video_key(url) for url in failed_links
}

total = len(main_links)

if total == 0:
    print("main.txt is empty. Nothing to download.")
    raise SystemExit(0)

new_downloads = 0
duplicates = 0
skipped = 0
failed_count = 0
interrupted = False
history_error = False
errors = []

print("=" * 55)
print("YOUTUBE MP3 BATCH DOWNLOADER")
print("=" * 55)
print(f"Total links: {total}")
print(f"Previously successful: {len(success_links)}")
print(f"Unresolved failures: {len(failed_links)}")
print(f"Download location: {SONGS_DIR}")
print("=" * 55)

try:
    for index, url in enumerate(main_links, 1):
        key = video_key(url)

        print(f"\n[{index}/{total}] {url}")

        if key in success_keys:
            print("SKIPPED: Link already in success history")
            skipped += 1

            if key in failed_keys:
                failed_links = remove_link(
                    failed_links, key
                )

                failed_keys.discard(key)

                try:
                    write_links(FAILED_FILE, failed_links)
                except OSError as error:
                    print(f"HISTORY ERROR: {error}")
                    history_error = True
                    break

            continue

        try:
            with TemporaryDirectory() as temp:
                temp_folder = Path(temp)

                with yt_dlp.YoutubeDL(
                    download_options(temp_folder)
                ) as ydl:
                    info = ydl.extract_info(
                        url,
                        download=True
                    )

                if not info:
                    raise RuntimeError(
                        "No video information returned"
                    )

                video_id = info.get("id")
                title = info.get("title") or video_id
                expected_duration = info.get("duration")

                if not video_id or not title:
                    raise RuntimeError(
                        "Missing video information"
                    )

                temp_mp3 = temp_folder / f"{video_id}.mp3"

                new_duration = verify_audio(
                    temp_mp3,
                    expected_duration
                )

                duplicate = find_duplicate(
                    title,
                    temp_mp3,
                    new_duration
                )

                if duplicate:
                    print(
                        f"DUPLICATE SKIPPED: {duplicate.name}"
                    )
                    duplicates += 1

                else:
                    destination = get_unique_filename(title)

                    if destination.exists():
                        raise RuntimeError(
                            "Destination filename already exists"
                        )

                    shutil.copy2(temp_mp3, destination)

                    try:
                        verify_audio(
                            destination,
                            expected_duration
                        )
                    except Exception:
                        destination.unlink(missing_ok=True)
                        raise

                    print(f"SUCCESS: {destination.name}")
                    print(
                        f"Duration: {new_duration:.1f} seconds"
                    )

                    new_downloads += 1

            if key not in success_keys:
                success_links.append(url)
                success_keys.add(key)

            write_links(SUCCESS_FILE, success_links)

            if key in failed_keys:
                failed_links = remove_link(
                    failed_links, key
                )

                failed_keys.discard(key)
                write_links(FAILED_FILE, failed_links)

        except KeyboardInterrupt:
            interrupted = True
            print("\nDownload interrupted.")
            break

        except Exception as error:
            if isinstance(error, (PermissionError, OSError)) and (
                key in success_keys
            ):
                print(f"HISTORY ERROR: {error}")
                history_error = True
                break

            print(f"FAILED: {error}")
            errors.append((url, str(error)))
            failed_count += 1

            if key not in failed_keys:
                failed_links.append(url)
                failed_keys.add(key)

            try:
                write_links(FAILED_FILE, failed_links)

            except OSError as save_error:
                print(f"HISTORY ERROR: {save_error}")
                history_error = True
                break

except KeyboardInterrupt:
    interrupted = True
    print("\nBatch interrupted.")

if not interrupted and not history_error:
    try:
        write_links(MAIN_FILE, [])
        print("\nmain.txt has been emptied.")

    except OSError as error:
        print(f"Could not clear main.txt: {error}")

else:
    print(
        "\nmain.txt has been preserved "
        "because the batch did not finish safely."
    )

print("\n" + "=" * 55)
print("DOWNLOAD SUMMARY")
print("=" * 55)

print(f"Total batch links: {total}")
print(f"New MP3 files: {new_downloads}")
print(f"Matching songs skipped: {duplicates}")
print(f"Previously recorded links: {skipped}")
print(f"Failed this batch: {failed_count}")
print(f"Total success history: {len(success_links)}")
print(f"Total unresolved failures: {len(failed_links)}")

print("=" * 55)

if errors:
    print("\nFAILED LINKS:")

    for url, reason in errors:
        print(f"{url}")
        print(f"Reason: {reason}\n")

if history_error:
    print(
        "\nWARNING: A history operation failed. "
        "Check the records before trying again."
    )

print("\nFinished.")