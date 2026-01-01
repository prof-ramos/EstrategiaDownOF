"""Performance monitoring and metrics collection."""
from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar
from dataclasses import dataclass, field
from collections import defaultdict

F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class PerformanceMetrics:
    """Stores performance metrics for the session."""
    scraping_time: float = 0.0
    download_time: float = 0.0
    compression_time: float = 0.0
    total_time: float = 0.0

    files_skipped: int = 0
    files_downloaded: int = 0
    files_failed: int = 0
    files_compressed: int = 0

    total_bytes: int = 0
    bytes_saved_compression: int = 0
    courses_processed: int = 0
    lessons_processed: int = 0

    function_timings: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def add_timing(self, func_name: str, duration: float) -> None:
        """Record a function timing."""
        self.function_timings[func_name].append(duration)

    def get_avg_timing(self, func_name: str) -> float:
        """Get average timing for a function."""
        timings = self.function_timings.get(func_name, [])
        return sum(timings) / len(timings) if timings else 0.0

    def get_total_timing(self, func_name: str) -> float:
        """Get total timing for a function."""
        timings = self.function_timings.get(func_name, [])
        return sum(timings)

    def print_report(self) -> None:
        """Print performance report."""
        print("\n" + "=" * 70)
        print("📊 PERFORMANCE REPORT")
        print("=" * 70)

        # Time breakdown
        print(f"⏱️  Total Time: {self.total_time:.2f}s")
        if self.total_time > 0:
            print(f"   ├─ Scraping: {self.scraping_time:.2f}s ({self.scraping_time/self.total_time*100:.1f}%)")
            print(f"   ├─ Downloads: {self.download_time:.2f}s ({self.download_time/self.total_time*100:.1f}%)")
            if self.compression_time > 0:
                print(f"   └─ Compression: {self.compression_time:.2f}s ({self.compression_time/self.total_time*100:.1f}%)")

        # File statistics
        print(f"\n📁 Files:")
        print(f"   ├─ Downloaded: {self.files_downloaded}")
        print(f"   ├─ Skipped: {self.files_skipped}")
        if self.files_compressed > 0:
            print(f"   ├─ Compressed: {self.files_compressed}")
        print(f"   └─ Failed: {self.files_failed}")

        # Data statistics
        total_mb = self.total_bytes / (1024**2)
        print(f"\n💾 Data: {total_mb:.2f} MB downloaded")
        if self.bytes_saved_compression > 0:
            saved_mb = self.bytes_saved_compression / (1024**2)
            compression_ratio = (self.bytes_saved_compression / self.total_bytes * 100) if self.total_bytes > 0 else 0
            print(f"   └─ Saved by compression: {saved_mb:.2f} MB ({compression_ratio:.1f}%)")

        # Course/Lesson statistics
        print(f"\n📚 Courses: {self.courses_processed} | Lessons: {self.lessons_processed}")

        # Throughput metrics
        if self.total_time > 0:
            print(f"\n⚡ Throughput:")
            if self.files_downloaded > 0:
                print(f"   ├─ Files/sec: {self.files_downloaded/self.total_time:.2f}")
                print(f"   ├─ MB/sec: {total_mb/self.total_time:.2f}")
            if self.lessons_processed > 0:
                print(f"   └─ Avg time/lesson: {self.total_time/self.lessons_processed:.2f}s")

        # Top function timings
        if self.function_timings:
            print(f"\n⚙️  Top Function Timings:")
            sorted_funcs = sorted(
                self.function_timings.items(),
                key=lambda x: sum(x[1]),
                reverse=True
            )[:5]
            for func_name, timings in sorted_funcs:
                total = sum(timings)
                avg = total / len(timings)
                count = len(timings)
                print(f"   • {func_name}: {total:.2f}s total, {avg:.2f}s avg ({count} calls)")

        print("=" * 70 + "\n")


# Global metrics instance
metrics = PerformanceMetrics()


def timed(func: F) -> F:
    """Decorator to time function execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        metrics.add_timing(func.__name__, duration)
        return result
    return wrapper  # type: ignore


def timed_async(func: F) -> F:
    """Decorator to time async function execution."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        duration = time.perf_counter() - start
        metrics.add_timing(func.__name__, duration)
        return result
    return wrapper  # type: ignore


class TimerContext:
    """Context manager for timing code blocks."""

    def __init__(self, name: str):
        self.name = name
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        metrics.add_timing(self.name, duration)
        return False


def timer(name: str) -> TimerContext:
    """Create a timer context manager for measuring code blocks.

    Usage:
        with timer("my_operation"):
            # code to measure
            pass
    """
    return TimerContext(name)
