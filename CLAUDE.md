# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutoDownload Estratégia Concursos is a Python-based downloader optimized for macOS that automatically downloads courses from Estratégia Concursos platform. The project emphasizes performance, resilience, and user experience with async downloads, SQLite-based tracking, automatic retry mechanisms, and optional FFmpeg video compression.

## Core Architecture

### Entry Point & Flow
- **main.py** (962 lines): Main orchestrator that handles authentication, course/lesson scraping, and download coordination
  - Uses Selenium for browser automation and cookie persistence
  - Delegates actual downloads to async_downloader.py
  - Supports both async (default, fast) and sync (fallback) download modes
  - After downloading a course, optionally compresses videos via compress_videos.py

### Download System (Dual-Mode)
The system supports two download modes:

1. **Async Mode (Default)**: async_downloader.py (340 lines)
   - Uses aiohttp + aiofiles for high-performance async I/O
   - Enhanced with uvloop on macOS/Linux (30-40% faster)
   - Parallel downloads with configurable workers (default: 4)
   - Entry: `run_async_downloads()`

2. **Sync Mode (Fallback)**: main.py
   - Uses requests library with ThreadPoolExecutor
   - Activated via `--sync` flag
   - Less performant but more stable for some edge cases

### Tracking System (Dual-Backend)
- **download_database.py** (678 lines): SQLite-based tracking system (v2.0+)
  - Primary database: `download_index.db`
  - Rich metadata: course name, lesson name, file type, size, SHA-256 hash, timestamps
  - Thread-safe with locks for concurrent access
  - Features: statistics, integrity verification, JSON export/import
  - Auto-migrates from legacy JSON format

- **Legacy JSON System**: async_downloader.py (DownloadIndex class)
  - Simple set-based tracking in `download_index.json`
  - Maintained for backwards compatibility via `--use-json` flag
  - Deprecated but still functional

### UI Components
- **ui.py** (268 lines): Terminal UI utilities
  - ASCII art headers with rounded borders
  - Status lines with colored icons (✓, ●, ⚠, ✗)
  - Panels and progress indicators
  - All visual elements use Unicode box-drawing characters

### Video Compression
- **compress_videos.py** (359 lines): FFmpeg-based video compression
  - Supports H.265 (better compression) and H.264 (compatibility)
  - Quality presets: high (CRF 18), balanced (CRF 23), small (CRF 28)
  - Parallel compression with configurable workers
  - Integrated into main workflow or standalone usage

## Common Commands

### Setup
```bash
# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Downloads
```bash
# Basic usage (async mode, headless after first login)
python main.py

# Headless mode (no browser window)
python main.py --headless

# Custom directory
python main.py -d ~/Downloads/Cursos

# Increase parallel downloads
python main.py --workers 8

# Fallback to sync mode
python main.py --sync

# Use legacy JSON tracking instead of SQLite
python main.py --use-json

# View download statistics
python main.py --stats

# Verify file integrity
python main.py --verify
```

### Video Compression
```bash
# Dry-run (show what would be compressed)
python compress_videos.py --dry-run

# Compress with defaults (H.265, balanced quality)
python compress_videos.py

# High quality, keep originals
python compress_videos.py --quality high

# Maximum compression, delete originals
python compress_videos.py --quality small --delete

# Use H.264 for compatibility
python compress_videos.py --codec h264

# Parallel compression workers
python compress_videos.py --workers 4

# Via shell wrapper
./compress.sh
```

### Testing
```bash
# Test download database functionality
python test_download_database.py

# Test compression workflow
python test_compression.py

# Test UI components
python demo_ui.py
```

## Key Technical Details

### Performance Optimizations
- **orjson**: 10x faster JSON parsing (fallback to stdlib json)
- **uvloop**: 30-40% faster async on macOS/Linux (auto-detected)
- **Connection pooling**: Reused HTTP connections via requests.Session
- **Compression**: Accept-Encoding header for 60-80% bandwidth savings
- **Resume capability**: .part files for interrupted downloads
- **Batch operations**: mark_completed_batch() to reduce I/O

### Retry & Resilience
- Exponential backoff: 2s, 4s, 8s delays over 4 attempts
- Network errors preserve .part files for resume
- Other errors clean up .part files to prevent corruption
- HTTP 416 (Range Not Satisfiable) detection for completed downloads
- HTTP 206 (Partial Content) for resume support

### Authentication & Session Management
- First run: Opens browser for manual login, saves cookies to `cookies.json`
- Subsequent runs: Reuses saved cookies (no browser needed with --headless)
- Session validation before starting downloads
- Cookie expiration handling with re-login

### File Organization Pattern
```
Base Directory/
  ├── Course_Name/
  │   ├── Lesson_01_Title/
  │   │   ├── Assuntos.txt
  │   │   ├── PDF_Original.pdf
  │   │   ├── PDF_Simplificado.pdf
  │   │   ├── Video_720p.mp4
  │   │   └── Video_Resumo.pdf
  │   └── Lesson_02_Title/
  └── download_index.db  # or download_index.json
```

### Download Tracking Schema (SQLite)
```sql
downloads (
  id, file_path [UNIQUE], file_name, url,
  course_name, lesson_name, file_type,
  size_bytes, sha256, downloaded_at,
  verified, verified_at
)
```

### Database API Compatibility
Both DownloadDatabase (SQLite) and DownloadIndex (JSON) implement:
- `is_downloaded(file_path) -> bool`
- `mark_downloaded(file_path, ...) -> None`  # DownloadDatabase has metadata params
- `mark_completed(file_path) -> None`  # Legacy DownloadIndex only

## Important Constraints

### macOS-Specific
- Default download path is iCloud Drive: `~/Library/Mobile Documents/com~apple~CloudDocs/...`
- FFmpeg installation: `brew install ffmpeg`
- Uses Chrome or Edge for Selenium (Safari not supported)

### Selenium/Browser
- Requires Chrome or Edge installed
- Uses webdriver-manager for automatic driver management
- Never use `git commit` flags like `-i` (interactive) with Selenium/automation

### File Naming
- Sanitization removes: `< > : " / \ | ? * . ,` and spaces → underscores
- See `sanitize_filename()` in main.py for exact logic

### Thread Safety
- DownloadDatabase uses threading.Lock for concurrent access
- DownloadIndex snapshots the set before iteration to avoid RuntimeError
- Both safe for use with ThreadPoolExecutor and asyncio

## Migration Notes

### JSON → SQLite Migration
When upgrading from v1.x to v2.0+:
1. System auto-detects `download_index.json` on first run
2. Creates `download_index.db` and migrates data
3. Backs up JSON as `download_index.json.backup.TIMESTAMP`
4. No manual intervention required

To force JSON mode: `python main.py --use-json`

### Adding New File Types
When adding support for new downloadable file types:
1. Add file type detection logic in main.py link collection
2. Update `file_type` parameter in `mark_downloaded()` calls
3. Consider updating statistics display if relevant

## Video Compression Integration

Video compression happens automatically after each course download completes (if FFmpeg is available). The integration is in `compress_course_videos()` at main.py:715.

Settings:
- Codec: H.265 (best compression)
- Quality: Balanced (CRF 23)
- Workers: 2 parallel compressions
- Delete originals: Yes

To disable auto-compression, comment out the call in the course loop at main.py (search for `compress_course_videos`).

## Troubleshooting Patterns

### No space left on device (Errno 28)
Downloads stop, .part files preserved. After freeing space: just re-run, script resumes.

### SSL certificate errors
Already disabled via `ssl._create_default_https_context = _create_unverified_context` and `SESSION.verify = False`.

### "Nenhum arquivo encontrado nesta aula"
Normal warning for unpublished lessons or exercise-only content. Not an error.

### Cookie expiration
Delete `cookies.json`, re-run without `--headless` to login again.

## Code Style Notes

- Type hints used throughout (Python 3.9+)
- Colorama for cross-platform colored output
- tqdm for all progress indicators
- Error logging via log_error(), log_warn(), log_success(), log_info()
- All user-facing text in Portuguese (Brazilian)
