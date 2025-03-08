"""
Tests for the diagnostics CLI module.
"""

import os
import sys
from unittest.mock import patch, MagicMock
import pytest

from file_watch_diagnostics.cli.diagnostics import main


@patch('file_watch_diagnostics.cli.diagnostics.argparse.ArgumentParser')
@patch('file_watch_diagnostics.cli.diagnostics.FileWatchDiagnostics')
@patch('file_watch_diagnostics.cli.diagnostics.sys.exit')
def test_main(mock_exit, mock_diagnostics, mock_argparse):
    """Test main function."""
    # Setup mocks
    parser_mock = MagicMock()
    args_mock = MagicMock()
    args_mock.directory = '/tmp'
    args_mock.log_dir = '/tmp/logs'
    args_mock.log_level = 'INFO'
    args_mock.testing_mode = False
    parser_mock.parse_args.return_value = args_mock
    mock_argparse.return_value = parser_mock
    
    diagnostics_mock = MagicMock()
    mock_diagnostics.return_value = diagnostics_mock
    
    # Call main
    main()
    
    # Verify FileWatchDiagnostics was initialized with correct arguments
    mock_diagnostics.assert_called_once_with('/tmp', '/tmp/logs', 'INFO', testing_mode=False)
    
    # Verify run_all_diagnostics was called
    diagnostics_mock.run_all_diagnostics.assert_called_once()
    
    # Verify sys.exit was called with 0
    mock_exit.assert_called_once_with(0)
    
    # Test with different arguments
    args_mock.directory = None
    args_mock.log_dir = None
    args_mock.log_level = 'DEBUG'
    args_mock.testing_mode = True
    
    # Reset mocks
    mock_diagnostics.reset_mock()
    diagnostics_mock.reset_mock()
    mock_exit.reset_mock()
    
    # Call main again
    main()
    
    # Verify FileWatchDiagnostics was initialized with correct arguments
    mock_diagnostics.assert_called_once_with(None, None, 'DEBUG', testing_mode=True)
    
    # Verify sys.exit was called with 0
    mock_exit.assert_called_once_with(0)
