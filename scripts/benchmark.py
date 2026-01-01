"""Benchmark script for Estratégia Downloader performance analysis.

Measures download speed, compression efficiency, and system resource usage.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from colorama import Fore, Style, init

init(autoreset=True)


def log_header(msg: str) -> None:
    """Print section header."""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}{Style.RESET_ALL}\n")


def log_metric(name: str, value: str, unit: str = "", good: bool = True) -> None:
    """Print a metric with color coding."""
    color = Fore.GREEN if good else Fore.YELLOW
    print(f"  {color}●{Style.RESET_ALL} {name}: {Fore.WHITE}{value}{Style.RESET_ALL} {unit}")


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def format_time(seconds: float) -> str:
    """Format seconds to human-readable string."""
    if seconds < 1:
        return f"{seconds*1000:.1f} ms"
    elif seconds < 60:
        return f"{seconds:.2f} s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.1f}s"


def check_system_resources() -> dict:
    """Check current system resources."""
    if not HAS_PSUTIL:
        return {"available": False}

    return {
        "available": True,
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "memory_available": psutil.virtual_memory().available,
        "disk_free": psutil.disk_usage('/').free,
    }


def benchmark_ffmpeg() -> dict:
    """Benchmark FFmpeg compression speed."""
    log_header("FFmpeg Compression Benchmark")

    # Check if FFmpeg is available
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"{Fore.RED}  FFmpeg not found!{Style.RESET_ALL}")
            return {"available": False}
    except (subprocess.SubprocessError, FileNotFoundError):
        print(f"{Fore.RED}  FFmpeg not found!{Style.RESET_ALL}")
        return {"available": False}

    # Get FFmpeg version
    version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown"
    log_metric("FFmpeg Version", version_line)

    # Check for hardware acceleration
    hwaccel_result = subprocess.run(
        ['ffmpeg', '-hwaccels'],
        capture_output=True, text=True, timeout=10
    )
    hwaccels = [line.strip() for line in hwaccel_result.stdout.split('\n')
                if line.strip() and line.strip() != 'Hardware acceleration methods:']
    log_metric("Hardware Accelerators", ', '.join(hwaccels) if hwaccels else "None")

    # Check codec support
    codec_result = subprocess.run(
        ['ffmpeg', '-codecs'],
        capture_output=True, text=True, timeout=10
    )
    has_h265 = 'libx265' in codec_result.stdout
    has_h264 = 'libx264' in codec_result.stdout
    has_videotoolbox = 'videotoolbox' in codec_result.stdout

    log_metric("H.265 (libx265)", "Available" if has_h265 else "Not available", good=has_h265)
    log_metric("H.264 (libx264)", "Available" if has_h264 else "Not available", good=has_h264)
    log_metric("VideoToolbox (macOS HW)", "Available" if has_videotoolbox else "Not available")

    return {
        "available": True,
        "version": version_line,
        "hwaccels": hwaccels,
        "h265": has_h265,
        "h264": has_h264,
        "videotoolbox": has_videotoolbox,
    }


def benchmark_network() -> dict:
    """Benchmark network connectivity to Estratégia servers."""
    log_header("Network Benchmark")

    import urllib.request
    import ssl

    # Create unverified SSL context (same as main.py)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    test_url = "https://www.estrategiaconcursos.com.br"

    try:
        start = time.perf_counter()
        req = urllib.request.Request(
            test_url,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        )
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            response.read()
        latency = time.perf_counter() - start

        log_metric("Server Reachable", "Yes", good=True)
        log_metric("Latency", format_time(latency), good=latency < 2)

        return {"reachable": True, "latency": latency}
    except Exception as e:
        log_metric("Server Reachable", f"No ({e})", good=False)
        return {"reachable": False, "error": str(e)}


def benchmark_imports() -> dict:
    """Benchmark import times for key modules."""
    log_header("Import Performance")

    modules = [
        ('selenium', 'Browser automation'),
        ('requests', 'HTTP client'),
        ('aiohttp', 'Async HTTP'),
        ('tqdm', 'Progress bars'),
        ('colorama', 'Terminal colors'),
    ]

    results = {}
    total_time = 0

    for module_name, description in modules:
        start = time.perf_counter()
        try:
            __import__(module_name)
            elapsed = time.perf_counter() - start
            log_metric(f"{module_name}", format_time(elapsed), f"({description})", good=elapsed < 0.5)
            results[module_name] = elapsed
            total_time += elapsed
        except ImportError:
            log_metric(f"{module_name}", "Not installed", good=False)
            results[module_name] = None

    log_metric("Total import time", format_time(total_time), good=total_time < 3)
    results['total'] = total_time

    return results


def benchmark_compression_settings() -> None:
    """Show recommended compression settings based on system."""
    log_header("Recommended Compression Settings")

    resources = check_system_resources()

    if resources.get("available"):
        cpu_cores = psutil.cpu_count(logical=False)
        memory_gb = psutil.virtual_memory().total / (1024**3)

        log_metric("CPU Cores (Physical)", str(cpu_cores))
        log_metric("Total Memory", f"{memory_gb:.1f} GB")

        # Recommend workers based on CPU cores
        recommended_workers = min(cpu_cores, 4)
        log_metric("Recommended --workers", str(recommended_workers))

        # Recommend codec based on memory
        if memory_gb >= 8:
            log_metric("Recommended --codec", "h265 (better compression, needs more RAM)")
        else:
            log_metric("Recommended --codec", "h264 (faster, less RAM)")

        # Recommend quality
        disk_free_gb = resources["disk_free"] / (1024**3)
        if disk_free_gb > 100:
            log_metric("Recommended --quality", "high (plenty of disk space)")
        elif disk_free_gb > 50:
            log_metric("Recommended --quality", "balanced (moderate disk space)")
        else:
            log_metric("Recommended --quality", "small (limited disk space)")
            log_metric("Disk Free", f"{disk_free_gb:.1f} GB", good=False)
    else:
        print(f"  {Fore.YELLOW}Install psutil for detailed recommendations: pip install psutil{Style.RESET_ALL}")
        log_metric("Recommended --workers", "2 (default)")
        log_metric("Recommended --codec", "h265")
        log_metric("Recommended --quality", "balanced")


def analyze_existing_downloads() -> None:
    """Analyze existing downloaded files for compression opportunities."""
    log_header("Download Analysis")

    # Default download path
    default_path = os.path.expanduser(
        "~/Library/Mobile Documents/com~apple~CloudDocs/Estudo/Estrategia/Meus Cursos - Estratégia Concursos"
    )

    if not os.path.exists(default_path):
        print(f"  {Fore.YELLOW}Default download path not found.{Style.RESET_ALL}")
        print(f"  Path: {default_path}")
        return

    # Find video files
    total_size = 0
    video_count = 0
    compressed_count = 0
    compressed_size = 0
    uncompressed_size = 0

    for video in Path(default_path).rglob('*.mp4'):
        size = video.stat().st_size
        total_size += size
        video_count += 1

        if '_compressed' in video.stem:
            compressed_count += 1
            compressed_size += size
        else:
            uncompressed_size += size

    if video_count == 0:
        print(f"  {Fore.YELLOW}No video files found.{Style.RESET_ALL}")
        return

    log_metric("Total Videos", str(video_count))
    log_metric("Total Size", format_bytes(total_size))
    log_metric("Already Compressed", f"{compressed_count} ({format_bytes(compressed_size)})")
    log_metric("Uncompressed", f"{video_count - compressed_count} ({format_bytes(uncompressed_size)})")

    if uncompressed_size > 0:
        # Estimate potential savings (assume 40% reduction with H.265)
        estimated_savings = uncompressed_size * 0.4
        log_metric("Estimated Savings", format_bytes(int(estimated_savings)), "(with H.265 CRF 23)")
        print(f"\n  {Fore.CYAN}Run: ./compress.sh{Style.RESET_ALL} to compress uncompressed videos")


def main() -> int:
    """Main benchmark function."""
    parser = argparse.ArgumentParser(
        description="Benchmark Estratégia Downloader performance"
    )
    parser.add_argument('--analyze', action='store_true',
                        help="Analyze existing downloads for compression opportunities")
    parser.add_argument('--full', action='store_true',
                        help="Run all benchmarks (default)")
    args = parser.parse_args()

    print(f"""
{Fore.CYAN}╭─────────────────────────────────────────────────────╮
│     Estratégia Downloader - Performance Benchmark   │
╰─────────────────────────────────────────────────────╯{Style.RESET_ALL}
""")

    # System resources
    log_header("System Resources")
    resources = check_system_resources()
    if resources.get("available"):
        log_metric("CPU Usage", f"{resources['cpu_percent']}%", good=resources['cpu_percent'] < 80)
        log_metric("Memory Usage", f"{resources['memory_percent']}%", good=resources['memory_percent'] < 80)
        log_metric("Memory Available", format_bytes(resources['memory_available']))
        log_metric("Disk Free", format_bytes(resources['disk_free']), good=resources['disk_free'] > 10*1024**3)
    else:
        print(f"  {Fore.YELLOW}Install psutil for system metrics: pip install psutil{Style.RESET_ALL}")

    # Import performance
    benchmark_imports()

    # FFmpeg
    benchmark_ffmpeg()

    # Network
    benchmark_network()

    # Recommendations
    benchmark_compression_settings()

    # Analyze existing downloads
    if args.analyze:
        analyze_existing_downloads()

    print(f"\n{Fore.GREEN}✓ Benchmark complete!{Style.RESET_ALL}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
