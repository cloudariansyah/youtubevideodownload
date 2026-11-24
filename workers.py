import threading
import urllib.request
import yt_dlp
from PySide6.QtCore import QThread, Signal


def format_eta_seconds(value):
    """Format ETA seconds without relying on removed yt-dlp utility APIs."""
    if value is None:
        return "-"
    seconds = max(0, int(value))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


class InfoWorker(QThread):
    info_ready = Signal(dict, bytes)
    error = Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "noplaylist": True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

            thumbnail_data = b""
            thumbnail_url = info.get("thumbnail")
            if thumbnail_url:
                request = urllib.request.Request(
                    thumbnail_url,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                try:
                    with urllib.request.urlopen(request, timeout=15) as response:
                        thumbnail_data = response.read()
                except Exception:
                    thumbnail_data = b""

            self.info_ready.emit(info, thumbnail_data)
        except Exception as exc:
            self.error.emit(str(exc))


class DownloadWorker(QThread):
    progress = Signal(dict)
    completed = Signal(str)
    error = Signal(str)

    def __init__(self, url, output_dir, audio, quality):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.audio = audio
        self.quality = quality
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            def progress_hook(data):
                if self.cancel_event.is_set():
                    raise yt_dlp.utils.DownloadError(
                        "Download dibatalkan oleh pengguna."
                    )

                if data.get("status") == "downloading":
                    total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                    downloaded = data.get("downloaded_bytes") or 0
                    percent = (downloaded / total * 100) if total else 0
                    speed_value = data.get("speed")
                    try:
                        speed = f"{yt_dlp.utils.format_bytes(speed_value)}/s" if speed_value else "-"
                    except Exception:
                        speed = f"{speed_value / 1024 / 1024:.2f} MB/s" if speed_value else "-"

                    self.progress.emit({
                        "percent": percent,
                        "speed": speed,
                        "eta": format_eta_seconds(data.get("eta")),
                    })

                elif data.get("status") == "finished":
                    self.progress.emit({
                        "percent": 100,
                        "speed": "-",
                        "eta": "Memproses file…",
                    })

            common = {
                "outtmpl": self.output_dir + "/%(title).180B.%(ext)s",
                "noplaylist": True,
                "progress_hooks": [progress_hook],
                "quiet": True,
            }

            if self.audio:
                opts = {
                    **common,
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                }
            else:
                height = {
                    "1080p": 1080,
                    "720p": 720,
                    "480p": 480,
                    "360p": 360,
                }.get(self.quality)

                if height:
                    fmt = f"bv*[height<={height}]+ba/b[height<={height}]"
                else:
                    fmt = "bv*+ba/b"

                opts = {
                    **common,
                    "format": fmt,
                    "merge_output_format": "mp4",
                }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=True)

                # Prefer the post-processed path when yt-dlp provides it.
                filepath = info.get("filepath")
                if not filepath:
                    filepath = ydl.prepare_filename(info)

                if self.audio:
                    filepath = str(__import__("pathlib").Path(filepath).with_suffix(".mp3"))
                else:
                    filepath = str(__import__("pathlib").Path(filepath).with_suffix(".mp4"))

            if self.cancel_event.is_set():
                self.error.emit("Download dibatalkan oleh pengguna.")
            else:
                self.completed.emit(filepath)

        except Exception as exc:
            message = str(exc)
            if self.cancel_event.is_set():
                message = "Download dibatalkan oleh pengguna."
            self.error.emit(message)
