"""Pytest configuration and shared fixtures."""
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock

import pytest


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that is cleaned up after test."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_download_dir(temp_dir):
    """Provide a structured temporary download directory."""
    download_dir = Path(temp_dir) / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)

    # Create sample structure
    course_dir = download_dir / "Curso_Teste"
    lesson_dir = course_dir / "Aula_01"
    lesson_dir.mkdir(parents=True, exist_ok=True)

    yield download_dir


@pytest.fixture
def sample_download_task() -> Dict[str, Any]:
    """Provide a standard download task dictionary."""
    return {
        'url': 'https://example.com/video.mp4',
        'path': '/tmp/test_video.mp4',
        'filename': 'test_video.mp4',
        'referer': 'https://example.com/course',
        'course_name': 'Curso Teste',
        'lesson_name': 'Aula 01',
        'file_type': 'video'
    }


@pytest.fixture
def sample_video_file(temp_dir):
    """Create a small sample video file for testing."""
    video_path = Path(temp_dir) / "test_video.mp4"
    # Create a small file with some content (not a real video)
    video_path.write_bytes(b'\x00' * 1024)  # 1KB file
    yield video_path


@pytest.fixture
def mock_selenium_driver():
    """Provide a mock Selenium WebDriver."""
    driver = MagicMock()
    driver.get = Mock()
    driver.find_element = Mock()
    driver.find_elements = Mock(return_value=[])
    driver.get_cookies = Mock(return_value=[
        {'name': 'session', 'value': 'test123', 'domain': 'example.com'}
    ])
    driver.add_cookie = Mock()
    driver.quit = Mock()
    driver.current_url = "https://example.com/test"
    driver.execute_script = Mock(return_value=[])

    yield driver


@pytest.fixture
def mock_requests_session(mocker):
    """Provide a mock requests Session."""
    session = mocker.MagicMock()
    response = mocker.MagicMock()
    response.status_code = 200
    response.headers = {'content-length': '1024'}
    response.iter_content = Mock(return_value=[b'test' * 256])
    response.raise_for_status = Mock()
    session.get = Mock(return_value=response)

    yield session


@pytest.fixture
def mock_aiohttp_session():
    """Provide a mock aiohttp ClientSession."""
    session = MagicMock()

    # Mock response
    response = MagicMock()
    response.status = 200
    response.headers = {'content-length': '1024'}

    # Mock async context manager
    async def mock_iter_chunked(chunk_size):
        yield b'test' * 256

    response.content.iter_chunked = mock_iter_chunked
    response.raise_for_status = Mock()

    # Mock session.get context manager
    session.get = MagicMock()
    session.get.return_value.__aenter__ = Mock(return_value=response)
    session.get.return_value.__aexit__ = Mock(return_value=None)

    yield session


@pytest.fixture
def sample_cookies_data():
    """Provide sample cookie data."""
    return [
        {
            'name': 'session_id',
            'value': 'abc123',
            'domain': 'estrategiaconcursos.com.br',
            'path': '/',
            'secure': True,
            'httpOnly': True,
            'sameSite': 'Lax'
        },
        {
            'name': 'user_token',
            'value': 'xyz789',
            'domain': 'estrategiaconcursos.com.br',
            'path': '/',
            'secure': True
        }
    ]


@pytest.fixture
def sample_course_data():
    """Provide sample course structure data."""
    return {
        'title': 'Direito Constitucional',
        'url': 'https://example.com/course/123',
        'lessons': [
            {
                'title': 'Princípios Fundamentais',
                'url': 'https://example.com/lesson/1',
                'subtitle': 'Introdução aos princípios'
            },
            {
                'title': 'Direitos e Garantias',
                'url': 'https://example.com/lesson/2',
                'subtitle': 'Direitos fundamentais'
            }
        ]
    }


@pytest.fixture
def mock_download_database(mocker, temp_dir):
    """Provide a mock DownloadDatabase."""
    from download_database import DownloadDatabase

    db = DownloadDatabase(temp_dir, use_sqlite=True)
    yield db


@pytest.fixture
def mock_download_index(mocker, temp_dir):
    """Provide a mock DownloadIndex."""
    from async_downloader import DownloadIndex

    index = DownloadIndex(temp_dir)
    yield index


# Markers for test categorization
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_ffmpeg: mark test as requiring FFmpeg"
    )
    config.addinivalue_line(
        "markers", "requires_selenium: mark test as requiring Selenium"
    )
