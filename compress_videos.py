"""FFmpeg video compression script for Estratégia Downloader.

Compresses downloaded videos using H.265/H.264 with minimal quality loss.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from colorama import Fore, Style, init
from tqdm import tqdm

# Initialize colorama
init(autoreset=True)

# Quality presets (CRF values)
QUALITY_PRESETS = {
    'high': 18,      # Visually lossless, larger files
    'balanced': 23,  # Good balance (default)
    'small': 28,     # Smaller files, some quality loss
}

# Compressed file suffix
COMPRESSED_SUFFIX = "_compressed"


def log_info(msg: str) -> None:
    """Log informational message."""
    tqdm.write(f"{Fore.CYAN}● INFO:{Style.RESET_ALL} {msg}")


def log_success(msg: str) -> None:
    """Log success message."""
    tqdm.write(f"{Fore.GREEN}✓ OK:{Style.RESET_ALL} {msg}")


def log_warn(msg: str) -> None:
    """Log warning message."""
    tqdm.write(f"{Fore.YELLOW}⚠ AVISO:{Style.RESET_ALL} {msg}")


def log_error(msg: str) -> None:
    """Log error message."""
    tqdm.write(f"{Fore.RED}✗ ERRO:{Style.RESET_ALL} {msg}")


def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed and available."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_video_info(file_path: Path) -> dict | None:
    """Get video file information using ffprobe."""
    try:
        result = subprocess.run(
            [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(file_path)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def find_videos(directory: Path, include_compressed: bool = False) -> list[Path]:
    """Find all .mp4 files in the directory recursively."""
    videos = []
    for video in directory.rglob('*.mp4'):
        # Skip already compressed files unless explicitly requested
        if not include_compressed and COMPRESSED_SUFFIX in video.stem:
            continue
        # Skip .part files (incomplete downloads)
        if video.suffix == '.part':
            continue
        videos.append(video)
    return sorted(videos)


def get_output_path(input_path: Path, delete_original: bool) -> Path:
    """Generate output path for compressed video."""
    if delete_original:
        # Use temp name, will replace original later
        return input_path.with_suffix('.mp4.temp')
    else:
        # Add compressed suffix
        stem = input_path.stem
        return input_path.with_name(f"{stem}{COMPRESSED_SUFFIX}.mp4")


def compress_video(
    input_path: Path,
    output_path: Path,
    codec: str = 'h265',
    quality: str = 'balanced',
    dry_run: bool = False
) -> tuple[bool, str, int, int]:
    """Compress a single video file.

    Returns:
        Tuple of (success, message, original_size, compressed_size)
    """
    crf = QUALITY_PRESETS.get(quality, 23)
    original_size = input_path.stat().st_size

    if dry_run:
        return (True, f"[DRY-RUN] Would compress: {input_path.name}", original_size, 0)

    # Build FFmpeg command
    if codec == 'h265':
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-c:v', 'libx265',
            '-x265-params', f'crf={crf}',
            '-preset', 'medium',
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-y',  # Overwrite output
            str(output_path)
        ]
    else:  # h264
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-c:v', 'libx264',
            '-crf', str(crf),
            '-preset', 'slow',
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-y',  # Overwrite output
            str(output_path)
        ]

    try:
        # Run FFmpeg with suppressed output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per video
        )

        if result.returncode != 0:
            # Clean up partial output
            if output_path.exists():
                output_path.unlink()
            return (False, f"FFmpeg error: {result.stderr[:200]}", original_size, 0)

        compressed_size = output_path.stat().st_size
        reduction = ((original_size - compressed_size) / original_size) * 100

        return (
            True,
            f"Compressed: {input_path.name} ({reduction:.1f}% reduction)",
            original_size,
            compressed_size
        )

    except subprocess.TimeoutExpired:
        if output_path.exists():
            output_path.unlink()
        return (False, f"Timeout compressing: {input_path.name}", original_size, 0)
    except Exception as e:
        if output_path.exists():
            output_path.unlink()
        return (False, f"Error: {e}", original_size, 0)


def compress_video_task(
    input_path: Path,
    codec: str,
    quality: str,
    delete_original: bool,
    dry_run: bool
) -> tuple[bool, str, int, int]:
    """Task wrapper for parallel compression."""
    output_path = get_output_path(input_path, delete_original)

    success, message, orig_size, comp_size = compress_video(
        input_path, output_path, codec, quality, dry_run
    )

    # If successful and delete_original is True, replace original atomically
    if success and delete_original and not dry_run:
        try:
            # Use atomic replace: move temp file over original in one operation
            os.replace(output_path, input_path)
            message = message.replace(COMPRESSED_SUFFIX, '')
        except OSError as e:
            return (False, f"Error replacing original: {e}", orig_size, comp_size)

    return (success, message, orig_size, comp_size)


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main() -> int:
    """Main function."""
    # Default path from environment variable or fallback
    default_path = os.environ.get(
        'ESTRATEGIA_DOWNLOAD_DIR',
        os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/Estudo/Estrategia/Meus Cursos - Estratégia Concursos')
    )

    parser = argparse.ArgumentParser(
        description="Compress downloaded videos using FFmpeg (H.265/H.264)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quality Presets:
  high      CRF 18 - Visually lossless, larger files
  balanced  CRF 23 - Good balance (default)
  small     CRF 28 - Smaller files, some quality loss

Codec Options:
  h265  H.265/HEVC - ~50% smaller, modern devices (default)
  h264  H.264/AVC  - Compatible with all devices
        """
    )
    parser.add_argument('-d', '--dir', type=str, default=default_path,
                        help="Directory to scan for videos")
    parser.add_argument('--quality', choices=['high', 'balanced', 'small'],
                        default='balanced', help="Quality preset (default: balanced)")
    parser.add_argument('--codec', choices=['h265', 'h264'], default='h265',
                        help="Video codec (default: h265)")
    parser.add_argument('--delete', action='store_true',
                        help="Delete originals after successful compression")
    parser.add_argument('--workers', type=int, default=2,
                        help="Number of parallel compressions (default: 2)")
    parser.add_argument('--dry-run', action='store_true',
                        help="Show what would be compressed without doing it")

    args = parser.parse_args()

    # Validate workers
    if args.workers < 1:
        log_error("Workers must be at least 1")
        return 1

    # Banner
    print(f"""
{Fore.CYAN}╭─────────────────────────────────────────────────────╮
│         FFmpeg Video Compressor v1.0                │
│         Estratégia Downloader                       │
╰─────────────────────────────────────────────────────╯{Style.RESET_ALL}
""")

    # Check FFmpeg
    if not check_ffmpeg():
        log_error("FFmpeg não encontrado! Instale com: brew install ffmpeg")
        return 1

    log_success("FFmpeg encontrado")

    # Expand path
    scan_dir = Path(os.path.expanduser(args.dir))
    if not scan_dir.exists():
        log_error(f"Diretório não existe: {scan_dir}")
        return 1

    # Configuration panel
    print(f"""
{Fore.CYAN}┌─ Configuração ─────────────────────────────────────┐
│  Diretório: {str(scan_dir)[:40]}...
│  Qualidade: {args.quality} (CRF {QUALITY_PRESETS[args.quality]})
│  Codec:     {args.codec.upper()}
│  Workers:   {args.workers}
│  Deletar:   {'Sim' if args.delete else 'Não'}
│  Dry-run:   {'Sim' if args.dry_run else 'Não'}
└─────────────────────────────────────────────────────┘{Style.RESET_ALL}
""")

    # Find videos
    log_info(f"Escaneando diretório...")
    videos = find_videos(scan_dir)

    if not videos:
        log_warn("Nenhum vídeo .mp4 encontrado para comprimir.")
        return 0

    log_info(f"Encontrados {len(videos)} vídeos para comprimir")

    if args.dry_run:
        print(f"\n{Fore.YELLOW}[DRY-RUN MODE]{Style.RESET_ALL}\n")
        for video in videos:
            size = format_size(video.stat().st_size)
            print(f"  • {video.name} ({size})")
        print()
        return 0

    # Compress videos in parallel
    total_original = 0
    total_compressed = 0
    success_count = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                compress_video_task,
                video, args.codec, args.quality, args.delete, args.dry_run
            ): video for video in videos
        }

        pbar_config = {
            "desc": "  🎬 Comprimindo",
            "unit": " vídeo",
            "colour": "green",
            "bar_format": "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        }

        for future in tqdm(as_completed(futures), total=len(videos), **pbar_config):
            success, message, orig_size, comp_size = future.result()
            total_original += orig_size
            total_compressed += comp_size

            if success:
                success_count += 1
                tqdm.write(f"{Fore.GREEN}  ✓ {message}{Style.RESET_ALL}")
            else:
                tqdm.write(f"{Fore.RED}  ✗ {message}{Style.RESET_ALL}")

    # Summary
    print(f"""
{Fore.CYAN}╭─ Resumo ────────────────────────────────────────────╮
│  Vídeos processados: {success_count}/{len(videos)}
│  Tamanho original:   {format_size(total_original)}
│  Tamanho comprimido: {format_size(total_compressed)}
│  Economia total:     {format_size(total_original - total_compressed)}
╰─────────────────────────────────────────────────────╯{Style.RESET_ALL}
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
