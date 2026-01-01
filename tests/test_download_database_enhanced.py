"""Enhanced tests for download_database.py - Additional coverage."""
import os
import tempfile
import shutil
import json
from pathlib import Path
import pytest

from download_database import DownloadDatabase


class TestDownloadDatabaseExportImport:
    """Test export/import functionality."""

    @pytest.mark.unit
    def test_export_to_json(self):
        """Test exporting database to JSON."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Add some data
            test_file = os.path.join(tmpdir, "test.mp4")
            Path(test_file).touch()

            db.mark_downloaded(
                file_path=test_file,
                url="https://example.com/test.mp4",
                course_name="Test Course",
                lesson_name="Test Lesson",
                file_type="video",
                size_bytes=1024
            )

            # Export
            export_path = db.export_to_json()

            assert os.path.exists(export_path)

            # Verify JSON structure
            with open(export_path, 'r') as f:
                data = json.load(f)

            assert 'version' in data
            assert 'downloads' in data
            assert 'statistics' in data
            assert len(data['downloads']) == 1

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_export_with_custom_path(self):
        """Test exporting to custom path."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            custom_path = os.path.join(tmpdir, "custom_export.json")
            export_path = db.export_to_json(custom_path)

            assert export_path == custom_path
            assert os.path.exists(custom_path)

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_export_empty_database(self):
        """Test exporting empty database."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            export_path = db.export_to_json()

            assert os.path.exists(export_path)

            with open(export_path, 'r') as f:
                data = json.load(f)

            assert data['downloads'] == []

        finally:
            shutil.rmtree(tmpdir)


class TestDownloadDatabaseContextManager:
    """Test context manager protocol."""

    @pytest.mark.unit
    def test_context_manager_basic(self):
        """Test using DownloadDatabase as context manager."""
        tmpdir = tempfile.mkdtemp()
        try:
            with DownloadDatabase(tmpdir, use_sqlite=True) as db:
                assert db is not None
                assert hasattr(db, 'mark_downloaded')

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_context_manager_updates_sync_time(self):
        """Test that __exit__ updates sync time."""
        tmpdir = tempfile.mkdtemp()
        try:
            with DownloadDatabase(tmpdir, use_sqlite=True) as db:
                test_file = os.path.join(tmpdir, "test.mp4")
                Path(test_file).touch()

                db.mark_downloaded(
                    file_path=test_file,
                    url="https://example.com/test.mp4",
                    course_name="Test",
                    lesson_name="Test",
                    file_type="video"
                )

            # Verify sync was called (last_sync_at should be set)
            db2 = DownloadDatabase(tmpdir, use_sqlite=True)
            stats = db2.get_statistics()
            assert stats.get('last_sync_at') is not None

        finally:
            shutil.rmtree(tmpdir)


class TestDownloadDatabaseQueries:
    """Test query functionality."""

    @pytest.mark.unit
    def test_get_downloads_by_course_empty(self):
        """Test querying non-existent course."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            downloads = db.get_downloads_by_course("NonExistent Course")

            assert downloads == []

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_get_downloads_by_course_multiple(self):
        """Test querying course with multiple downloads."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Add multiple files for same course
            for i in range(5):
                test_file = os.path.join(tmpdir, f"test{i}.mp4")
                Path(test_file).touch()

                db.mark_downloaded(
                    file_path=test_file,
                    url=f"https://example.com/test{i}.mp4",
                    course_name="Test Course",
                    lesson_name=f"Lesson {i}",
                    file_type="video"
                )

            downloads = db.get_downloads_by_course("Test Course")

            assert len(downloads) == 5
            assert all(d['file_type'] == 'video' for d in downloads)

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_get_downloads_by_course_sorting(self):
        """Test that downloads are sorted by lesson and filename."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Add files in random order
            files_data = [
                ("file_c.pdf", "Lesson B", "pdf"),
                ("file_a.mp4", "Lesson A", "video"),
                ("file_b.pdf", "Lesson A", "pdf"),
            ]

            for filename, lesson, ftype in files_data:
                test_file = os.path.join(tmpdir, filename)
                Path(test_file).touch()

                db.mark_downloaded(
                    file_path=test_file,
                    url=f"https://example.com/{filename}",
                    course_name="Test Course",
                    lesson_name=lesson,
                    file_type=ftype
                )

            downloads = db.get_downloads_by_course("Test Course")

            # Should be sorted by lesson_name, then file_name
            assert downloads[0]['lesson_name'] == "Lesson A"
            assert downloads[1]['lesson_name'] == "Lesson A"
            assert downloads[2]['lesson_name'] == "Lesson B"

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_get_unverified_files(self):
        """Test getting list of unverified files."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Add file without hash
            test_file = os.path.join(tmpdir, "test.mp4")
            Path(test_file).touch()

            db.mark_downloaded(
                file_path=test_file,
                url="https://example.com/test.mp4",
                course_name="Test",
                lesson_name="Test",
                file_type="video",
                calculate_hash=False
            )

            unverified = db.get_unverified_files()

            assert len(unverified) == 1
            assert test_file in unverified

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_get_unverified_files_empty(self):
        """Test getting unverified files when all are verified."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Add file with hash
            test_file = os.path.join(tmpdir, "test.mp4")
            with open(test_file, 'wb') as f:
                f.write(b'test content')

            db.mark_downloaded(
                file_path=test_file,
                url="https://example.com/test.mp4",
                course_name="Test",
                lesson_name="Test",
                file_type="video",
                calculate_hash=True
            )

            unverified = db.get_unverified_files()

            assert len(unverified) == 0

        finally:
            shutil.rmtree(tmpdir)


class TestDownloadDatabaseEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.unit
    def test_special_characters_in_paths(self):
        """Test handling of special characters in file paths."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            special_chars_path = os.path.join(tmpdir, "test'with\"quotes.mp4")
            Path(special_chars_path).touch()

            # Should not raise exception
            db.mark_downloaded(
                file_path=special_chars_path,
                url="https://example.com/test.mp4",
                course_name="Test",
                lesson_name="Test",
                file_type="video"
            )

            assert db.is_downloaded(special_chars_path)

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_unicode_in_course_names(self):
        """Test handling of unicode characters in course names."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            test_file = os.path.join(tmpdir, "test.mp4")
            Path(test_file).touch()

            db.mark_downloaded(
                file_path=test_file,
                url="https://example.com/test.mp4",
                course_name="Português Avançado - Acentuação",
                lesson_name="Introdução",
                file_type="video"
            )

            downloads = db.get_downloads_by_course("Português Avançado - Acentuação")
            assert len(downloads) == 1

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_very_long_paths(self):
        """Test handling of very long file paths."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Create a very long path
            long_path = os.path.join(tmpdir, "a" * 200 + ".mp4")

            # May fail on some filesystems, but should not crash
            try:
                Path(long_path).touch()
                db.mark_downloaded(
                    file_path=long_path,
                    url="https://example.com/test.mp4",
                    course_name="Test",
                    lesson_name="Test",
                    file_type="video"
                )
            except (OSError, IOError):
                # OS limitation, not a database error
                pass

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_duplicate_marking(self):
        """Test marking the same file multiple times."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            test_file = os.path.join(tmpdir, "test.mp4")
            Path(test_file).touch()

            # Mark same file twice
            for _ in range(3):
                db.mark_downloaded(
                    file_path=test_file,
                    url="https://example.com/test.mp4",
                    course_name="Test",
                    lesson_name="Test",
                    file_type="video"
                )

            # Should only count once in statistics
            stats = db.get_statistics()
            assert stats.get('total_files') == 1

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_missing_file_verification(self):
        """Test verification of missing file."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Mark file without creating it
            test_file = os.path.join(tmpdir, "missing.mp4")

            db.mark_downloaded(
                file_path=test_file,
                url="https://example.com/test.mp4",
                course_name="Test",
                lesson_name="Test",
                file_type="video"
            )

            # Try to verify
            is_valid, message = db.verify_file_integrity(test_file)

            assert is_valid is False
            assert "não existe" in message.lower() or "not exist" in message.lower()

        finally:
            shutil.rmtree(tmpdir)


class TestDownloadDatabaseStatistics:
    """Test statistics tracking."""

    @pytest.mark.unit
    def test_statistics_by_file_type(self):
        """Test statistics breakdown by file type."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Add different file types
            file_types = [
                ('video1.mp4', 'video'),
                ('video2.mp4', 'video'),
                ('doc1.pdf', 'pdf'),
                ('doc2.pdf', 'pdf'),
                ('doc3.pdf', 'pdf'),
                ('slide1.pdf', 'material'),
            ]

            for filename, ftype in file_types:
                test_file = os.path.join(tmpdir, filename)
                Path(test_file).touch()

                db.mark_downloaded(
                    file_path=test_file,
                    url=f"https://example.com/{filename}",
                    course_name="Test",
                    lesson_name="Test",
                    file_type=ftype
                )

            stats = db.get_statistics()

            assert stats.get('total_videos') == 2
            assert stats.get('total_pdfs') == 3
            assert stats.get('total_materials') == 1
            assert stats.get('total_files') == 6

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_statistics_by_course(self):
        """Test statistics grouped by course."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=True)

            # Add files for different courses
            courses_data = [
                ('Course A', 5),
                ('Course B', 3),
                ('Course C', 7),
            ]

            for course, count in courses_data:
                for i in range(count):
                    test_file = os.path.join(tmpdir, f"{course}_{i}.mp4")
                    Path(test_file).touch()

                    db.mark_downloaded(
                        file_path=test_file,
                        url=f"https://example.com/{course}_{i}.mp4",
                        course_name=course,
                        lesson_name=f"Lesson {i}",
                        file_type="video"
                    )

            stats = db.get_statistics()

            assert 'by_course' in stats
            assert len(stats['by_course']) == 3

            # Find Course C stats
            course_c_stats = next(c for c in stats['by_course'] if c['course'] == 'Course C')
            assert course_c_stats['files'] == 7

        finally:
            shutil.rmtree(tmpdir)


class TestDownloadDatabaseJSONFallback:
    """Test JSON fallback mode."""

    @pytest.mark.unit
    def test_json_mode_basic(self):
        """Test basic operations in JSON mode."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=False)

            test_file = os.path.join(tmpdir, "test.mp4")
            Path(test_file).touch()

            # Should work but with limited features
            db.mark_downloaded(
                file_path=test_file,
                url="https://example.com/test.mp4",
                course_name="Test",
                lesson_name="Test",
                file_type="video"
            )

            assert db.is_downloaded(test_file)

            # Statistics should be limited
            stats = db.get_statistics()
            assert stats.get('mode') == 'json'
            assert stats.get('total_files') == 1

        finally:
            shutil.rmtree(tmpdir)

    @pytest.mark.unit
    def test_json_mode_no_advanced_features(self):
        """Test that advanced features return empty/error in JSON mode."""
        tmpdir = tempfile.mkdtemp()
        try:
            db = DownloadDatabase(tmpdir, use_sqlite=False)

            # get_downloads_by_course should return empty
            downloads = db.get_downloads_by_course("Test")
            assert downloads == []

            # get_unverified_files should return empty
            unverified = db.get_unverified_files()
            assert unverified == []

            # verify_file_integrity should fail gracefully
            is_valid, message = db.verify_file_integrity("/tmp/test.mp4")
            assert is_valid is False

        finally:
            shutil.rmtree(tmpdir)
