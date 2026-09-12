import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget

from settings_store import OutputFormat

_INSTAGRAM_HOST = re.compile(
    r"(?:^|\.)instagram\.com$|(?:^|\.)instagr\.am$",
    re.IGNORECASE,
)


def is_instagram_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if host:
        return bool(_INSTAGRAM_HOST.search(host))
    return "instagram.com" in url.lower() or "instagr.am" in url.lower()


def resource_path(*parts: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS).joinpath(*parts)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.joinpath(*parts)


def ffmpeg_path() -> str:
    bundled = resource_path("bin", "ffmpeg.exe")
    if bundled.is_file():
        return str(bundled)
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise FileNotFoundError(
        "ffmpeg not found. Install ffmpeg or rebuild Wavish with bin/ffmpeg.exe bundled."
    )


def sanitize_filename(name: str, max_len: int = 180) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', "", name).strip().strip(".")
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        cleaned = "audio"
    return cleaned[:max_len]


def _output_title(info: dict, fallback: str) -> str:
    title = str(info.get("title") or "").strip()
    uploader = str(
        info.get("uploader") or info.get("channel") or info.get("creator") or ""
    ).strip()
    description = str(info.get("description") or "").strip()
    generic = {"", "video", "instagram video", "instagram", "instagram reel"}

    if title.lower() in generic or title.lower().startswith("video by"):
        first_line = description.splitlines()[0].strip() if description else ""
        if first_line:
            title = first_line
        elif uploader:
            title = f"{uploader} reel"

    return sanitize_filename(title or fallback)


_BROWSER_COOKIE_ORDER = ("chrome", "edge", "firefox", "brave")


def _needs_instagram_retry(exc: Exception) -> bool:
    lower = str(exc).lower()
    return any(
        token in lower
        for token in (
            "empty media",
            "login",
            "cookies",
            "rate-limit",
            "rate limit",
            "csrf",
            "restricted",
            "registered users",
            "impersonat",
        )
    )


def _friendly_error(url: str, exc: Exception) -> RuntimeError:
    text = str(exc).strip() or "Download failed."
    instagram = is_instagram_url(url) or "instagram" in text.lower()

    if instagram:
        return RuntimeError(
            "Instagram blocked this Reel.\n\n"
            "If you can watch it logged in: open Instagram in Chrome or Edge, "
            "then try Extract again. Close the browser if Wavish still cannot "
            "read cookies.\n\n"
            "Private or follower-only clips cannot be extracted."
        )
    return exc if isinstance(exc, RuntimeError) else RuntimeError(text)


def _base_ydl_opts(
    out_template: str,
    ffmpeg: str,
    on_status: Callable[[str], None] | None,
    on_progress: Callable[[float], None] | None,
) -> dict:
    return {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "ffmpeg_location": str(Path(ffmpeg).parent),
        # Any available curl_cffi target — Instagram rejects anonymous requests without this.
        "impersonate": ImpersonateTarget(),
        "progress_hooks": [
            lambda d: _progress_hook(d, on_status, on_progress),
        ],
    }


def _extract_info(url: str, ydl_opts: dict) -> dict:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    if info is None:
        raise RuntimeError("Could not read video information.")
    return info


def _progress_hook(
    data: dict,
    on_status: Callable[[str], None] | None,
    on_progress: Callable[[float], None] | None,
) -> None:
    status = data.get("status")
    if status == "downloading":
        if on_status:
            on_status("Downloading audio…")
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        downloaded = data.get("downloaded_bytes") or 0
        if on_progress and total:
            # Map download phase to 8–82%
            pct = 8 + (downloaded / total) * 74
            on_progress(pct)
        elif on_progress:
            on_progress(20)
    elif status == "finished":
        if on_progress:
            on_progress(82)
        if on_status:
            on_status("Download complete.")


def download_audio(
    url: str,
    save_dir: Path,
    output_format: OutputFormat,
    on_status: Callable[[str], None] | None = None,
    on_progress: Callable[[float], None] | None = None,
) -> Path:
    save_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = ffmpeg_path()

    def status(msg: str) -> None:
        if on_status:
            on_status(msg)

    def progress(pct: float) -> None:
        if on_progress:
            on_progress(pct)

    progress(4)
    status("Fetching source…")

    with tempfile.TemporaryDirectory(prefix="wavish-") as tmp:
        tmp_path = Path(tmp)
        out_template = str(tmp_path / "%(title)s.%(id)s.%(ext)s")

        # Instagram Reels are muxed video; bestaudio falls back to best.
        ydl_opts = _base_ydl_opts(out_template, ffmpeg, on_status, on_progress)
        info: dict | None = None

        try:
            info = _extract_info(url, ydl_opts)
        except Exception as first:
            if not (is_instagram_url(url) and _needs_instagram_retry(first)):
                raise _friendly_error(url, first) from first

            last: Exception = first
            for browser in _BROWSER_COOKIE_ORDER:
                status(f"Instagram asked for a login — trying {browser.title()} cookies…")
                retry_opts = dict(ydl_opts)
                retry_opts["cookiesfrombrowser"] = (browser,)
                try:
                    info = _extract_info(url, retry_opts)
                    break
                except Exception as exc:
                    last = exc

            if info is None:
                raise _friendly_error(url, last) from last

        downloaded = [
            path
            for path in tmp_path.iterdir()
            if path.is_file() and path.suffix.lower() not in {".json", ".part", ".ytdl"}
        ]
        if not downloaded:
            raise RuntimeError("Download failed — no audio file produced.")

        source = max(downloaded, key=lambda path: path.stat().st_size)
        title = _output_title(info, source.stem)
        ext = output_format
        destination = save_dir / f"{title}.{ext}"

        if destination.exists():
            stem = destination.stem
            suffix = destination.suffix
            n = 2
            while destination.exists():
                destination = save_dir / f"{stem} ({n}){suffix}"
                n += 1

        progress(86)
        status(f"Converting to {output_format.upper()}…")

        if output_format == "wav":
            cmd = [
                ffmpeg,
                "-y",
                "-i",
                str(source),
                "-vn",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-c:a",
                "pcm_s24le",
                str(destination),
            ]
        else:
            cmd = [
                ffmpeg,
                "-y",
                "-i",
                str(source),
                "-vn",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "320k",
                str(destination),
            ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "ffmpeg failed").strip()
            raise RuntimeError(detail[-500:])

        progress(100)
        status("Done.")
        return destination
