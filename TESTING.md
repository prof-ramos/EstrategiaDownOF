# Testing Guide

## Overview

This project now has comprehensive test coverage for critical functionality. Tests are organized by priority and type.

## Test Structure

```
.
├── conftest.py                          # Shared fixtures and configuration
├── pytest.ini                           # Pytest configuration
├── requirements-dev.txt                 # Testing dependencies
│
├── test_main_comprehensive.py           # Main.py critical path tests
├── test_async_downloader_comprehensive.py # Async download tests
├── test_download_database_enhanced.py   # Enhanced database tests
├── test_compression_enhanced.py         # Enhanced compression tests
├── test_ui_formatting.py                # UI formatting tests
├── test_integration.py                  # Integration tests
├── test_error_scenarios.py              # Error handling tests
│
└── Legacy tests (maintained for compatibility):
    ├── test_compression.py
    ├── test_download_database.py
    ├── test_improvements.py
    └── test_race_condition.py
```

## Installation

Install testing dependencies:

```bash
pip install -r requirements-dev.txt
```

Dependencies include:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `aioresponses` - Async HTTP mocking
- `responses` - HTTP mocking
- `freezegun` - Time mocking
- `faker` - Test data generation

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest test_main_comprehensive.py
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run only unit tests
```bash
pytest -m unit
```

### Run only integration tests
```bash
pytest -m integration
```

### Run excluding slow tests
```bash
pytest -m "not slow"
```

### Run with verbose output
```bash
pytest -v
```

## Test Categories

Tests are marked with categories:

- **@pytest.mark.unit** - Fast unit tests
- **@pytest.mark.integration** - Integration tests
- **@pytest.mark.slow** - Slow-running tests
- **@pytest.mark.requires_ffmpeg** - Tests requiring FFmpeg
- **@pytest.mark.requires_selenium** - Tests requiring Selenium

## Coverage Goals

| Module | Target Coverage | Current Status |
|--------|----------------|----------------|
| main.py | 80% | ✅ High priority tests added |
| async_downloader.py | 80% | ✅ Async tests added |
| download_database.py | 90% | ✅ Enhanced coverage |
| compress_videos.py | 70% | ✅ Enhanced coverage |
| ui.py | 60% | ✅ Formatting tests added |

## Key Test Files

### test_main_comprehensive.py
Tests for main.py including:
- Filename sanitization
- Retry mechanism with backoff
- Cookie handling (save/load)
- Download task execution
- Queue processing
- Video compression integration

### test_async_downloader_comprehensive.py
Tests for async_downloader.py including:
- DownloadIndex operations
- Async file downloads
- Resume functionality
- Error handling and retries
- Concurrent downloads
- Thread safety

### test_download_database_enhanced.py
Enhanced tests for download_database.py including:
- Export/import functionality
- Context manager usage
- Query operations
- Edge cases (unicode, special chars)
- Statistics accuracy
- JSON fallback mode

### test_compression_enhanced.py
Enhanced tests for compress_videos.py including:
- Video info extraction
- Video discovery
- Compression execution
- FFmpeg integration
- Error handling

### test_ui_formatting.py
Tests for ui.py including:
- All formatting functions
- Edge cases (long names, special chars)
- Terminal width handling
- Color code handling

### test_integration.py
Integration tests including:
- Download → Compression workflow
- Database tracking through workflows
- JSON → SQLite migration
- Concurrent operations
- Error recovery
- Statistics accuracy

### test_error_scenarios.py
Error scenario tests including:
- Network errors (timeouts, connection failures)
- Filesystem errors (permissions, disk full)
- Input validation and SQL injection protection
- Memory and performance edge cases
- Data integrity checks

## Fixtures

Shared fixtures in `conftest.py`:

- `temp_dir` - Temporary directory (auto-cleanup)
- `temp_download_dir` - Structured download directory
- `sample_download_task` - Standard download task dict
- `sample_video_file` - Sample video file for testing
- `mock_selenium_driver` - Mock WebDriver
- `mock_requests_session` - Mock requests Session
- `mock_aiohttp_session` - Mock aiohttp ClientSession
- `mock_download_database` - Mock DownloadDatabase
- `mock_download_index` - Mock DownloadIndex

## Best Practices

1. **Use appropriate markers** - Mark tests with `@pytest.mark.unit`, `@pytest.mark.integration`, etc.

2. **Use fixtures** - Leverage shared fixtures instead of duplicating setup code

3. **Mock external dependencies** - Use mocks for HTTP requests, Selenium, FFmpeg

4. **Clean up resources** - Use context managers and fixtures with cleanup

5. **Test both success and failure** - Test happy path AND error scenarios

6. **Descriptive names** - Test names should clearly describe what they test

## CI/CD Integration

To integrate with CI/CD:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Troubleshooting

### Tests fail due to missing FFmpeg
- Tests marked with `@pytest.mark.requires_ffmpeg` require FFmpeg installed
- Skip these tests: `pytest -m "not requires_ffmpeg"`

### Tests fail due to missing Selenium
- Tests marked with `@pytest.mark.requires_selenium` require browser drivers
- Skip these tests: `pytest -m "not requires_selenium"`

### Async tests fail
- Ensure `pytest-asyncio` is installed
- Check `asyncio_mode = auto` in `pytest.ini`

### Import errors
- Ensure all dependencies installed: `pip install -r requirements.txt requirements-dev.txt`

## Contributing

When adding new functionality:

1. Write tests FIRST (TDD approach)
2. Aim for 80%+ coverage on new code
3. Include both unit and integration tests
4. Test error scenarios
5. Update this documentation

## Continuous Improvement

Future test enhancements:
- [ ] Add performance benchmarks
- [ ] Add mutation testing
- [ ] Add property-based testing (Hypothesis)
- [ ] Add E2E tests with real browsers
- [ ] Add load testing for concurrent operations
