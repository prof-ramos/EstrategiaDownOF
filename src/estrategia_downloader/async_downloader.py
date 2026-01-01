"""Async download manager with progress checkpointing and retry."""
from __future__ import annotations

import asyncio
import os
import sys
import threading
from pathlib import Path
from typing import Any, Union

import aiofiles
import aiohttp
from colorama import Fore, Style
from tqdm import tqdm

# Import new DownloadDatabase
from .download_database import DownloadDatabase

# Use uvloop on macOS/Linux for 30-40% faster async (fallback on Windows/if not installed)
if sys.platform != 'win32':
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass

# Use orjson for 10x faster JSON if available, fallback to stdlib
try:
    import orjson
    def json_loads(data: str | bytes) -> dict:
        return orjson.loads(data)
    def json_dumps(obj: dict) -> bytes:
        return orjson.dumps(obj, option=orjson.OPT_INDENT_2)
    JSON_WRITE_MODE = 'wb'
except ImportError:
    import json
    def json_loads(data: str | bytes) -> dict:
        return json.loads(data)
    def json_dumps(obj: dict) -> str:
        return json.dumps(obj, indent=2)
    JSON_WRITE_MODE = 'w'

CHUNK_SIZE = 131072  # 128KB
INDEX_FILE = "download_index.json"
MAX_RETRIES = 4
INITIAL_RETRY_DELAY = 2.0  # segundos

# Adaptive timeout settings (seconds)
TIMEOUT_VIDEO = 600      # 10 minutes for videos (large files)
TIMEOUT_PDF = 120        # 2 minutes for PDFs
TIMEOUT_DEFAULT = 60     # 1 minute for other files


def get_adaptive_timeout(filename: str) -> int:
    """Calculate adaptive timeout based on file type.

    Args:
        filename: Name of the file to download.

    Returns:
        Timeout in seconds.
    """
    filename_lower = filename.lower()
    if filename_lower.endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm')):
        return TIMEOUT_VIDEO
    elif filename_lower.endswith('.pdf'):
        return TIMEOUT_PDF
    else:
        return TIMEOUT_DEFAULT


class DownloadIndex:
    """Legacy download index - mantido para compatibilidade reversa.

    DEPRECATED: Use DownloadDatabase em vez disso.
    """

    def __init__(self, base_dir: str):
        self.index_path = Path(base_dir) / INDEX_FILE
        self.completed: set[str] = set()
        self._lock = threading.Lock()  # Protege acesso concorrente
        self.load()

    def load(self) -> None:
        """Load the index from disk (orjson optimized, called during __init__)."""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'rb') as f:
                    data = json_loads(f.read())
                    self.completed = set(data.get('completed', []))
            except (ValueError, OSError):
                self.completed = set()

    def save(self) -> None:
        """Save the index to disk (orjson optimized + thread-safe)."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        # Cria snapshot do set para evitar RuntimeError durante iteração
        with self._lock:
            completed_snapshot = list(self.completed)

        with open(self.index_path, JSON_WRITE_MODE) as f:
            f.write(json_dumps({'completed': completed_snapshot}))

    def is_completed(self, file_path: str) -> bool:
        """Check if a file has been downloaded (thread-safe)."""
        with self._lock:
            return file_path in self.completed

    def is_downloaded(self, file_path: str) -> bool:
        """Alias for is_completed() for compatibility with DownloadDatabase API."""
        return self.is_completed(file_path)

    def mark_completed(self, file_path: str) -> None:
        """Mark a file as completed and save index (thread-safe)."""
        with self._lock:
            self.completed.add(file_path)
        # save() agora cria seu próprio snapshot com lock
        self.save()

    def mark_completed_batch(self, file_paths: list[str]) -> None:
        """Mark multiple files as completed and save index once (reduces I/O)."""
        self.completed.update(file_paths)
        self.save()


async def download_file_async(
    session: aiohttp.ClientSession,
    task: dict[str, str],
    index: Union[DownloadIndex, DownloadDatabase],
    semaphore: asyncio.Semaphore,
    pbar: tqdm
) -> str:
    """Download a single file asynchronously with resume and retry support.

    Args:
        session: aiohttp session for connection pooling.
        task: Dict with url, path, filename, referer, course_name, lesson_name, file_type.
        index: DownloadIndex or DownloadDatabase for checkpointing.
        semaphore: Limits concurrent downloads.
        pbar: Progress bar to update.

    Returns:
        Status message.
    """
    url = task['url']
    path = task['path']
    filename = task['filename']
    referer = task.get('referer')

    # Extract metadata for DownloadDatabase
    course_name = task.get('course_name', 'Unknown')
    lesson_name = task.get('lesson_name', 'Unknown')
    file_type = task.get('file_type', 'unknown')

    async with semaphore:
        # Check index first
        if index.is_downloaded(path):
            pbar.update(1)
            return f"{Fore.YELLOW}Já indexado (pulado): {filename}"

        # Check if file exists on disk
        if os.path.exists(path):
            # Mark as completed with metadata if using DownloadDatabase
            if isinstance(index, DownloadDatabase):
                index.mark_downloaded(
                    file_path=path,
                    url=url,
                    course_name=course_name,
                    lesson_name=lesson_name,
                    file_type=file_type
                )
            else:
                index.mark_completed(path)
            pbar.update(1)
            return f"{Fore.YELLOW}Já existe (pulado): {filename}"

        temp_path = path + ".part"

        # Retry loop com backoff exponencial
        delay = INITIAL_RETRY_DELAY
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',  # Compression for 60-80% bandwidth savings
                    'Connection': 'keep-alive'  # Reuse connections
                }
                if referer:
                    headers['Referer'] = referer

                # Check for partial download (resume support)
                existing_size = 0
                if os.path.exists(temp_path):
                    existing_size = os.path.getsize(temp_path)
                    headers['Range'] = f'bytes={existing_size}-'

                # Create parent directory
                os.makedirs(os.path.dirname(path), exist_ok=True)

                # Use adaptive timeout based on file type
                file_timeout = get_adaptive_timeout(filename)
                timeout = aiohttp.ClientTimeout(total=file_timeout)

                async with session.get(url, headers=headers, ssl=False, timeout=timeout) as response:
                    # Check if server supports range requests
                    if response.status == 416:  # Range not satisfiable = file complete
                        if os.path.exists(temp_path):
                            os.rename(temp_path, path)

                        # Mark with metadata if using DownloadDatabase
                        if isinstance(index, DownloadDatabase):
                            index.mark_downloaded(
                                file_path=path,
                                url=url,
                                course_name=course_name,
                                lesson_name=lesson_name,
                                file_type=file_type
                            )
                        else:
                            index.mark_completed(path)

                        pbar.update(1)
                        return f"{Fore.GREEN}Resumido (completo): {filename}"

                    response.raise_for_status()

                    # Get total size
                    content_length = response.headers.get('content-length')
                    total_size = int(content_length) if content_length else 0

                    # If resuming and server returned 206 Partial Content
                    mode = 'ab' if response.status == 206 else 'wb'

                    async with aiofiles.open(temp_path, mode) as f:
                        async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                            await f.write(chunk)

                    # Rename temp file to final
                    os.rename(temp_path, path)

                    # Mark with metadata if using DownloadDatabase
                    if isinstance(index, DownloadDatabase):
                        index.mark_downloaded(
                            file_path=path,
                            url=url,
                            course_name=course_name,
                            lesson_name=lesson_name,
                            file_type=file_type
                        )
                    else:
                        index.mark_completed(path)

                    pbar.update(1)
                    return f"{Fore.GREEN}Baixado: {filename}"

            except asyncio.CancelledError:
                # Don't delete partial file on cancellation (for resume)
                raise

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Erros de rede são recuperáveis
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    delay *= 2  # Backoff exponencial
                continue

            except Exception as e:
                # Outros erros, não tenta novamente
                pbar.update(1)
                # Remove arquivo parcial em caso de erro fatal
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                return f"{Fore.RED}Falha: {filename} - {e}"

        # Se chegou aqui, todas as tentativas falharam
        pbar.update(1)
        return f"{Fore.RED}Falha após {MAX_RETRIES} tentativas: {filename} - {last_error}"


async def process_download_queue_async(
    queue: list[dict[str, str]],
    base_dir: str,
    max_workers: int = 4,
    use_sqlite: bool = True
) -> None:
    """Process download queue using async I/O.

    Args:
        queue: List of download tasks.
        base_dir: Base directory for downloads.
        max_workers: Maximum concurrent downloads.
        use_sqlite: If True uses SQLite (default), if False uses JSON fallback.
    """
    if not queue:
        return

    # Use new DownloadDatabase by default
    if use_sqlite:
        index = DownloadDatabase(base_dir, use_sqlite=True)
        tqdm.write(f"{Fore.CYAN}● INFO:{Style.RESET_ALL} Usando sistema de tracking SQLite (com metadados)")
    else:
        index = DownloadIndex(base_dir)
        tqdm.write(f"{Fore.YELLOW}● INFO:{Style.RESET_ALL} Usando sistema de tracking JSON (legado)")

    semaphore = asyncio.Semaphore(max_workers)

    # Filter out already completed downloads
    pending = [t for t in queue if not index.is_downloaded(t['path'])]

    if not pending:
        tqdm.write(f"{Fore.GREEN}✓{Style.RESET_ALL} Todos os arquivos já foram baixados.")
        return

    tqdm.write(f"{Fore.CYAN}● INFO:{Style.RESET_ALL} Iniciando download de {len(pending)} arquivos (async)...")

    connector = aiohttp.TCPConnector(limit=max_workers, limit_per_host=max_workers)
    timeout = aiohttp.ClientTimeout(total=300)  # 5 min timeout

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        pbar_config = {
            "desc": "  ⚡ Baixando (async)",
            "unit": " arq",
            "colour": "magenta",
            "bar_format": "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        }
        with tqdm(total=len(pending), **pbar_config) as pbar:
            tasks = [
                download_file_async(session, task, index, semaphore, pbar)
                for task in pending
            ]

            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                # Log any errors
                for result in results:
                    if isinstance(result, Exception):
                        tqdm.write(f"{Fore.RED}✗ ERRO:{Style.RESET_ALL} {result}")
            except asyncio.CancelledError:
                tqdm.write(f"{Fore.YELLOW}⚠ AVISO:{Style.RESET_ALL} Download interrompido. Progresso salvo.")
                raise


def run_async_downloads(
    queue: list[dict[str, str]],
    base_dir: str,
    max_workers: int = 4,
    use_sqlite: bool = True
) -> None:
    """Wrapper to run async downloads from sync code.

    Args:
        queue: List of download tasks.
        base_dir: Base directory for downloads.
        max_workers: Maximum concurrent downloads.
        use_sqlite: If True uses SQLite (default), if False uses JSON fallback.
    """
    try:
        asyncio.run(process_download_queue_async(queue, base_dir, max_workers, use_sqlite))
    except KeyboardInterrupt:
        tqdm.write(f"{Fore.YELLOW}⚠ AVISO:{Style.RESET_ALL} Interrompido pelo usuário. Progresso salvo.")
