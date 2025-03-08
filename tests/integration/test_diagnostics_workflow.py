"""
Integration tests for the diagnostics workflow.
Tests the end-to-end functionality of the diagnostics system.
"""

import os
import json
import tempfile
from unittest.mock import patch
import pytest

from file_watch_diagnostics.diagnostics import FileWatchDiagnostics
from file_watch_diagnostics.cli.diagnostics import main as diagnostics_main
from file_watch_diagnostics.cli.quick_check import main as quick_check_main


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.mark.timeout(30)  # Increase timeout to 30 seconds
@pytest.mark.integration
def test_diagnostics_end_to_end(temp_dir):
    """Test the end-to-end diagnostics workflow."""
    # Create a diagnostics instance with testing mode enabled
    diagnostics = FileWatchDiagnostics(temp_dir, temp_dir, testing_mode=True)
    
    # Run all diagnostics
    results = diagnostics.run_all_diagnostics()
    
    # Verify the results structure
    assert 'system_info' in results
    assert 'system_limits' in results
    assert 'filesystem_info' in results
    assert 'event_monitoring' in results
    assert 'library_tests' in results
    
    # Check that results were saved
    results_file = os.path.join(temp_dir, 'diagnostics_results.json')
    diagnostics.save_results(results_file)
    assert os.path.exists(results_file)
    
    # Verify the saved results
    with open(results_file, 'r') as f:
        saved_results = json.load(f)
    
    # Compare only the keys since the actual values might differ slightly
    assert set(saved_results.keys()) == set(results.keys())


@pytest.mark.timeout(5)  # Set a 5-second timeout
@pytest.mark.integration
def test_diagnostics_cli_integration(temp_dir):
    """Test the diagnostics CLI integration."""
    # Mock the run_all_diagnostics method to avoid running the full diagnostics
    with patch('file_watch_diagnostics.diagnostics.FileWatchDiagnostics.run_all_diagnostics') as mock_run:
        mock_run.return_value = {
            'system_info': {},
            'system_limits': {},
            'filesystem_info': {},
            'event_monitoring': {},
            'library_tests': {}
        }
        
        # Mock sys.argv with valid arguments including testing mode
        with patch('sys.argv', ['diagnostics.py', temp_dir, '--testing-mode']):
            # Run the CLI
            with patch('sys.exit') as mock_exit:
                # Call the main function
                from file_watch_diagnostics.cli.diagnostics import main as diagnostics_main
                diagnostics_main()
                
                # Verify that the diagnostics were run
                mock_run.assert_called_once()
                mock_exit.assert_called_once_with(0)


@pytest.mark.timeout(5)  # Set a 5-second timeout
@pytest.mark.integration
def test_quick_check_cli_integration(temp_dir):
    """Test the quick check CLI integration."""
    # Mock the run_quick_check function to avoid running the actual check
    with patch('file_watch_diagnostics.cli.quick_check.run_quick_check') as mock_run_quick_check:
        mock_run_quick_check.return_value = {
            'status': 'ok',
            'message': 'All checks passed',
            'details': {},
            'directory': temp_dir,
            'system_limits': {'status': 'ok'},
            'filesystem_compatibility': {'status': 'ok'},
            'resource_constraints': {'status': 'ok'},
            'event_delivery': {'status': 'ok'}
        }
        
        # Mock sys.argv with valid arguments including testing mode
        with patch('sys.argv', ['quick_check.py', '--directory', temp_dir, '--testing']):
            # Mock print to capture output
            with patch('builtins.print') as mock_print:
                # Run the CLI
                with patch('sys.exit') as mock_exit:
                    # Call the main function
                    from file_watch_diagnostics.cli.quick_check import main as quick_check_main
                    quick_check_main()
                    
                    # Verify that the quick check was run
                    mock_run_quick_check.assert_called_once()
                    mock_print.assert_called()
                    mock_exit.assert_called_once_with(0)


@pytest.mark.skip(reason="This test takes too long to run in CI")
def test_full_workflow_integration(temp_dir):
    """Test the full workflow integration with real components."""
    # Create a test file to monitor
    test_file_path = os.path.join(temp_dir, 'test_file.txt')
    with open(test_file_path, 'w') as f:
        f.write('Test content')
    
    # Create a diagnostics instance
    diagnostics = FileWatchDiagnostics(temp_dir, temp_dir)
    
    # Run all diagnostics
    results = diagnostics.run_all_diagnostics()
    
    # Verify the results structure
    assert 'system_info' in results
    assert 'system_limits' in results
    assert 'filesystem_info' in results
    assert 'event_monitoring' in results
    assert 'library_tests' in results
    
    # Check filesystem info
    filesystem_info = results['filesystem_info']
    assert isinstance(filesystem_info, dict)
    
    # Check event monitoring
    event_monitoring = results['event_monitoring']
    assert isinstance(event_monitoring, dict)
    
    # Check library tests
    library_tests = results['library_tests']
    assert isinstance(library_tests, dict)
    
    # Save and verify results
    results_file = os.path.join(temp_dir, 'full_workflow_results.json')
    diagnostics.save_results(results_file)
    assert os.path.exists(results_file)
