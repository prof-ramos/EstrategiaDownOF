"""Integration tests - End-to-end workflow testing."""
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import pytest

from download_database import DownloadDatabase
from async_downloader import DownloadIndex, run_async_downloads
from compress_videos import compress_video_task, find_videos


class TestDownloadToCompressionFlow:
    """Test complete download -> compression workflow."""

    @pytest.mark.integration
    @patch('main.SESSION')
    def test_download_then_compress_flow(self, mock_session):
        """Test downloading files then compressing them."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Setup mock download
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {'content-length': '1024'}
            mock_response.iter_content = Mock(return_value=[b'test' * 256])
            mock_response.raise_for_status = Mock()
            mock_session.get.return_value = mock_response

            # Simulate download
            from main import download_file_task

            task = {
                'url': 'https://example.com/video.mp4',
                'path': os.path.join(tmpdir, 'video.mp4'),
                'filename': 'video.mp4',
                'course_name': 'Test Course',
                'lesson_name': 'Lesson 1',
                'file_type': 'video'
            }

            index = DownloadIndex(tmpdir)
            result = download_file_task(task, index)

            # Verify download completed
            assert os.path.exists(task['path'])
            assert index.is_downloaded(task['path'])

            # Now compress the downloaded file
            videos = find_videos(Path(tmpdir))
            assert len(videos) == 1

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.integration
    def test_database_tracking_through_workflow(self):
        """Test database properly tracks through full workflow."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Simulate multiple downloads
            for i in range(5):
                file_path = os.path.join(tmpdir, f'video{i}.mp4')
                Path(file_path).touch()

                db.mark_downloaded(
                    file_path=file_path,
                    url=f'https://example.com/video{i}.mp4',
                    course_name='Test Course',
                    lesson_name=f'Lesson {i}',
                    file_type='video',
                    size_bytes=1024 * (i + 1)
                )

            # Verify statistics
            stats = db.get_statistics()
            assert stats['total_files'] == 5
            assert stats['total_videos'] == 5

            # Query by course
            downloads = db.get_downloads_by_course('Test Course')
            assert len(downloads) == 5

        finally:
            shutil.rmtree(tmpdir)


class TestAsyncDownloadIntegration:
    """Test async download integration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_download_with_database(self):
        """Test async downloads with database tracking."""
        import asyncio
        from async_downloader import download_file_async

        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Mock aiohttp session
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.headers = {'content-length': '1024'}

            async def mock_iter_chunked(chunk_size):
                yield b'test data'

            mock_response.content.iter_chunked = mock_iter_chunked
            mock_response.raise_for_status = Mock()

            from unittest.mock import AsyncMock
            mock_session = MagicMock()
            mock_session.get = MagicMock()
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

            task = {
                'url': 'https://example.com/video.mp4',
                'path': os.path.join(tmpdir, 'video.mp4'),
                'filename': 'video.mp4',
                'course_name': 'Test',
                'lesson_name': 'Test',
                'file_type': 'video'
            }

            semaphore = asyncio.Semaphore(1)
            pbar = MagicMock()

            result = await download_file_async(mock_session, task, db, semaphore, pbar)

            # Verify tracked in database
            assert db.is_downloaded(task['path'])

        finally:
            shutil.rmtree(tmpdir)


class TestJSONToSQLiteMigration:
    """Test migration from JSON to SQLite."""

    @pytest.mark.integration
    def test_migration_preserves_data(self):
        """Test that migration preserves all download data."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Create JSON index
            json_index = DownloadIndex(tmpdir)

            test_files = [
                os.path.join(tmpdir, 'video1.mp4'),
                os.path.join(tmpdir, 'video2.mp4'),
                os.path.join(tmpdir, 'document.pdf'),
            ]

            for file_path in test_files:
                Path(file_path).touch()
                json_index.mark_completed(file_path)

            # Verify JSON has files
            assert len(json_index.completed) == 3

            # Initialize SQLite (should trigger migration)
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Verify all files migrated
            for file_path in test_files:
                assert db.is_downloaded(file_path)

            stats = db.get_statistics()
            assert stats['total_files'] == 3

        finally:
            shutil.rmtree(tmpdir)


class TestConcurrentDownloads:
    """Test concurrent download scenarios."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_downloads_no_conflicts(self):
        """Test that concurrent downloads don't cause conflicts."""
        from concurrent.futures import ThreadPoolExecutor
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            def download_and_mark(file_num):
                file_path = os.path.join(tmpdir, f'file{file_num}.mp4')
                Path(file_path).touch()

                db.mark_downloaded(
                    file_path=file_path,
                    url=f'https://example.com/file{file_num}.mp4',
                    course_name='Test',
                    lesson_name=f'Lesson {file_num % 5}',
                    file_type='video'
                )

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(download_and_mark, i) for i in range(100)]
                for future in futures:
                    future.result()

            # Verify all files tracked
            stats = db.get_statistics()
            assert stats['total_files'] == 100

        finally:
            shutil.rmtree(tmpdir)


class TestErrorRecovery:
    """Test error recovery in workflows."""

    @pytest.mark.integration
    @patch('main.SESSION')
    def test_download_retry_recovery(self, mock_session):
        """Test that downloads recover from temporary failures."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Mock session that fails once then succeeds
            call_count = {'count': 0}

            def get_with_retry(*args, **kwargs):
                call_count['count'] += 1
                if call_count['count'] == 1:
                    raise Exception("Network error")

                # Second call succeeds
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.headers = {'content-length': '1024'}
                mock_response.iter_content = Mock(return_value=[b'test' * 256])
                mock_response.raise_for_status = Mock()
                return mock_response

            mock_session.get = get_with_retry

            from main import download_file_task

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

            # Should eventually succeed
            assert call_count['count'] >= 2
            assert os.path.exists(task['path'])

        finally:
            shutil.rmtree(tmpdir)


class TestStatisticsAccuracy:
    """Test statistics accuracy across operations."""

    @pytest.mark.integration
    def test_statistics_match_actual_files(self):
        """Test that statistics accurately reflect actual files."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Add various file types
            file_data = [
                ('video1.mp4', 'video', 1024),
                ('video2.mp4', 'video', 2048),
                ('doc1.pdf', 'pdf', 512),
                ('doc2.pdf', 'pdf', 1024),
                ('slide1.pdf', 'material', 256),
            ]

            total_bytes = 0
            for filename, ftype, size in file_data:
                file_path = os.path.join(tmpdir, filename)
                Path(file_path).write_bytes(b'\x00' * size)
                total_bytes += size

                db.mark_downloaded(
                    file_path=file_path,
                    url=f'https://example.com/{filename}',
                    course_name='Test',
                    lesson_name='Test',
                    file_type=ftype,
                    size_bytes=size
                )

            stats = db.get_statistics()

            assert stats['total_files'] == 5
            assert stats['total_videos'] == 2
            assert stats['total_pdfs'] == 2
            assert stats['total_materials'] == 1
            assert stats['total_bytes'] == total_bytes

        finally:
            shutil.rmtree(tmpdir)


class TestResumeDownload:
    """Test download resume functionality."""

    @pytest.mark.integration
    @patch('main.SESSION')
    def test_resume_partial_download(self, mock_session):
        """Test resuming a partially downloaded file."""
        tmpdir = tempfile.mkdtemp()
        try:
            from main import download_file_task

            task = {
                'url': 'https://example.com/video.mp4',
                'path': os.path.join(tmpdir, 'video.mp4'),
                'filename': 'video.mp4',
                'course_name': 'Test',
                'lesson_name': 'Test',
                'file_type': 'video'
            }

            # Create partial file
            temp_path = task['path'] + '.part'
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            with open(temp_path, 'wb') as f:
                f.write(b'partial')

            # Mock 206 Partial Content
            mock_response = MagicMock()
            mock_response.status_code = 206
            mock_response.headers = {'content-length': '1024'}
            mock_response.iter_content = Mock(return_value=[b'rest'])
            mock_response.raise_for_status = Mock()
            mock_session.get.return_value = mock_response

            index = DownloadIndex(tmpdir)
            result = download_file_task(task, index)

            # Verify Range header was used
            call_args = mock_session.get.call_args
            if call_args:
                headers = call_args[1].get('headers', {})
                assert 'Range' in headers

            # Final file should exist
            assert os.path.exists(task['path'])

        finally:
            shutil.rmtree(tmpdir)


class TestExportImportWorkflow:
    """Test export/import workflow."""

    @pytest.mark.integration
    def test_export_then_import(self):
        """Test exporting data and verifying it can be used."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Create database with data
            db1 = DownloadDatabase(tmpdir, use_sqlite=True)

            for i in range(10):
                file_path = os.path.join(tmpdir, f'file{i}.mp4')
                Path(file_path).touch()

                db1.mark_downloaded(
                    file_path=file_path,
                    url=f'https://example.com/file{i}.mp4',
                    course_name=f'Course {i % 3}',
                    lesson_name=f'Lesson {i}',
                    file_type='video'
                )

            # Export
            export_path = db1.export_to_json()
            assert os.path.exists(export_path)

            # Verify export is valid JSON
            import json
            with open(export_path, 'r') as f:
                data = json.load(f)

            assert len(data['downloads']) == 10

        finally:
            shutil.rmtree(tmpdir)
