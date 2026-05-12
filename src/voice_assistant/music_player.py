import logging
import os
import shutil
import subprocess
import threading


def _find_mpv() -> str | None:
    """Locate mpv binary cross-platform (Windows + Linux/ARM)."""
    on_path = shutil.which("mpv")
    if on_path:
        return on_path
    # Common Windows install locations (shinchiro build, mpv.net)
    candidates = [
        r"C:\Program Files\MPV Player\mpv.exe",
        r"C:\Program Files\mpv\mpv.exe",
        r"C:\Program Files (x86)\mpv\mpv.exe",
        r"C:\Program Files\mpv.net\mpv.net.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


class MusicPlayer:
    """Plays YouTube audio via yt-dlp + mpv. Cross-platform (Win + OrangePi ARM)."""

    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._mpv = _find_mpv()
        if not self._mpv:
            logging.warning("mpv no encontrado en PATH. La reproducción de música no funcionará.")
        try:
            import yt_dlp  # noqa: F401
            self._ytdlp_ok = True
        except ImportError:
            logging.warning("yt_dlp no instalado. La reproducción de música no funcionará.")
            self._ytdlp_ok = False

    def available(self) -> bool:
        return bool(self._mpv) and self._ytdlp_ok

    def _resolve_stream(self, query: str) -> tuple[str | None, str | None]:
        """Returns (audio_url, title) for the best match on YouTube."""
        import yt_dlp

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "default_search": "ytsearch1",
            "skip_download": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
            if "entries" in info:
                entries = info["entries"]
                if not entries:
                    return None, None
                info = entries[0]
            return info.get("url"), info.get("title")
        except Exception as e:
            logging.error(f"yt-dlp falló buscando '{query}': {e}")
            return None, None

    def play(self, query: str) -> str | None:
        """Plays the first YouTube result for `query`. Returns the song title or None."""
        if not self.available():
            return None

        self.stop()

        url, title = self._resolve_stream(query)
        if not url:
            return None

        logging.info(f"Reproduciendo: {title}")
        cmd = [
            self._mpv,
            "--no-video",
            "--no-terminal",
            "--really-quiet",
            "--no-input-terminal",
            url,
        ]
        try:
            with self._lock:
                self._proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )
            return title
        except Exception as e:
            logging.error(f"No se pudo lanzar mpv: {e}")
            return None

    def stop(self) -> bool:
        """Stops current playback if any. Returns True if something was stopped."""
        with self._lock:
            proc = self._proc
            self._proc = None
        if proc is None or proc.poll() is not None:
            return False
        try:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception as e:
            logging.error(f"Error parando mpv: {e}")
        return True

    def is_playing(self) -> bool:
        with self._lock:
            return self._proc is not None and self._proc.poll() is None
