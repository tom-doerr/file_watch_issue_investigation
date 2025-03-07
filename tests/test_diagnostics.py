"""
Tests for the diagnostics module.
"""

import os
import sys
import json
import tempfile
from unittest import mock
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_watch_diagnostics.diagnostics import FileWatchDiagnostics


def test_init():
    """Test initializing the diagnostics class."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the create_log_filename function to return a known value
        log_file = os.path.join(temp_dir, "test.log")
        with mock.patch("file_watch_diagnostics.diagnostics.create_log_filename", return_value=log_file):
            # Initialize the diagnostics class
            diagnostics = FileWatchDiagnostics(target_dir=temp_dir)
            
            assert diagnostics.target_dir == Path(temp_dir).resolve()
            assert diagnostics.log_file == log_file
            assert diagnostics.logger is not None
            assert "timestamp" in diagnostics.results
            assert diagnostics.results["target_directory"] == str(Path(temp_dir).resolve())


def test_run_system_info_check():
    """Test running the system info check."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the create_log_filename function to return a known value
        log_file = os.path.join(temp_dir, "test.log")
        with mock.patch("file_watch_diagnostics.diagnostics.create_log_filename", return_value=log_file):
            # Initialize the diagnostics class
            diagnostics = FileWatchDiagnostics(target_dir=temp_dir)
            
            # Run the system info check
            diagnostics._run_system_info_check()
            
            # Check that the results were updated
            assert "system_info" in diagnostics.results
            assert "platform" in diagnostics.results["system_info"]
            assert "python_version" in diagnostics.results["system_info"]
            assert "cpu_count" in diagnostics.results["system_info"]
            assert "memory_total_gb" in diagnostics.results["system_info"]
            assert "memory_available_gb" in diagnostics.results["system_info"]


def test_run_system_limits_check():
    """Test running the system limits check."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the create_log_filename function to return a known value
        log_file = os.path.join(temp_dir, "test.log")
        with mock.patch("file_watch_diagnostics.diagnostics.create_log_filename", return_value=log_file):
            # Mock the check_system_limits function to return known values
            system_limits = {
                "max_user_watches": 524288,
                "max_user_instances": 128,
                "max_queued_events": 16384,
                "current_watches": 75,
                "watch_details": []
            }
            with mock.patch("file_watch_diagnostics.diagnostics.check_system_limits", return_value=system_limits):
                # Initialize the diagnostics class
                diagnostics = FileWatchDiagnostics(target_dir=temp_dir)
                
                # Run the system limits check
                diagnostics._run_system_limits_check()
                
                # Check that the results were updated
                assert "system_limits" in diagnostics.results
                assert diagnostics.results["system_limits"] == system_limits


def test_run_filesystem_info_check():
    """Test running the filesystem info check."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the create_log_filename function to return a known value
        log_file = os.path.join(temp_dir, "test.log")
        with mock.patch("file_watch_diagnostics.diagnostics.create_log_filename", return_value=log_file):
            # Mock the get_filesystem_info function to return known values
            filesystem_info = {
                "path": temp_dir,
                "filesystem_type": "ext4",
                "total_space_gb": 100.0,
                "free_space_gb": 50.0,
                "inodes_total": 1000000,
                "inodes_free": 900000,
                "max_filename_length": 255
            }
            with mock.patch("file_watch_diagnostics.diagnostics.get_filesystem_info", return_value=filesystem_info):
                # Initialize the diagnostics class
                diagnostics = FileWatchDiagnostics(target_dir=temp_dir)
                
                # Run the filesystem info check
                diagnostics._run_filesystem_info_check()
                
                # Check that the results were updated
                assert "filesystem_info" in diagnostics.results
                assert diagnostics.results["filesystem_info"] == filesystem_info


def test_run_event_monitoring():
    """Test running event monitoring."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the create_log_filename function to return a known value
        log_file = os.path.join(temp_dir, "test.log")
        with mock.patch("file_watch_diagnostics.diagnostics.create_log_filename", return_value=log_file):
            # Mock the monitor_events function to return known values
            watchdog_results = {
                "stats": {"events_count": 10},
                "events": [{"event": 1}, {"event": 2}]
            }
            pyinotify_results = {
                "stats": {"events_count": 12},
                "events": [{"event": 3}, {"event": 4}]
            }
            
            def mock_monitor_events(path, duration, library):
                if library == "watchdog":
                    return watchdog_results
                elif library == "pyinotify":
                    return pyinotify_results
            
            with mock.patch("file_watch_diagnostics.diagnostics.monitor_events", side_effect=mock_monitor_events):
                # Initialize the diagnostics class
                diagnostics = FileWatchDiagnostics(target_dir=temp_dir)
                
                # Run event monitoring
                diagnostics._run_event_monitoring()
                
                # Check that the results were updated
                assert "event_monitoring" in diagnostics.results
                assert "watchdog" in diagnostics.results["event_monitoring"]
                assert "pyinotify" in diagnostics.results["event_monitoring"]
                assert diagnostics.results["event_monitoring"]["watchdog"] == watchdog_results
                assert diagnostics.results["event_monitoring"]["pyinotify"] == pyinotify_results


def test_run_library_tests():
    """Test running library tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the create_log_filename function to return a known value
        log_file = os.path.join(temp_dir, "test.log")
        with mock.patch("file_watch_diagnostics.diagnostics.create_log_filename", return_value=log_file):
            # Mock the run_all_library_tests function to return known values
            library_tests = {
                "watchdog": {
                    "status": "success",
                    "events_detected": 10,
                    "events_missed": 0
                },
                "pyinotify": {
                    "status": "success",
                    "events_detected": 12,
                    "events_missed": 1
                }
            }
            
            with mock.patch("file_watch_diagnostics.diagnostics.run_all_library_tests", return_value=library_tests):
                # Initialize the diagnostics class
                diagnostics = FileWatchDiagnostics(target_dir=temp_dir)
                
                # Run library tests
                diagnostics._run_library_tests()
                
                # Check that the results were updated
                assert "library_tests" in diagnostics.results
                assert diagnostics.results["library_tests"] == library_tests


def test_save_results():
    """Test saving results."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the create_log_filename function to return a known value
        log_file = os.path.join(temp_dir, "test.log")
        with mock.patch("file_watch_diagnostics.diagnostics.create_log_filename", return_value=log_file):
            # Initialize the diagnostics class
            diagnostics = FileWatchDiagnostics(target_dir=temp_dir, log_dir=temp_dir)
            
            # Add some test results
            diagnostics.results["test"] = "value"
            
            # Save the results
            diagnostics._save_results()
            
            # Check that the results file was created
            assert hasattr(diagnostics, "results_file")
            assert os.path.exists(diagnostics.results_file)
            
            # Check that the results were saved correctly
            with open(diagnostics.results_file, 'r') as f:
                saved_results = json.load(f)
                assert "test" in saved_results
                assert saved_results["test"] == "value"


def test_run_all_diagnostics():
    """Test running all diagnostics."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the create_log_filename function to return a known value
        log_file = os.path.join(temp_dir, "test.log")
        with mock.patch("file_watch_diagnostics.diagnostics.create_log_filename", return_value=log_file):
            # Mock all the individual diagnostic functions
            with mock.patch.object(FileWatchDiagnostics, "_run_system_info_check") as mock_system_info:
                with mock.patch.object(FileWatchDiagnostics, "_run_system_limits_check") as mock_system_limits:
                    with mock.patch.object(FileWatchDiagnostics, "_run_filesystem_info_check") as mock_filesystem_info:
                        with mock.patch.object(FileWatchDiagnostics, "_run_event_monitoring") as mock_event_monitoring:
                            with mock.patch.object(FileWatchDiagnostics, "_run_library_tests") as mock_library_tests:
                                with mock.patch.object(FileWatchDiagnostics, "_save_results") as mock_save_results:
                                    # Initialize the diagnostics class
                                    diagnostics = FileWatchDiagnostics(target_dir=temp_dir)
                                    
                                    # Run all diagnostics
                                    results = diagnostics.run_all_diagnostics()
                                    
                                    # Check that all the individual functions were called
                                    mock_system_info.assert_called_once()
                                    mock_system_limits.assert_called_once()
                                    mock_filesystem_info.assert_called_once()
                                    mock_event_monitoring.assert_called_once()
                                    mock_library_tests.assert_called_once()
                                    mock_save_results.assert_called_once()
                                    
                                    # Check that the results were returned
                                    assert results is diagnostics.results
