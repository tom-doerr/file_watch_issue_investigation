"""
Tests for the quick_check.py script.
"""

import os
import sys
import json
import pytest
from unittest import mock
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the quick_check module
import quick_check


def test_parse_args():
    """Test parsing command-line arguments."""
    # Test with default arguments
    with mock.patch("sys.argv", ["quick_check.py"]):
        args = quick_check.parse_args()
        assert args.directory == os.getcwd()
        assert args.verbose == False
    
    # Test with custom arguments
    with mock.patch("sys.argv", ["quick_check.py", "--directory", "/tmp", "--verbose"]):
        args = quick_check.parse_args()
        assert args.directory == "/tmp"
        assert args.verbose == True


def test_check_system_limits():
    """Test checking system limits."""
    # Mock the get_inotify_max_user_watches function to return a known value
    with mock.patch("quick_check.get_inotify_max_user_watches", return_value=524288):
        # Mock the get_current_inotify_watches function to return a known value
        with mock.patch("quick_check.get_current_inotify_watches", return_value=75):
            # Call the function
            result = quick_check.check_system_limits()
            
            # Check the result
            assert result["max_watches"] == 524288
            assert result["current_watches"] == 75
            assert result["status"] == "ok"


def test_check_filesystem_compatibility():
    """Test checking filesystem compatibility."""
    # Mock the get_filesystem_type function to return a known value
    with mock.patch("quick_check.get_filesystem_type", return_value="ext4"):
        # Call the function
        result = quick_check.check_filesystem_compatibility("/tmp")
        
        # Check the result
        assert result["filesystem_type"] == "ext4"
        assert result["status"] == "ok"
    
    # Test with a less compatible filesystem
    with mock.patch("quick_check.get_filesystem_type", return_value="nfs"):
        # Call the function
        result = quick_check.check_filesystem_compatibility("/tmp")
        
        # Check the result
        assert result["filesystem_type"] == "nfs"
        assert result["status"] == "warning"
        assert "limited inotify support" in result["message"]


def test_check_resource_constraints():
    """Test checking resource constraints."""
    # Mock the psutil functions to return known values
    with mock.patch("psutil.cpu_percent", return_value=50.0):
        with mock.patch("psutil.virtual_memory") as mock_memory:
            mock_memory.return_value.percent = 75.0
            
            # Call the function
            result = quick_check.check_resource_constraints()
            
            # Check the result
            assert result["cpu_percent"] == 50.0
            assert result["memory_percent"] == 75.0
            assert result["status"] == "ok"


class MockEventCollector:
    def __init__(self, events=None):
        self.events = events or []
    
    def get_events(self):
        return self.events
    
    def start(self, path):
        pass
    
    def stop(self):
        pass


def test_check_event_delivery():
    """Test checking event delivery."""
    # Mock the create_event_collector function to return a mock event collector
    mock_collector = MockEventCollector([
        {"type": "created", "path": "/tmp/test.txt"},
        {"type": "modified", "path": "/tmp/test.txt"},
        {"type": "deleted", "path": "/tmp/test.txt"}
    ])
    
    with mock.patch("quick_check.create_event_collector", return_value=mock_collector):
        with mock.patch("quick_check.create_file_for_testing"):
            with mock.patch("quick_check.modify_file_for_testing"):
                with mock.patch("quick_check.delete_file_for_testing"):
                    with mock.patch("quick_check.time.sleep"):
                        # Call the function
                        result = quick_check.check_event_delivery("/tmp")
                        
                        # Check the result
                        assert result["events_detected"] == 3
                        assert result["status"] == "ok"


def test_run_quick_check():
    """Test running a quick check."""
    # Mock all the individual check functions
    system_limits_result = {
        "max_watches": 524288,
        "current_watches": 75,
        "status": "ok"
    }
    filesystem_result = {
        "filesystem_type": "ext4",
        "status": "ok"
    }
    resource_result = {
        "cpu_percent": 50.0,
        "memory_percent": 75.0,
        "status": "ok"
    }
    event_result = {
        "events_detected": 3,
        "status": "ok"
    }
    
    with mock.patch("quick_check.check_system_limits", return_value=system_limits_result):
        with mock.patch("quick_check.check_filesystem_compatibility", return_value=filesystem_result):
            with mock.patch("quick_check.check_resource_constraints", return_value=resource_result):
                with mock.patch("quick_check.check_event_delivery", return_value=event_result):
                    # Call the function
                    result = quick_check.run_quick_check("/tmp")
                    
                    # Check the result
                    assert "directory" in result
                    assert result["directory"] == "/tmp"
                    assert result["system_limits"] == system_limits_result
                    assert result["filesystem_compatibility"] == filesystem_result
                    assert result["resource_constraints"] == resource_result
                    assert result["event_delivery"] == event_result
                    assert "status" in result
                    assert result["status"] == "ok"
