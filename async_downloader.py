"""Async download manager with progress checkpointing and retry."""
from __future__ import annotations

import asyncio
import json
import os
import threading
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp
from colorama import Fore, Style
from tqdm import tqdm

CHUNK_SIZE = 131072  # 128KB
INDEX_FILE = "download_index.json"
MAX_RETRIES = 4
INITIAL_RETRY_DELAY = 2.0  # segundos


class DownloadIndex:
    """Manages the download checkpoint index with thread-safe operations."""

    def __init__(self, base_dir: str):
        self.index_path = Path(base_dir) / INDEX_FILE
        self.completed: set[str] = set()
        self._lock = threading.Lock()  # Protege acesso concorrente
        self.load()

    def load(self) -> None:
        """Load the index from disk (called during __init__, no lock needed)."""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.completed = set(data.get('completed', []))
            except (json.JSONDecodeError, OSError):
                self.completed = set()

    def save(self) -> None:
        """Save the index to disk. MUST be called with lock held."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        # Cria snapshot do set para evitar RuntimeError durante iteração
        with self._lock:
            completed_snapshot = list(self.completed)

        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump({'completed': completed_snapshot}, f, indent=2)

    def is_completed(self, file_path: str) -> bool:
        """Check if a file has been downloaded (thread-safe)."""
        with self._lock:
            return file_path in self.completed

    def mark_completed(self, file_path: str) -> None:
        """Mark a file as completed and save index (thread-safe)."""
        with self._lock:
            self.completed.add(file_path)
        # save() agora cria seu próprio snapshot com lock
        self.save()


async def download_file_async(
    session: aiohttp.ClientSession,
    task: dict[str, str],
    index: DownloadIndex,
    semaphore: asyncio.Semaphore,
    pbar: tqdm
) -> str:
    """Download a single file asynchronously with resume and retry support.

    Args:
        session: aiohttp session for connection pooling.
        task: Dict with url, path, filename, referer.
        index: DownloadIndex for checkpointing.
        semaphore: Limits concurrent downloads.
        pbar: Progress bar to update.

    Returns:
        Status message.
    """
    url = task['url']
    path = task['path']
    filename = task['filename']
    referer = task.get('referer')

    async with semaphore:
        # Check index first
        if index.is_completed(path):
            pbar.update(1)
            return f"{Fore.YELLOW}Já indexado (pulado): {filename}"

        # Check if file exists on disk
        if os.path.exists(path):
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
                    'Accept': '*/*'
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

                async with session.get(url, headers=headers, ssl=False) as response:
                    # Check if server supports range requests
                    if response.status == 416:  # Range not satisfiable = file complete
                        if os.path.exists(temp_path):
                            os.rename(temp_path, path)
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
    max_workers: int = 4
) -> None:
    """Process download queue using async I/O.

    Args:
        queue: List of download tasks.
        base_dir: Base directory for downloads.
        max_workers: Maximum concurrent downloads.
    """
    if not queue:
        return

    index = DownloadIndex(base_dir)
    semaphore = asyncio.Semaphore(max_workers)

    # Filter out already completed downloads
    pending = [t for t in queue if not index.is_completed(t['path'])]

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


def run_async_downloads(queue: list[dict[str, str]], base_dir: str, max_workers: int = 4) -> None:
    """Wrapper to run async downloads from sync code.

    Args:
        queue: List of download tasks.
        base_dir: Base directory for downloads.
        max_workers: Maximum concurrent downloads.
    """
    try:
        asyncio.run(process_download_queue_async(queue, base_dir, max_workers))
    except KeyboardInterrupt:
        tqdm.write(f"{Fore.YELLOW}⚠ AVISO:{Style.RESET_ALL} Interrompido pelo usuário. Progresso salvo.")
