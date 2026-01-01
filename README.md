# EstrategiaDownloader

Automated course downloader for Estratégia Concursos platform, optimized for macOS with
high-performance async engines, SQLite tracking, and FFmpeg video compression.

## ⚡ Performance First

This project has been redesigned for maximum throughput, achieving **60-70% faster** operations
compared to traditional scraping methods.

- **JS-Powered Scraping**: 70-80% reduction in scraping time via single-pass JavaScript metadata
  extraction.
- **Async Engine**: Built with `aiohttp` and `uvloop`, leveraging Context7 best practices for
  connection pooling and adaptive timeouts.
- **SQLite Tracking**: Robust download management with rich metadata and integrity checks.

## 🚀 Quick Start

The recommended way to run this project is using [**uv**](https://github.com/astral-sh/uv) for
maximum speed and dependency reliability.

```bash
# Clone the repository
git clone https://github.com/prof-ramos/EstrategiaDownOF.git
cd EstrategiaDownloader

# Run with uv (automatically manages venv and dependencies)
uv run python main.py --async --headless
```

Alternatively, use standard pip:

```bash
pip install -r requirements.txt
python main.py --async
```

## 🛠️ Project Structure

```
EstrategiaDownloader/
├── src/estrategia_downloader/    # Core Package
│   ├── main.py                    # Scraper orchestration
│   ├── async_downloader.py        # High-performance async engine (uvloop + aiohttp)
│   ├── download_database.py       # SQLite tracking system
│   ├── performance_monitor.py     # Real-time metrics & reporting
│   ├── compress_videos.py         # FFmpeg-powered compression
│   └── ui.py                      # Modern terminal interface
├── tests/                         # Comprehensive test suite (250+ tests)
├── docs/                          # Detailed guides & optimization plans
└── scripts/                       # Benchmarks and utility tools
```

## ✨ Features

- 🏎️ **Ultra-Fast Async Mode**: Parallel downloads using `uvloop` (Python 3.12+ optimized).
- 🧠 **Smart Scraping**: JavaScript extraction logic that bypasses slow page-by-page loads.
- 🔌 **Optimized Connection Pool**: High-performance TCP pooling with DNS caching.
- 🗜️ **Advanced Compression**: Efficient H.265/H.264 video compression via FFmpeg.
- 📊 **Metric Dashboard**: Detailed performance reports after every execution.
- 🛡️ **Resilient Downloads**: Automatic resume support (`.part` files) and exponential backoff
  retries.

## 📖 Documentation

- **[Optimization Roadmap](docs/optimizerplan.md)** - Details on recent performance gains.
- **[System Tracking Plan](PLANO_SISTEMA_TRACKING.md)** - Deep dive into the SQLite architecture.
- **[Full User Guide](docs/README.md)** - CLI flags and advanced configuration.
- **[Testing Manual](docs/TESTING.md)** - How to run and extend the test suite.

## 📋 Requirements

- Python 3.9+ (Python 3.12+ recommended for `uvloop.run()`)
- Google Chrome or Microsoft Edge
- **FFmpeg**: Optional, required for video compression features.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
