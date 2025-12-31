# AGENTS.md - Agent Guidelines for EstrategiaDownloader

This file contains guidelines for agentic coding assistants working on this repository.

## Build & Test Commands

### Installation

```bash
pip install -r requirements.txt
```

### Running Tests

```bash
# Run all improvement tests
python test_improvements.py

# Run race condition tests
python test_race_condition.py

# Run a single test function (add at bottom of test file):
if __name__ == "__main__":
    test_imports()  # Replace with specific function name
```

### Running the Application

```bash
# Default async mode
python main.py

# Synchronous mode
python main.py --sync

# Headless mode with custom workers
python main.py --headless --workers 8
```

### Linting & Type Checking

No formal linting or type checking commands configured. Use `python -m py_compile` for syntax
checks.

## Code Style Guidelines

### Imports

- Always start with `from __future__ import annotations` for Python 3.9+ compatibility
- Group imports: standard lib, third-party, local
- Use `TYPE_CHECKING` to avoid circular imports for type-only imports

### Type Hints

- Use Python 3.9+ style: `dict[str, str]`, `list[str]`, `int | None`
- All functions need type hints for parameters and return types
- Use `Literal` for enum-like string values

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

### Formatting & Structure

- Docstrings use triple quotes with Args/Returns sections
- Maximum line length: 120 characters (aim for readability)
- Use `with` statements for resource management
- Comments in Portuguese (matching codebase)

### Error Handling

- Use specific exceptions: `OSError`, `IOError`, `ValueError`, `aiohttp.ClientError`
- Use try/except with `pass` for expected/ignorable failures
- Log with colorama: `log_error()`, `log_warn()`, `log_info()`, `log_success()`
- Clean up partial files on non-recoverable errors

### Performance Optimizations

- Precompute translation tables: `str.maketrans()` at module load
- Use `CHUNK_SIZE = 131072` (128KB) for download chunks
- Batch I/O operations where possible

### Thread Safety

- Use `threading.Lock()` for protecting shared state
- Always use `with lock:` context managers
- Create snapshots before iteration to avoid `RuntimeError: Set changed size during iteration`

```python
def mark_completed(self, file_path: str) -> None:
    with self._lock:
        self.completed.add(file_path)
    self.save()  # save() creates its own snapshot
```

### Async/Await Patterns

- Use `asyncio.Semaphore` to limit concurrent operations
- Use `asyncio.gather(*tasks, return_exceptions=True)` for parallel execution
- Handle `asyncio.CancelledError` to preserve partial downloads
- Use `aiofiles` for async file I/O
- Wrap async execution in `asyncio.run()` when calling from sync code

### Retry Logic

- Implement exponential backoff: `delay *= 2`
- Default: `MAX_RETRIES = 4`, `INITIAL_RETRY_DELAY = 2.0` seconds
- Only retry on recoverable errors (network, timeout)
- Use `.part` files for resume support

### Session Management

- Use global `requests.Session()` for connection pooling in sync mode
- Use `aiohttp.TCPConnector` with limits for async mode
- Configure timeout: `aiohttp.ClientTimeout(total=300)` for 5 min
- Set headers: `User-Agent`, `Accept-Encoding`, `Connection: keep-alive`

### Logging & Output

- Use `tqdm.write()` instead of `print()` when progress bars are active
- Colorama functions: `log_info()`, `log_success()`, `log_warn()`, `log_error()`
  - Provided by `main.py` (lines 69-86). Example:
    `from main import log_info, log_success, log_warn, log_error`
- Use Unicode icons: ✓ ✗ ● ⚠ ⚡ 📦 📁

### Constants

- `MAX_WORKERS = 4` (configurable via CLI)
- `CHUNK_SIZE = 131072` (128KB)
- `MAX_RETRIES = 4`
- `INITIAL_RETRY_DELAY = 2.0`
- `INDEX_FILE = "download_index.json"`
- `COOKIES_FILE = "cookies.json"`

### Optional Dependencies Pattern

```python
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
```

Critical: `aiohttp`, `aiofiles`, `requests`, `selenium`, `tqdm`, `colorama`. Optional: `orjson` (10x
JSON speed), `uvloop` (30-40% async speed, macOS/Linux only).

### File Structure

- `main.py`: Entry point, sync download logic, Selenium scraping
- `async_downloader.py`: Async download manager, DownloadIndex class
- `ui.py`: Terminal UI components
- `test_improvements.py`: Integration tests
- `test_race_condition.py`: Thread-safety tests

### Testing Patterns

```python
def test_function() -> bool:
    """Test description."""
    try:
        from module import Class
        with tempfile.TemporaryDirectory() as tmpdir:
            obj = Class(tmpdir)
            assert obj.method() == expected
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False
```

- Tests are standalone Python scripts (not pytest/unittest)
- Use `assert` statements for validation
- Return `True`/`False` from test functions
- Use `tempfile.TemporaryDirectory()` for isolation
- For thread-safety: use `ThreadPoolExecutor` with high concurrency (20+ threads)
