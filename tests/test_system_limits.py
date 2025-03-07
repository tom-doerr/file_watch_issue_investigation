"""
Tests for the system_limits module.
"""

import os
import sys
import pytest
from unittest import mock
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_watch_diagnostics.utils.system_limits import (
    get_inotify_max_user_watches,
    get_inotify_max_user_instances,
    get_inotify_max_queued_events,
    get_current_inotify_watches,
    get_inotify_watch_details,
    get_filesystem_info,
    get_filesystem_type,
    check_system_limits
)


def test_get_inotify_max_user_watches():
    """Test getting max user watches."""
    # Mock the open function to return a known value
    mock_open = mock.mock_open(read_data="524288\n")
    with mock.patch("builtins.open", mock_open):
        result = get_inotify_max_user_watches()
        assert result == 524288


def test_get_inotify_max_user_watches_error():
    """Test error handling when getting max user watches."""
    # Mock the open function to raise an exception
    with mock.patch("builtins.open", side_effect=FileNotFoundError("File not found")):
        result = get_inotify_max_user_watches()
        assert isinstance(result, str)
        assert "Error reading max_user_watches" in result


def test_get_inotify_max_user_instances():
    """Test getting max user instances."""
    # Mock the open function to return a known value
    mock_open = mock.mock_open(read_data="128\n")
    with mock.patch("builtins.open", mock_open):
        result = get_inotify_max_user_instances()
        assert result == 128


def test_get_inotify_max_queued_events():
    """Test getting max queued events."""
    # Mock the open function to return a known value
    mock_open = mock.mock_open(read_data="16384\n")
    with mock.patch("builtins.open", mock_open):
        result = get_inotify_max_queued_events()
        assert result == 16384


def test_get_current_inotify_watches():
    """Test getting current inotify watches."""
    # Mock the subprocess.run function to return a known value
    mock_result = mock.MagicMock()
    mock_result.stdout = "75\n"
    with mock.patch("subprocess.run", return_value=mock_result):
        result = get_current_inotify_watches()
        assert result == 75


def test_get_current_inotify_watches_error():
    """Test error handling when getting current inotify watches."""
    # Mock the subprocess.run function to raise an exception
    with mock.patch("subprocess.run", side_effect=Exception("Command failed")):
        result = get_current_inotify_watches()
        assert isinstance(result, str)
        assert "Error counting current watches" in result


def test_get_inotify_watch_details():
    """Test getting inotify watch details."""
    # Mock the subprocess.run function to return a known value
    mock_result = mock.MagicMock()
    mock_result.stdout = "3 1234\n2 5678\n"
    
    # Mock the psutil.Process function to return mock processes
    mock_process1 = mock.MagicMock()
    mock_process1.name.return_value = "process1"
    mock_process1.cmdline.return_value = ["cmd1", "arg1"]
    
    mock_process2 = mock.MagicMock()
    mock_process2.name.return_value = "process2"
    mock_process2.cmdline.return_value = ["cmd2", "arg2"]
    
    with mock.patch("subprocess.run", return_value=mock_result):
        with mock.patch("psutil.Process", side_effect=[mock_process1, mock_process2]):
            result = get_inotify_watch_details()
            
            assert len(result) == 2
            assert result[0]["pid"] == 1234
            assert result[0]["name"] == "process1"
            assert result[0]["watch_count"] == 3
            assert result[1]["pid"] == 5678
            assert result[1]["name"] == "process2"
            assert result[1]["watch_count"] == 2


def test_get_filesystem_type():
    """Test getting filesystem type."""
    # Mock the subprocess.run function to return a known value
    mock_result = mock.MagicMock()
    mock_result.stdout = "ext4\n"
    with mock.patch("subprocess.run", return_value=mock_result):
        result = get_filesystem_type("/tmp")
        assert result == "ext4"


def test_get_filesystem_info():
    """Test getting filesystem info."""
    # Mock the os.statvfs function to return a known value
    mock_statvfs = mock.MagicMock()
    mock_statvfs.f_blocks = 1000000
    mock_statvfs.f_frsize = 4096
    mock_statvfs.f_bfree = 500000
    mock_statvfs.f_files = 1000000
    mock_statvfs.f_ffree = 900000
    mock_statvfs.f_namemax = 255
    
    with mock.patch("os.statvfs", return_value=mock_statvfs):
        with mock.patch("file_watch_diagnostics.utils.system_limits.get_filesystem_type", return_value="ext4"):
            result = get_filesystem_info("/tmp")
            
            assert result["filesystem_type"] == "ext4"
            assert result["total_space_gb"] == 1000000 * 4096 / (1024**3)
            assert result["free_space_gb"] == 500000 * 4096 / (1024**3)
            assert result["inodes_total"] == 1000000
            assert result["inodes_free"] == 900000
            assert result["max_filename_length"] == 255


def test_check_system_limits():
    """Test checking all system limits."""
    with mock.patch("file_watch_diagnostics.utils.system_limits.get_inotify_max_user_watches", return_value=524288):
        with mock.patch("file_watch_diagnostics.utils.system_limits.get_inotify_max_user_instances", return_value=128):
            with mock.patch("file_watch_diagnostics.utils.system_limits.get_inotify_max_queued_events", return_value=16384):
                with mock.patch("file_watch_diagnostics.utils.system_limits.get_current_inotify_watches", return_value=75):
                    with mock.patch("file_watch_diagnostics.utils.system_limits.get_inotify_watch_details", return_value=[]):
                        result = check_system_limits()
                        
                        assert result["max_user_watches"] == 524288
                        assert result["max_user_instances"] == 128
                        assert result["max_queued_events"] == 16384
                        assert result["current_watches"] == 75
                        assert result["watch_details"] == []
