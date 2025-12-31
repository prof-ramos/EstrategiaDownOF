"""Comprehensive tests for main.py - Critical path testing."""
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

import pytest

# Import functions to test
from main import (
    sanitize_filename,
    retry_with_backoff,
    save_cookies,
    load_cookies,
    download_file_task,
    process_download_queue,
)


class TestSanitizeFilename:
    """Test filename sanitization function."""

    @pytest.mark.unit
    def test_basic_sanitization(self):
        """Test basic character removal."""
        result = sanitize_filename("Hello World.txt")
        assert result == "Hello_World_txt"

    @pytest.mark.unit
    def test_special_characters(self):
        """Test removal of special characters."""
        result = sanitize_filename('test<>:"/\\|?*.mp4')
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '"' not in result
        assert '/' not in result
        assert '\\' not in result
        assert '|' not in result
        assert '?' not in result
        assert '*' not in result
        assert '.' not in result

    @pytest.mark.unit
    def test_multiple_spaces(self):
        """Test collapsing multiple spaces to single underscore."""
        result = sanitize_filename("Hello    World")
        assert result == "Hello_World"

    @pytest.mark.unit
    def test_multiple_dashes(self):
        """Test collapsing multiple dashes to single underscore."""
        result = sanitize_filename("Hello---World")
        assert result == "Hello_World"

    @pytest.mark.unit
    def test_leading_trailing_underscores(self):
        """Test removal of leading/trailing underscores."""
        result = sanitize_filename("___test___")
        assert result == "test"

    @pytest.mark.unit
    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        result = sanitize_filename("Tópico Ação")
        # Should replace spaces but keep unicode
        assert '_' in result
        assert 'ó' in result or result != ""

    @pytest.mark.unit
    def test_empty_string(self):
        """Test empty string handling."""
        result = sanitize_filename("")
        assert result == ""

    @pytest.mark.unit
    def test_only_special_chars(self):
        """Test string with only special characters."""
        result = sanitize_filename("....----")
        assert result == ""


class TestRetryWithBackoff:
    """Test retry mechanism with exponential backoff."""

    @pytest.mark.unit
    def test_success_on_first_try(self):
        """Test successful execution on first attempt."""
        func = Mock(return_value=(True, "success"))
        result = retry_with_backoff(func, max_retries=3, initial_delay=0.1)

        assert result == "success"
        assert func.call_count == 1

    @pytest.mark.unit
    def test_success_on_second_try(self):
        """Test successful execution on second attempt."""
        func = Mock(side_effect=[
            (False, None),
            (True, "success")
        ])
        result = retry_with_backoff(func, max_retries=3, initial_delay=0.1)

        assert result == "success"
        assert func.call_count == 2

    @pytest.mark.unit
    def test_failure_all_retries(self):
        """Test failure after all retries exhausted."""
        func = Mock(return_value=(False, None))
        result = retry_with_backoff(func, max_retries=3, initial_delay=0.1)

        assert result is None
        assert func.call_count == 3

    @pytest.mark.unit
    def test_exception_handling(self):
        """Test exception is re-raised on final attempt."""
        func = Mock(side_effect=Exception("Test error"))

        with pytest.raises(Exception, match="Test error"):
            retry_with_backoff(func, max_retries=3, initial_delay=0.1)

    @pytest.mark.unit
    def test_exponential_backoff_timing(self):
        """Test that delays increase exponentially."""
        import time

        call_times = []

        def time_tracking_func():
            call_times.append(time.time())
            return (False, None)

        retry_with_backoff(time_tracking_func, max_retries=3, initial_delay=0.1)

        # Verify we have 3 calls
        assert len(call_times) == 3

        # Verify delays (approximately) double
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            # Second delay should be roughly 2x first delay
            assert delay2 > delay1 * 1.5


class TestCookieHandling:
    """Test cookie save/load functionality."""

    @pytest.mark.unit
    def test_save_cookies_success(self, mock_selenium_driver, temp_dir):
        """Test successful cookie saving."""
        cookie_path = os.path.join(temp_dir, "cookies.json")
        mock_selenium_driver.get_cookies.return_value = [
            {'name': 'test', 'value': '123'}
        ]

        result = save_cookies(mock_selenium_driver, cookie_path)

        assert result is True
        assert os.path.exists(cookie_path)

    @pytest.mark.unit
    def test_save_cookies_failure(self, mock_selenium_driver):
        """Test cookie saving with invalid path."""
        invalid_path = "/invalid/path/cookies.json"
        result = save_cookies(mock_selenium_driver, invalid_path)

        # Should handle error gracefully
        assert result is False

    @pytest.mark.unit
    def test_load_cookies_success(self, mock_selenium_driver, temp_dir, sample_cookies_data):
        """Test successful cookie loading."""
        cookie_path = os.path.join(temp_dir, "cookies.json")

        # Save cookies first
        import json
        with open(cookie_path, 'w') as f:
            json.dump(sample_cookies_data, f)

        result = load_cookies(mock_selenium_driver, cookie_path)

        assert result is True
        # Should have called add_cookie for each cookie (minus sameSite)
        assert mock_selenium_driver.add_cookie.call_count >= 1

    @pytest.mark.unit
    def test_load_cookies_file_not_found(self, mock_selenium_driver):
        """Test loading cookies when file doesn't exist."""
        result = load_cookies(mock_selenium_driver, "/nonexistent/cookies.json")

        assert result is False
        assert mock_selenium_driver.add_cookie.call_count == 0

    @pytest.mark.unit
    def test_load_cookies_invalid_json(self, mock_selenium_driver, temp_dir):
        """Test loading cookies with invalid JSON."""
        cookie_path = os.path.join(temp_dir, "cookies.json")

        with open(cookie_path, 'w') as f:
            f.write("invalid json{{{")

        result = load_cookies(mock_selenium_driver, cookie_path)

        assert result is False


class TestDownloadFileTask:
    """Test individual download task execution."""

    @pytest.mark.unit
    def test_download_already_indexed(self, sample_download_task, mock_download_database):
        """Test skipping already indexed files."""
        # Mark file as already downloaded
        mock_download_database.mark_downloaded(
            file_path=sample_download_task['path'],
            url=sample_download_task['url'],
            course_name=sample_download_task['course_name'],
            lesson_name=sample_download_task['lesson_name'],
            file_type=sample_download_task['file_type']
        )

        result = download_file_task(sample_download_task, mock_download_database)

        assert "Já indexado" in result or "pulado" in result

    @pytest.mark.unit
    def test_download_file_exists(self, sample_download_task, temp_dir, mock_download_index):
        """Test skipping when file already exists on disk."""
        # Create the file
        sample_download_task['path'] = os.path.join(temp_dir, "test.mp4")
        Path(sample_download_task['path']).touch()

        result = download_file_task(sample_download_task, mock_download_index)

        assert "Já existe" in result or "pulado" in result

    @pytest.mark.unit
    @patch('main.SESSION')
    def test_download_success(self, mock_session, sample_download_task, temp_dir, mock_download_index):
        """Test successful file download."""
        sample_download_task['path'] = os.path.join(temp_dir, "test.mp4")

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1024'}
        mock_response.iter_content = Mock(return_value=[b'test' * 256])
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        result = download_file_task(sample_download_task, mock_download_index)

        assert "Baixado" in result or "✓" in result

    @pytest.mark.unit
    @patch('main.SESSION')
    def test_download_resume_partial(self, mock_session, sample_download_task, temp_dir, mock_download_index):
        """Test resuming partial download."""
        sample_download_task['path'] = os.path.join(temp_dir, "test.mp4")
        temp_path = sample_download_task['path'] + ".part"

        # Create partial file
        with open(temp_path, 'wb') as f:
            f.write(b'partial')

        # Mock 206 Partial Content response
        mock_response = MagicMock()
        mock_response.status_code = 206
        mock_response.headers = {'content-length': '1024'}
        mock_response.iter_content = Mock(return_value=[b'rest'])
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        result = download_file_task(sample_download_task, mock_download_index)

        # Verify Range header was sent
        call_args = mock_session.get.call_args
        if call_args:
            headers = call_args[1].get('headers', {})
            assert 'Range' in headers

    @pytest.mark.unit
    @patch('main.SESSION')
    def test_download_http_error(self, mock_session, sample_download_task, temp_dir, mock_download_index):
        """Test handling of HTTP errors."""
        sample_download_task['path'] = os.path.join(temp_dir, "test.mp4")

        # Mock HTTP error
        import requests
        mock_session.get.side_effect = requests.exceptions.HTTPError("404 Not Found")

        result = download_file_task(sample_download_task, mock_download_index)

        assert "Falha" in result or "ERRO" in result


class TestProcessDownloadQueue:
    """Test download queue processing."""

    @pytest.mark.unit
    def test_empty_queue(self, temp_dir):
        """Test processing empty queue."""
        # Should handle gracefully
        process_download_queue([], temp_dir)
        # No exception means success

    @pytest.mark.unit
    def test_all_files_completed(self, temp_dir, mock_download_index):
        """Test queue with all files already completed."""
        queue = [
            {
                'url': 'https://example.com/1.mp4',
                'path': os.path.join(temp_dir, '1.mp4'),
                'filename': '1.mp4',
                'course_name': 'Test',
                'lesson_name': 'Lesson 1',
                'file_type': 'video'
            }
        ]

        # Mark as completed
        mock_download_index.mark_completed(queue[0]['path'])

        # Create the file
        Path(queue[0]['path']).touch()

        # Should skip all
        process_download_queue(queue, temp_dir, use_sqlite=False)


class TestCompressCourseVideos:
    """Test automatic video compression after course download."""

    @pytest.mark.unit
    @patch('main.check_ffmpeg')
    def test_ffmpeg_not_available(self, mock_check_ffmpeg, temp_dir):
        """Test graceful handling when FFmpeg is not available."""
        from main import compress_course_videos

        mock_check_ffmpeg.return_value = False

        # Should not raise exception
        compress_course_videos(temp_dir, "Test Course")

    @pytest.mark.unit
    @patch('main.check_ffmpeg')
    @patch('main.find_videos')
    def test_no_videos_to_compress(self, mock_find_videos, mock_check_ffmpeg, temp_dir):
        """Test when no videos are found."""
        from main import compress_course_videos

        mock_check_ffmpeg.return_value = True
        mock_find_videos.return_value = []

        # Should handle gracefully
        compress_course_videos(temp_dir, "Test Course")

    @pytest.mark.unit
    @patch('main.check_ffmpeg')
    @patch('main.find_videos')
    @patch('main.compress_video_task')
    def test_compression_execution(self, mock_compress_task, mock_find_videos, mock_check_ffmpeg, temp_dir):
        """Test that compression is executed for found videos."""
        from main import compress_course_videos

        mock_check_ffmpeg.return_value = True
        mock_find_videos.return_value = [Path(temp_dir) / "video.mp4"]
        mock_compress_task.return_value = (True, "Compressed", 1000, 500)

        compress_course_videos(temp_dir, "Test Course")

        # Verify compress_video_task was called
        assert mock_compress_task.call_count >= 1


class TestSanitizeEdgeCases:
    """Additional edge case tests for sanitize_filename."""

    @pytest.mark.unit
    def test_very_long_filename(self):
        """Test handling of very long filenames."""
        long_name = "A" * 500
        result = sanitize_filename(long_name)
        assert len(result) > 0

    @pytest.mark.unit
    def test_mixed_special_and_normal(self):
        """Test mixed special and normal characters."""
        result = sanitize_filename("Video-Aula: Parte 1 (Completo)")
        assert result != ""
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result

    @pytest.mark.unit
    def test_consecutive_dots_and_commas(self):
        """Test handling of consecutive dots and commas."""
        result = sanitize_filename("test...file,,,name")
        assert '.' not in result
        assert ',' not in result

    @pytest.mark.unit
    def test_path_separator_removal(self):
        """Test that path separators are removed."""
        result = sanitize_filename("../../etc/passwd")
        assert '/' not in result
        assert '\\' not in result
