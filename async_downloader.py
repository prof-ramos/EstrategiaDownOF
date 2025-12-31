"""Async download manager with progress checkpointing."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp
from colorama import Fore, Style
from tqdm import tqdm

CHUNK_SIZE = 131072  # 128KB
INDEX_FILE = "download_index.json"


class DownloadIndex:
    """Manages the download checkpoint index."""

    def __init__(self, base_dir: str):
        self.index_path = Path(base_dir) / INDEX_FILE
        self.completed: set[str] = set()
        self.load()

    def load(self) -> None:
        """Load the index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.completed = set(data.get('completed', []))
            except (json.JSONDecodeError, OSError):
                self.completed = set()

    def save(self) -> None:
        """Save the index to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump({'completed': list(self.completed)}, f, indent=2)

    def is_completed(self, file_path: str) -> bool:
        """Check if a file has been downloaded."""
        return file_path in self.completed

    def mark_completed(self, file_path: str) -> None:
        """Mark a file as completed and save index."""
        self.completed.add(file_path)
        self.save()


async def download_file_async(
    session: aiohttp.ClientSession,
    task: dict[str, str],
    index: DownloadIndex,
    semaphore: asyncio.Semaphore,
    pbar: tqdm
) -> str:
    """Download a single file asynchronously with resume support.

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

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': '*/*'
        }
        if referer:
            headers['Referer'] = referer

        # Check for partial download (resume support)
        existing_size = 0
        temp_path = path + ".part"
        if os.path.exists(temp_path):
            existing_size = os.path.getsize(temp_path)
            headers['Range'] = f'bytes={existing_size}-'

        try:
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
        except Exception as e:
            pbar.update(1)
            return f"{Fore.RED}Falha: {filename} - {e}"


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
        tqdm.write(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Todos os arquivos já foram baixados.")
        return

    tqdm.write(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Iniciando download de {len(pending)} arquivos (async)...")

    connector = aiohttp.TCPConnector(limit=max_workers, limit_per_host=max_workers)
    timeout = aiohttp.ClientTimeout(total=300)  # 5 min timeout

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        with tqdm(total=len(pending), desc="Progresso da Aula", unit="arq", colour='cyan') as pbar:
            tasks = [
                download_file_async(session, task, index, semaphore, pbar)
                for task in pending
            ]

            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                # Log any errors
                for result in results:
                    if isinstance(result, Exception):
                        tqdm.write(f"{Fore.RED}[ERRO]{Style.RESET_ALL} {result}")
            except asyncio.CancelledError:
                tqdm.write(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} Download interrompido. Progresso salvo.")
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
        tqdm.write(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} Interrompido pelo usuário. Progresso salvo.")
