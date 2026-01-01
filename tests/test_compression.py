"""Tests for the video compression module."""
import os
import sys
import tempfile
from pathlib import Path


def test_ffmpeg_check():
    """Test FFmpeg availability check."""
    print("Testing FFmpeg availability check...")

    from compress_videos import check_ffmpeg

    result = check_ffmpeg()
    if result:
        print("  ✓ FFmpeg is available")
    else:
        print("  ⚠ FFmpeg not found (install with: brew install ffmpeg)")

    return True  # Pass regardless, just informational


def test_quality_presets():
    """Test quality presets are defined correctly."""
    print("Testing quality presets...")

    from compress_videos import QUALITY_PRESETS

    assert 'high' in QUALITY_PRESETS, "Missing 'high' preset"
    assert 'balanced' in QUALITY_PRESETS, "Missing 'balanced' preset"
    assert 'small' in QUALITY_PRESETS, "Missing 'small' preset"

    assert QUALITY_PRESETS['high'] == 18, "high should be CRF 18"
    assert QUALITY_PRESETS['balanced'] == 23, "balanced should be CRF 23"
    assert QUALITY_PRESETS['small'] == 28, "small should be CRF 28"

    print("  ✓ All quality presets defined correctly")
    return True


def test_find_videos():
    """Test video file discovery in a temp directory."""
    print("Testing video file discovery...")

    from compress_videos import find_videos, COMPRESSED_SUFFIX

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test files
        (tmppath / "video1.mp4").touch()
        (tmppath / "video2.mp4").touch()
        (tmppath / f"video3{COMPRESSED_SUFFIX}.mp4").touch()  # Already compressed
        (tmppath / "video4.mp4.part").touch()  # Partial download
        (tmppath / "document.pdf").touch()  # Not a video

        # Create subdirectory with video
        subdir = tmppath / "subdir"
        subdir.mkdir()
        (subdir / "video5.mp4").touch()

        # Find videos (excluding compressed)
        videos = find_videos(tmppath)
        video_names = [v.name for v in videos]

        assert "video1.mp4" in video_names, "Should find video1.mp4"
        assert "video2.mp4" in video_names, "Should find video2.mp4"
        assert f"video3{COMPRESSED_SUFFIX}.mp4" not in video_names, "Should skip compressed"
        assert "video4.mp4.part" not in video_names, "Should skip .part files"
        assert "document.pdf" not in video_names, "Should skip non-mp4"
        assert "video5.mp4" in video_names, "Should find videos in subdirs"

        assert len(videos) == 3, f"Expected 3 videos, found {len(videos)}"

    print("  ✓ Video discovery works correctly")
    return True


def test_output_path_generation():
    """Test output path generation."""
    print("Testing output path generation...")

    from compress_videos import get_output_path, COMPRESSED_SUFFIX

    input_path = Path("/path/to/video.mp4")

    # Without delete
    output = get_output_path(input_path, delete_original=False)
    expected = Path(f"/path/to/video{COMPRESSED_SUFFIX}.mp4")
    assert output == expected, f"Expected {expected}, got {output}"

    # With delete (uses temp file)
    output_del = get_output_path(input_path, delete_original=True)
    expected_del = Path("/path/to/video.mp4.temp")
    assert output_del == expected_del, f"Expected {expected_del}, got {output_del}"

    print("  ✓ Output path generation works correctly")
    return True


def test_format_size():
    """Test file size formatting."""
    print("Testing size formatting...")

    from compress_videos import format_size

    assert "1.0 B" in format_size(1), f"1 byte failed: {format_size(1)}"
    assert "1.0 KB" in format_size(1024), f"1KB failed: {format_size(1024)}"
    assert "1.0 MB" in format_size(1024**2), f"1MB failed: {format_size(1024**2)}"
    assert "1.0 GB" in format_size(1024**3), f"1GB failed: {format_size(1024**3)}"

    print("  ✓ Size formatting works correctly")
    return True


def test_imports():
    """Test all required imports."""
    print("Testing imports...")

    try:
        import compress_videos
        print("  ✓ compress_videos module imports successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False


def main() -> int:
    """Run all tests."""
    print("=" * 50)
    print("  Video Compression Module Tests")
    print("=" * 50)
    print()

    tests = [
        ("Imports", test_imports),
        ("FFmpeg Check", test_ffmpeg_check),
        ("Quality Presets", test_quality_presets),
        ("Find Videos", test_find_videos),
        ("Output Path Generation", test_output_path_generation),
        ("Format Size", test_format_size),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ {name} failed with exception: {e}")
            failed += 1
        print()

    print("=" * 50)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
