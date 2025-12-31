"""Enhanced tests for compress_videos.py - Additional coverage."""
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

import pytest

from compress_videos import (
    check_ffmpeg,
    get_video_info,
    find_videos,
    get_output_path,
    compress_video,
    compress_video_task,
    format_size,
    QUALITY_PRESETS,
    COMPRESSED_SUFFIX
)


class TestGetVideoInfo:
    """Test video information extraction."""

    @pytest.mark.unit
    @pytest.mark.requires_ffmpeg
    @patch('subprocess.run')
    def test_get_video_info_success(self, mock_run):
        """Test successful video info extraction."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"format": {"filename": "test.mp4"}}'
        )

        result = get_video_info(Path("/tmp/test.mp4"))

        assert result is not None
        assert 'format' in result

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_video_info_failure(self, mock_run):
        """Test handling of ffprobe failure."""
        mock_run.return_value = Mock(returncode=1, stdout='')

        result = get_video_info(Path("/tmp/test.mp4"))

        assert result is None

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_video_info_timeout(self, mock_run):
        """Test handling of ffprobe timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('ffprobe', 30)

        result = get_video_info(Path("/tmp/test.mp4"))

        assert result is None

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_video_info_not_found(self, mock_run):
        """Test handling when ffprobe is not installed."""
        mock_run.side_effect = FileNotFoundError()

        result = get_video_info(Path("/tmp/test.mp4"))

        assert result is None


class TestFindVideosEnhanced:
    """Enhanced tests for video discovery."""

    @pytest.mark.unit
    def test_find_videos_nested_directories(self):
        """Test finding videos in deeply nested directories."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Create nested structure
            nested_path = Path(tmpdir) / "a" / "b" / "c" / "d"
            nested_path.mkdir(parents=True, exist_ok=True)

            # Create video in deep directory
            (nested_path / "video.mp4").touch()

            videos = find_videos(Path(tmpdir))

            assert len(videos) == 1
            assert videos[0].name == "video.mp4"

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_find_videos_include_compressed(self):
        """Test finding videos including compressed ones."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Create both regular and compressed videos
            (Path(tmpdir) / "regular.mp4").touch()
            (Path(tmpdir) / f"compressed{COMPRESSED_SUFFIX}.mp4").touch()

            videos_without = find_videos(Path(tmpdir), include_compressed=False)
            videos_with = find_videos(Path(tmpdir), include_compressed=True)

            assert len(videos_without) == 1
            assert len(videos_with) == 2

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_find_videos_mixed_extensions(self):
        """Test that only .mp4 files are found."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Create files with different extensions
            (Path(tmpdir) / "video.mp4").touch()
            (Path(tmpdir) / "video.mkv").touch()
            (Path(tmpdir) / "video.avi").touch()
            (Path(tmpdir) / "document.pdf").touch()

            videos = find_videos(Path(tmpdir))

            # Should only find .mp4
            assert len(videos) == 1
            assert videos[0].suffix == ".mp4"

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_find_videos_empty_directory(self):
        """Test finding videos in empty directory."""
        tmpdir = tempfile.mkdtemp()
        try:
            videos = find_videos(Path(tmpdir))
            assert videos == []

        finally:
            shutil.rmtree(tmpdir)


class TestGetOutputPath:
    """Test output path generation."""

    @pytest.mark.unit
    def test_output_path_delete_true(self):
        """Test output path when delete_original=True."""
        input_path = Path("/path/to/video.mp4")
        output = get_output_path(input_path, delete_original=True)

        assert output == Path("/path/to/video.mp4.temp")

    @pytest.mark.unit
    def test_output_path_delete_false(self):
        """Test output path when delete_original=False."""
        input_path = Path("/path/to/video.mp4")
        output = get_output_path(input_path, delete_original=False)

        assert COMPRESSED_SUFFIX in str(output)
        assert output.suffix == ".mp4"

    @pytest.mark.unit
    def test_output_path_preserves_directory(self):
        """Test that output path preserves directory structure."""
        input_path = Path("/path/to/nested/dir/video.mp4")
        output = get_output_path(input_path, delete_original=False)

        assert output.parent == input_path.parent


class TestCompressVideo:
    """Test actual video compression function."""

    @pytest.mark.unit
    def test_compress_video_dry_run(self, sample_video_file):
        """Test dry run mode."""
        output_path = sample_video_file.with_suffix('.mp4.temp')

        success, message, orig_size, comp_size = compress_video(
            sample_video_file,
            output_path,
            codec='h265',
            quality='balanced',
            dry_run=True
        )

        assert success is True
        assert "[DRY-RUN]" in message
        assert orig_size > 0
        assert comp_size == 0

    @pytest.mark.unit
    @pytest.mark.requires_ffmpeg
    @patch('subprocess.run')
    def test_compress_video_success(self, mock_run, sample_video_file):
        """Test successful compression."""
        output_path = sample_video_file.with_suffix('.mp4.temp')

        # Mock successful FFmpeg execution
        mock_run.return_value = Mock(returncode=0, stderr='')

        # Create output file to simulate FFmpeg output
        output_path.write_bytes(b'\x00' * 512)  # Smaller compressed file

        success, message, orig_size, comp_size = compress_video(
            sample_video_file,
            output_path,
            codec='h265',
            quality='balanced',
            dry_run=False
        )

        assert success is True
        assert "Compressed" in message
        assert orig_size > 0
        assert comp_size > 0

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_compress_video_ffmpeg_error(self, mock_run, sample_video_file):
        """Test handling of FFmpeg errors."""
        output_path = sample_video_file.with_suffix('.mp4.temp')

        # Mock FFmpeg failure
        mock_run.return_value = Mock(returncode=1, stderr='Error: invalid codec')

        success, message, orig_size, comp_size = compress_video(
            sample_video_file,
            output_path,
            codec='h265',
            quality='balanced',
            dry_run=False
        )

        assert success is False
        assert "FFmpeg error" in message

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_compress_video_timeout(self, mock_run, sample_video_file):
        """Test handling of FFmpeg timeout."""
        output_path = sample_video_file.with_suffix('.mp4.temp')

        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired('ffmpeg', 3600)

        success, message, orig_size, comp_size = compress_video(
            sample_video_file,
            output_path,
            codec='h265',
            quality='balanced',
            dry_run=False
        )

        assert success is False
        assert "Timeout" in message

    @pytest.mark.unit
    @pytest.mark.requires_ffmpeg
    @patch('subprocess.run')
    def test_compress_video_h264_codec(self, mock_run, sample_video_file):
        """Test compression with H.264 codec."""
        output_path = sample_video_file.with_suffix('.mp4.temp')

        mock_run.return_value = Mock(returncode=0, stderr='')
        output_path.write_bytes(b'\x00' * 512)

        success, message, orig_size, comp_size = compress_video(
            sample_video_file,
            output_path,
            codec='h264',
            quality='balanced',
            dry_run=False
        )

        # Verify h264 codec was used in command
        call_args = mock_run.call_args[0][0]
        assert 'libx264' in call_args

    @pytest.mark.unit
    @pytest.mark.requires_ffmpeg
    @patch('subprocess.run')
    def test_compress_video_quality_presets(self, mock_run, sample_video_file):
        """Test different quality presets."""
        output_path = sample_video_file.with_suffix('.mp4.temp')

        for quality in ['high', 'balanced', 'small']:
            mock_run.return_value = Mock(returncode=0, stderr='')
            output_path.write_bytes(b'\x00' * 512)

            success, message, orig_size, comp_size = compress_video(
                sample_video_file,
                output_path,
                codec='h265',
                quality=quality,
                dry_run=False
            )

            # Should verify CRF value is correct
            call_args = mock_run.call_args[0][0]
            expected_crf = QUALITY_PRESETS[quality]


class TestCompressVideoTask:
    """Test video compression task wrapper."""

    @pytest.mark.unit
    @patch('compress_videos.compress_video')
    def test_compress_video_task_no_delete(self, mock_compress, sample_video_file):
        """Test task without deleting original."""
        mock_compress.return_value = (True, "Compressed", 1024, 512)

        success, message, orig_size, comp_size = compress_video_task(
            sample_video_file,
            codec='h265',
            quality='balanced',
            delete_original=False,
            dry_run=False
        )

        assert success is True
        assert orig_size == 1024
        assert comp_size == 512

        # Original should still exist
        assert sample_video_file.exists()

    @pytest.mark.unit
    @patch('compress_videos.compress_video')
    def test_compress_video_task_with_delete(self, mock_compress, sample_video_file):
        """Test task with deleting original."""
        output_path = sample_video_file.with_suffix('.mp4.temp')
        output_path.write_bytes(b'\x00' * 512)

        mock_compress.return_value = (True, "Compressed", 1024, 512)

        success, message, orig_size, comp_size = compress_video_task(
            sample_video_file,
            codec='h265',
            quality='balanced',
            delete_original=True,
            dry_run=False
        )

        assert success is True

        # Temp file should be renamed to original
        assert sample_video_file.exists()
        assert not output_path.exists()

    @pytest.mark.unit
    @patch('compress_videos.compress_video')
    def test_compress_video_task_replace_error(self, mock_compress, sample_video_file):
        """Test handling of file replacement error."""
        # Don't create output file, so replace will fail
        mock_compress.return_value = (True, "Compressed", 1024, 512)

        success, message, orig_size, comp_size = compress_video_task(
            sample_video_file,
            codec='h265',
            quality='balanced',
            delete_original=True,
            dry_run=False
        )

        # Should fail gracefully
        assert success is False
        assert "Error replacing" in message


class TestFormatSizeEnhanced:
    """Enhanced tests for size formatting."""

    @pytest.mark.unit
    def test_format_size_zero(self):
        """Test formatting zero bytes."""
        result = format_size(0)
        assert "0.0 B" in result

    @pytest.mark.unit
    def test_format_size_bytes(self):
        """Test formatting bytes."""
        result = format_size(512)
        assert "512.0 B" in result

    @pytest.mark.unit
    def test_format_size_kilobytes(self):
        """Test formatting kilobytes."""
        result = format_size(2048)
        assert "2.0 KB" in result

    @pytest.mark.unit
    def test_format_size_megabytes(self):
        """Test formatting megabytes."""
        result = format_size(5 * 1024 * 1024)
        assert "5.0 MB" in result

    @pytest.mark.unit
    def test_format_size_gigabytes(self):
        """Test formatting gigabytes."""
        result = format_size(3 * 1024 * 1024 * 1024)
        assert "3.0 GB" in result

    @pytest.mark.unit
    def test_format_size_terabytes(self):
        """Test formatting terabytes."""
        result = format_size(2 * 1024 * 1024 * 1024 * 1024)
        assert "2.0 TB" in result

    @pytest.mark.unit
    def test_format_size_fractional(self):
        """Test formatting fractional values."""
        result = format_size(1536)  # 1.5 KB
        assert "1.5 KB" in result


class TestCompressionEdgeCases:
    """Test edge cases in compression."""

    @pytest.mark.unit
    def test_compress_nonexistent_file(self):
        """Test compressing nonexistent file."""
        input_path = Path("/nonexistent/video.mp4")
        output_path = Path("/nonexistent/video_compressed.mp4")

        # Should handle gracefully without crashing
        try:
            success, message, orig_size, comp_size = compress_video(
                input_path,
                output_path,
                codec='h265',
                quality='balanced',
                dry_run=False
            )
            # If it doesn't raise, it should return failure
            assert success is False
        except (FileNotFoundError, OSError):
            # Expected exception
            pass

    @pytest.mark.unit
    def test_find_videos_with_symlinks(self):
        """Test finding videos with symlinks."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Create video
            video_path = Path(tmpdir) / "video.mp4"
            video_path.touch()

            # Create symlink
            symlink_path = Path(tmpdir) / "link.mp4"
            try:
                symlink_path.symlink_to(video_path)

                videos = find_videos(Path(tmpdir))

                # Should find both or deduplicate
                assert len(videos) >= 1

            except (OSError, NotImplementedError):
                # Symlinks may not be supported on all systems
                pass

        finally:
            shutil.rmtree(tmpdir)
