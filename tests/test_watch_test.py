"""
Tests for the watch_test module.
"""

import os
import sys
import time
import pytest
import tempfile
from unittest import mock
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_watch_diagnostics.utils.watch_test import (
    generate_random_string,
    create_file_for_testing,
    modify_file_for_testing,
    delete_file_for_testing,
    run_watchdog_test,
    run_pyinotify_test,
    run_all_library_tests
)


def test_generate_random_string():
    """Test generating a random string."""
    # Test default length
    string1 = generate_random_string()
    assert len(string1) == 10
    assert isinstance(string1, str)
    
    # Test custom length
    string2 = generate_random_string(length=20)
    assert len(string2) == 20
    assert isinstance(string2, str)
    
    # Test uniqueness
    string3 = generate_random_string()
    assert string1 != string3


def test_create_test_file():
    """Test creating a test file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        path = create_file_for_testing(temp_dir)
        
        # Check that the file exists
        assert os.path.exists(path)
        
        # Check that the file has content
        with open(path, 'r') as f:
            content = f.read()
            assert len(content) == 1024  # Default content size
        
        # Create another test file with custom content size
        path2 = create_file_for_testing(temp_dir, content_size=2048)
        
        # Check that the file has the custom content size
        with open(path2, 'r') as f:
            content = f.read()
            assert len(content) == 2048


def test_modify_test_file():
    """Test modifying a test file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        path = create_file_for_testing(temp_dir)
        
        # Get the original content
        with open(path, 'r') as f:
            original_content = f.read()
        
        # Modify the file
        modify_file_for_testing(path)
        
        # Check that the file still exists
        assert os.path.exists(path)
        
        # Check that the content has changed
        with open(path, 'r') as f:
            new_content = f.read()
            assert new_content != original_content
            assert len(new_content) == 1024  # Default content size
        
        # Modify the file with custom content size
        modify_file_for_testing(path, content_size=2048)
        
        # Check that the content has changed and has the custom size
        with open(path, 'r') as f:
            new_content2 = f.read()
            assert new_content2 != new_content
            assert len(new_content2) == 2048


def test_delete_test_file():
    """Test deleting a test file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        path = create_file_for_testing(temp_dir)
        
        # Check that the file exists
        assert os.path.exists(path)
        
        # Delete the file
        delete_file_for_testing(path)
        
        # Check that the file no longer exists
        assert not os.path.exists(path)


def test_run_watchdog_not_available():
    """Test watchdog testing when the library is not available."""
    with mock.patch("builtins.__import__", side_effect=ImportError("No module named 'watchdog'")):
        result = run_watchdog_test("/tmp")
        
        assert result["status"] == "error"
        assert "watchdog library is not available" in result["message"]


def test_run_pyinotify_not_available():
    """Test pyinotify testing when the library is not available."""
    with mock.patch("builtins.__import__", side_effect=ImportError("No module named 'pyinotify'")):
        result = run_pyinotify_test("/tmp")
        
        assert result["status"] == "error"
        assert "pyinotify library is not available" in result["message"]


def test_run_all_libraries():
    """Test testing all libraries."""
    # Mock the test functions to return known values
    watchdog_result = {"status": "success", "events_detected": 10, "events_missed": 0}
    pyinotify_result = {"status": "success", "events_detected": 12, "events_missed": 1}
    
    with mock.patch("file_watch_diagnostics.utils.watch_test.run_watchdog_test", return_value=watchdog_result):
        with mock.patch("file_watch_diagnostics.utils.watch_test.run_pyinotify_test", return_value=pyinotify_result):
            result = run_all_library_tests("/tmp", duration_seconds=0.1)
            
            assert "watchdog" in result
            assert "pyinotify" in result
            assert result["watchdog"] == watchdog_result
            assert result["pyinotify"] == pyinotify_result
