"""EstrategiaDownloader - Automated course downloader for Estratégia Concursos."""

__version__ = "2.1.0"
__author__ = "Gabriel Ramos"

from .main import main
from .async_downloader import run_async_downloads, DownloadIndex
from .download_database import DownloadDatabase
from .compress_videos import compress_video_task, find_videos, check_ffmpeg
from .performance_monitor import metrics, timed, timed_async, timer

__all__ = [
    "main",
    "run_async_downloads",
    "DownloadIndex",
    "DownloadDatabase",
    "compress_video_task",
    "find_videos",
    "check_ffmpeg",
    "metrics",
    "timed",
    "timed_async",
    "timer",
]
