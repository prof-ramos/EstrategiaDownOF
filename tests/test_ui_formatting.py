"""Tests for ui.py - UI formatting and display."""
import pytest
from unittest.mock import patch

import ui
from colorama import Fore, Style


class TestBasicFormatting:
    """Test basic UI formatting functions."""

    @pytest.mark.unit
    def test_get_terminal_width(self):
        """Test terminal width detection."""
        width = ui.get_terminal_width()
        assert isinstance(width, int)
        assert width > 0

    @pytest.mark.unit
    @patch('shutil.get_terminal_size')
    def test_get_terminal_width_fallback(self, mock_get_size):
        """Test fallback when terminal size cannot be determined."""
        mock_get_size.side_effect = Exception("No terminal")

        width = ui.get_terminal_width()

        assert width == 80  # Default fallback

    @pytest.mark.unit
    def test_header_basic(self):
        """Test header creation."""
        result = ui.header("Test Header", width=50)

        assert "Test Header" in result
        assert "╭" in result
        assert "╰" in result

    @pytest.mark.unit
    def test_subheader(self):
        """Test subheader creation."""
        result = ui.subheader("Test Subheader")

        assert "Test Subheader" in result
        assert "▸" in result

    @pytest.mark.unit
    def test_subheader_custom_icon(self):
        """Test subheader with custom icon."""
        result = ui.subheader("Test", icon="★")

        assert "★" in result
        assert "Test" in result


class TestPanel:
    """Test panel creation."""

    @pytest.mark.unit
    def test_panel_basic(self):
        """Test basic panel creation."""
        lines = ["Line 1", "Line 2", "Line 3"]
        result = ui.panel("Test Panel", lines, width=60)

        assert "Test Panel" in result
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
        assert "┌" in result
        assert "└" in result

    @pytest.mark.unit
    def test_panel_empty_lines(self):
        """Test panel with empty lines."""
        lines = ["Line 1", "", "Line 2"]
        result = ui.panel("Test", lines, width=60)

        assert "Line 1" in result
        assert "Line 2" in result

    @pytest.mark.unit
    def test_panel_custom_border_color(self):
        """Test panel with custom border color."""
        lines = ["Test"]
        result = ui.panel("Test", lines, width=60, border_color=Fore.RED)

        assert Fore.RED in result


class TestStatusLine:
    """Test status line creation."""

    @pytest.mark.unit
    def test_status_line_success(self):
        """Test success status line."""
        result = ui.status_line("Test", "Value", status="success")

        assert "Test" in result
        assert "Value" in result
        assert "✓" in result

    @pytest.mark.unit
    def test_status_line_error(self):
        """Test error status line."""
        result = ui.status_line("Error", "Message", status="error")

        assert "Error" in result
        assert "Message" in result
        assert "✗" in result

    @pytest.mark.unit
    def test_status_line_warning(self):
        """Test warning status line."""
        result = ui.status_line("Warning", "Text", status="warning")

        assert "Warning" in result
        assert "⚠" in result

    @pytest.mark.unit
    def test_status_line_info(self):
        """Test info status line."""
        result = ui.status_line("Info", "Data", status="info")

        assert "Info" in result
        assert "●" in result

    @pytest.mark.unit
    def test_status_line_custom_icon(self):
        """Test status line with custom icon."""
        result = ui.status_line("Custom", "Value", status="neutral", icon="🎯")

        assert "🎯" in result


class TestDivider:
    """Test divider creation."""

    @pytest.mark.unit
    def test_divider_default(self):
        """Test default divider."""
        result = ui.divider(width=50)

        assert len(result) > 0
        assert "─" in result

    @pytest.mark.unit
    def test_divider_custom_char(self):
        """Test divider with custom character."""
        result = ui.divider(char="=", width=50)

        assert "=" in result


class TestBanners:
    """Test banner displays."""

    @pytest.mark.unit
    def test_banner(self):
        """Test main banner."""
        result = ui.banner()

        assert "ESTRATÉGIA" in result or "ESTRAT" in result
        assert "DOWNLOADER" in result
        assert "v 2.0" in result or "v2.0" in result

    @pytest.mark.unit
    def test_simple_banner(self):
        """Test simple banner."""
        result = ui.simple_banner()

        assert "DOWNLOADER" in result
        assert "v2.0" in result or "v 2.0" in result
        assert "║" in result or "│" in result

    @pytest.mark.unit
    def test_goodbye(self):
        """Test goodbye message."""
        result = ui.goodbye()

        assert "Concluído" in result or "concluído" in result
        assert "Obrigado" in result or "obrigado" in result


class TestConfigPanel:
    """Test configuration panel."""

    @pytest.mark.unit
    def test_config_panel(self):
        """Test config panel creation."""
        result = ui.config_panel("Async", 8, "/path/to/downloads")

        assert "Async" in result
        assert "8" in result
        assert "downloads" in result or "/path" in result
        assert "4x" in result  # Retry count
        assert "backoff" in result

    @pytest.mark.unit
    def test_config_panel_long_path(self):
        """Test config panel with very long path."""
        long_path = "/very/long/path/" * 20
        result = ui.config_panel("Sync", 4, long_path)

        # Should truncate long path
        assert len(result) < len(long_path) * 2


class TestCourseHeader:
    """Test course header display."""

    @pytest.mark.unit
    def test_course_header(self):
        """Test course header creation."""
        result = ui.course_header(1, 5, "Direito Constitucional")

        assert "1/5" in result
        assert "Direito" in result
        assert "█" in result or "░" in result  # Progress bar

    @pytest.mark.unit
    def test_course_header_progress(self):
        """Test course header shows correct progress."""
        result = ui.course_header(3, 10, "Test Course")

        assert "3/10" in result
        assert "30%" in result

    @pytest.mark.unit
    def test_course_header_long_name(self):
        """Test course header with very long course name."""
        long_name = "A" * 200
        result = ui.course_header(1, 1, long_name)

        # Should truncate
        assert len(result) < len(long_name) * 2


class TestLessonHeader:
    """Test lesson header display."""

    @pytest.mark.unit
    def test_lesson_header(self):
        """Test lesson header creation."""
        result = ui.lesson_header(5, 20, "Introdução ao Direito")

        assert "05/20" in result
        assert "Introdução" in result
        assert "▸" in result


class TestDownloadSummary:
    """Test download summary panel."""

    @pytest.mark.unit
    def test_download_summary_success(self):
        """Test summary with no failures."""
        result = ui.download_summary(
            total=100,
            completed=95,
            skipped=5,
            failed=0,
            elapsed_time="00:15:30"
        )

        assert "100" in result
        assert "95" in result
        assert "5" in result
        assert "0" in result
        assert "15:30" in result

    @pytest.mark.unit
    def test_download_summary_with_failures(self):
        """Test summary with failures."""
        result = ui.download_summary(
            total=50,
            completed=40,
            skipped=5,
            failed=5,
            elapsed_time="00:10:00"
        )

        assert "50" in result
        assert "5" in result  # Failed count


class TestLoginPrompt:
    """Test login prompt."""

    @pytest.mark.unit
    def test_login_prompt(self):
        """Test login prompt creation."""
        result = ui.login_prompt(60)

        assert "60 segundos" in result or "60" in result
        assert "LOGIN" in result or "login" in result
        assert "cookies" in result or "Cookies" in result


class TestSessionRestored:
    """Test session restored message."""

    @pytest.mark.unit
    def test_session_restored(self):
        """Test session restored message."""
        result = ui.session_restored()

        assert "Sessão" in result or "sessão" in result
        assert "restaurada" in result
        assert "✓" in result


class TestRetryIndicator:
    """Test retry indicator."""

    @pytest.mark.unit
    def test_retry_indicator(self):
        """Test retry indicator creation."""
        result = ui.retry_indicator(2, 4, "test.mp4")

        assert "2/4" in result
        assert "test.mp4" in result
        assert "Tentativa" in result or "tentativa" in result


class TestProgressBarFormat:
    """Test progress bar configuration."""

    @pytest.mark.unit
    def test_progress_bar_format(self):
        """Test progress bar format configuration."""
        config = ui.progress_bar_format()

        assert 'bar_format' in config
        assert 'colour' in config
        assert 'ncols' in config
        assert config['colour'] == 'cyan'


class TestFileStatus:
    """Test file status formatting."""

    @pytest.mark.unit
    def test_file_status_downloaded(self):
        """Test downloaded file status."""
        result = ui.file_status("test.mp4", 124.5, "downloaded")

        assert "test.mp4" in result
        assert "124.5" in result
        assert "✓" in result

    @pytest.mark.unit
    def test_file_status_skipped(self):
        """Test skipped file status."""
        result = ui.file_status("test.pdf", 2.3, "skipped")

        assert "test.pdf" in result
        assert "2.3" in result
        assert "○" in result

    @pytest.mark.unit
    def test_file_status_failed(self):
        """Test failed file status."""
        result = ui.file_status("test.mp4", 0, "failed")

        assert "test.mp4" in result
        assert "✗" in result

    @pytest.mark.unit
    def test_file_status_long_filename(self):
        """Test file status with very long filename."""
        long_name = "very_long_filename_" * 10 + ".mp4"
        result = ui.file_status(long_name, 10.0, "downloaded")

        # Should truncate
        assert "..." in result


class TestUIEdgeCases:
    """Test UI edge cases."""

    @pytest.mark.unit
    def test_empty_strings(self):
        """Test handling of empty strings."""
        result = ui.subheader("")
        assert result is not None

    @pytest.mark.unit
    def test_special_characters(self):
        """Test handling of special characters."""
        result = ui.status_line("Test", "Value with <>&", status="info")
        assert "Value with <>&" in result

    @pytest.mark.unit
    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        result = ui.course_header(1, 1, "Português Avançado - Acentuação")
        assert "Português" in result or "Portugu" in result
