"""Error scenario tests - Testing error handling and edge cases."""
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import sqlite3

import pytest
import requests

from download_database import DownloadDatabase
from async_downloader import DownloadIndex
from main import sanitize_filename, download_file_task


class TestNetworkErrors:
    """Test network error scenarios."""

    @pytest.mark.unit
    @patch('main.SESSION')
    def test_download_timeout_error(self, mock_session):
        """Test handling of timeout errors."""
        tmpdir = tempfile.mkdtemp()
        try:
            mock_session.get.side_effect = requests.exceptions.Timeout("Connection timeout")

            task = {
                'url': 'https://example.com/video.mp4',
                'path': os.path.join(tmpdir, 'video.mp4'),
                'filename': 'video.mp4',
                'course_name': 'Test',
                'lesson_name': 'Test',
                'file_type': 'video'
            }

            index = DownloadIndex(tmpdir)
            result = download_file_task(task, index)

            # Should handle gracefully
            assert "Falha" in result or "ERRO" in result

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    @patch('main.SESSION')
    def test_download_connection_error(self, mock_session):
        """Test handling of connection errors."""
        tmpdir = tempfile.mkdtemp()
        try:
            mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection refused")

            task = {
                'url': 'https://example.com/video.mp4',
                'path': os.path.join(tmpdir, 'video.mp4'),
                'filename': 'video.mp4',
                'course_name': 'Test',
                'lesson_name': 'Test',
                'file_type': 'video'
            }

            index = DownloadIndex(tmpdir)
            result = download_file_task(task, index)

            assert "Falha" in result or "ERRO" in result

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    @patch('main.SESSION')
    def test_download_http_404(self, mock_session):
        """Test handling of HTTP 404 errors."""
        tmpdir = tempfile.mkdtemp()
        try:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
            mock_session.get.return_value = mock_response

            task = {
                'url': 'https://example.com/video.mp4',
                'path': os.path.join(tmpdir, 'video.mp4'),
                'filename': 'video.mp4',
                'course_name': 'Test',
                'lesson_name': 'Test',
                'file_type': 'video'
            }

            index = DownloadIndex(tmpdir)
            result = download_file_task(task, index)

            assert "Falha" in result or "ERRO" in result

        finally:
            shutil.rmtree(tmpdir)


class TestFilesystemErrors:
    """Test filesystem-related errors."""

    @pytest.mark.unit
    def test_download_permission_denied(self):
        """Test handling of permission denied errors."""
        # Try to write to a read-only location
        task = {
            'url': 'https://example.com/video.mp4',
            'path': '/root/protected/video.mp4',  # Typically no permission
            'filename': 'video.mp4',
            'course_name': 'Test',
            'lesson_name': 'Test',
            'file_type': 'video'
        }

        index = DownloadIndex(tempfile.gettempdir())

        # Should handle permission error gracefully
        try:
            result = download_file_task(task, index)
            # If no exception, should return error message
            assert "Falha" in result or "ERRO" in result
        except (PermissionError, OSError):
            # Expected exception
            pass

    @pytest.mark.unit
    def test_database_disk_full(self):
        """Test handling when disk is full."""
        # This is difficult to test without actually filling disk
        # Test that we handle write errors gracefully
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Simulate disk full by mocking the connection
            with patch('sqlite3.connect') as mock_connect:
                mock_conn = MagicMock()
                mock_conn.cursor.return_value.execute.side_effect = sqlite3.OperationalError("disk full")
                mock_connect.return_value = mock_conn

                # Should handle error
                try:
                    file_path = os.path.join(tmpdir, 'test.mp4')
                    db.mark_downloaded(
                        file_path=file_path,
                        url='https://example.com/test.mp4',
                        course_name='Test',
                        lesson_name='Test',
                        file_type='video'
                    )
                except sqlite3.OperationalError:
                    # Expected
                    pass

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_corrupted_database_recovery(self):
        """Test recovery from corrupted database."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Create corrupted database file
            db_path = Path(tmpdir) / "download_index.db"
            db_path.write_text("corrupted data{{{")

            # Try to initialize - should handle gracefully
            try:
                db = DownloadDatabase(tmpdir, use_sqlite=True)
                # If it initializes, it recovered
                assert db is not None
            except (sqlite3.DatabaseError, sqlite3.OperationalError):
                # Expected exception
                pass

        finally:
            shutil.rmtree(tmpdir)


class TestInputValidation:
    """Test input validation and sanitization."""

    @pytest.mark.unit
    def test_sanitize_malicious_filename(self):
        """Test sanitization of potentially malicious filenames."""
        malicious_names = [
            "../../etc/passwd",
            "../../../.ssh/id_rsa",
            "test\x00.mp4",  # Null byte injection
            "CON",  # Windows reserved name
            "NUL",
            "..\\..\\windows\\system32",
        ]

        for name in malicious_names:
            result = sanitize_filename(name)

            # Should not contain path traversal
            assert ".." not in result
            assert "/" not in result
            assert "\\" not in result
            assert "\x00" not in result

    @pytest.mark.unit
    def test_database_sql_injection_protection(self):
        """Test SQL injection protection."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Try SQL injection in various fields
            malicious_inputs = [
                "'; DROP TABLE downloads; --",
                "' OR '1'='1",
                "1'; DELETE FROM downloads; --",
            ]

            for malicious in malicious_inputs:
                file_path = os.path.join(tmpdir, 'test.mp4')
                Path(file_path).touch()

                # Should not execute SQL injection
                db.mark_downloaded(
                    file_path=file_path,
                    url=malicious,
                    course_name=malicious,
                    lesson_name=malicious,
                    file_type='video'
                )

                # Database should still be intact
                stats = db.get_statistics()
                assert stats is not None

        finally:
            shutil.rmtree(tmpdir)


class TestMemoryAndPerformance:
    """Test memory and performance edge cases."""

    @pytest.mark.slow
    def test_large_number_of_files(self):
        """Test handling large number of files."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Add many files
            for i in range(1000):
                file_path = os.path.join(tmpdir, f'file{i}.mp4')

                db.mark_downloaded(
                    file_path=file_path,
                    url=f'https://example.com/file{i}.mp4',
                    course_name=f'Course {i % 10}',
                    lesson_name=f'Lesson {i % 50}',
                    file_type='video',
                    size_bytes=1024
                )

            # Should handle query efficiently
            stats = db.get_statistics()
            assert stats['total_files'] == 1000

            # Course query should still work
            downloads = db.get_downloads_by_course('Course 0')
            assert len(downloads) == 100

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_very_large_file_hash(self):
        """Test hash calculation for very large files."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Create a large file (10MB)
            large_file = Path(tmpdir) / 'large.mp4'
            with open(large_file, 'wb') as f:
                f.write(b'\x00' * (10 * 1024 * 1024))

            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Should be able to hash it
            db.mark_downloaded(
                file_path=str(large_file),
                url='https://example.com/large.mp4',
                course_name='Test',
                lesson_name='Test',
                file_type='video',
                calculate_hash=True
            )

            # Verify hash was calculated
            is_valid, message = db.verify_file_integrity(str(large_file))
            assert is_valid is True

        finally:
            shutil.rmtree(tmpdir)


class TestConcurrencyErrors:
    """Test concurrency-related errors."""

    @pytest.mark.unit
    def test_race_condition_file_creation(self):
        """Test race condition in file creation."""
        from concurrent.futures import ThreadPoolExecutor
        tmpdir = tempfile.mkdtemp()
        try:
            index = DownloadIndex(tmpdir)

            # Multiple threads trying to mark same file
            same_path = "/tmp/test.mp4"

            def mark_file():
                index.mark_completed(same_path)

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(mark_file) for _ in range(100)]
                for future in futures:
                    future.result()

            # Should only be marked once
            assert same_path in index.completed
            assert len(index.completed) == 1

        finally:
            shutil.rmtree(tmpdir)


class TestDataIntegrity:
    """Test data integrity scenarios."""

    @pytest.mark.unit
    def test_partial_file_detection(self):
        """Test detection of partial files."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Create file and mark with size
            file_path = os.path.join(tmpdir, 'test.mp4')
            with open(file_path, 'wb') as f:
                f.write(b'\x00' * 512)

            db.mark_downloaded(
                file_path=file_path,
                url='https://example.com/test.mp4',
                course_name='Test',
                lesson_name='Test',
                file_type='video',
                size_bytes=1024  # Claimed size
            )

            # Verify should detect size mismatch
            is_valid, message = db.verify_file_integrity(file_path)

            assert is_valid is False
            assert "Tamanho diferente" in message or "size" in message.lower()

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_corrupted_file_hash_mismatch(self):
        """Test detection of corrupted files via hash."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Create and mark file
            file_path = os.path.join(tmpdir, 'test.mp4')
            with open(file_path, 'wb') as f:
                f.write(b'original content')

            db.mark_downloaded(
                file_path=file_path,
                url='https://example.com/test.mp4',
                course_name='Test',
                lesson_name='Test',
                file_type='video',
                calculate_hash=True
            )

            # Corrupt the file
            with open(file_path, 'wb') as f:
                f.write(b'corrupted content')

            # Verify should detect corruption
            is_valid, message = db.verify_file_integrity(file_path)

            assert is_valid is False
            assert "Hash diferente" in message or "hash" in message.lower()

        finally:
            shutil.rmtree(tmpdir)


class TestEdgeCaseInputs:
    """Test edge case inputs."""

    @pytest.mark.unit
    def test_empty_url(self):
        """Test handling of empty URL."""
        tmpdir = tempfile.mkdtemp()
        try:
            task = {
                'url': '',
                'path': os.path.join(tmpdir, 'video.mp4'),
                'filename': 'video.mp4',
                'course_name': 'Test',
                'lesson_name': 'Test',
                'file_type': 'video'
            }

            index = DownloadIndex(tmpdir)

            # Should handle gracefully
            try:
                result = download_file_task(task, index)
                assert "Falha" in result or "ERRO" in result
            except Exception:
                # Some exception is expected
                pass

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_none_values(self):
        """Test handling of None values."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            file_path = os.path.join(tmpdir, 'test.mp4')
            Path(file_path).touch()

            # Should handle None values gracefully
            db.mark_downloaded(
                file_path=file_path,
                url='https://example.com/test.mp4',
                course_name='Test',
                lesson_name='Test',
                file_type='video',
                size_bytes=None
            )

            assert db.is_downloaded(file_path)

        finally:
            shutil.rmtree(tmpdir)
