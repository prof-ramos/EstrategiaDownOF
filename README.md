# EstrategiaDownloader

Automated course downloader for Estratégia Concursos platform, optimized for macOS with async downloads, SQLite tracking, and FFmpeg video compression.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the downloader
python main.py
```

## Project Structure

```
EstrategiaDownloader/
├── src/estrategia_downloader/    # Main package
│   ├── __init__.py
│   ├── main.py                    # Entry point
│   ├── async_downloader.py        # Async download engine
│   ├── download_database.py       # SQLite tracking system
│   ├── compress_videos.py         # FFmpeg compression
│   ├── ui.py                      # Terminal UI components
│   └── performance_monitor.py     # Performance metrics
├── tests/                         # Test suite (250+ tests)
├── scripts/                       # Utility scripts
│   ├── benchmark.py               # Performance benchmarks
│   ├── demo_ui.py                 # UI component demos
│   └── compress.sh                # Video compression wrapper
├── docs/                          # Documentation
│   ├── README.md                  # Detailed documentation
│   ├── CLAUDE.md                  # Claude Code instructions
│   ├── TESTING.md                 # Testing guide
│   ├── CHANGELOG.md               # Version history
│   ├── AGENTS.md                  # Agent workflows
│   └── optimizerplan.md           # Performance optimization plan
├── .archive/                      # Archived documents
├── main.py -> src/.../main.py     # Compatibility symlink
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
└── pytest.ini                     # Pytest configuration
```

## Documentation

- **[Full Documentation](docs/README.md)** - Complete usage guide
- **[Testing Guide](docs/TESTING.md)** - How to run tests
- **[Optimization Plan](docs/optimizerplan.md)** - Performance improvements
- **[Changelog](docs/CHANGELOG.md)** - Version history

## Features

- ⚡ **Async Downloads** - High-performance parallel downloads with uvloop
- 💾 **SQLite Tracking** - Rich metadata and integrity verification
- 🗜️ **Video Compression** - Automatic H.265/H.264 compression with FFmpeg
- 🔄 **Resume Support** - Automatic retry with exponential backoff
- 📊 **Performance Monitoring** - Comprehensive metrics and reporting
- 🎯 **Adaptive Timeouts** - File-type-specific timeout handling

## Requirements

- Python 3.9+
- Chrome or Edge browser
- FFmpeg (optional, for video compression)

## License

MIT License - see [LICENSE](LICENSE) for details.
