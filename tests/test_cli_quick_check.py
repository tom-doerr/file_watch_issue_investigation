"""
Tests for the quick_check CLI module.
"""

import os
import sys
import json
import tempfile
from unittest.mock import patch, MagicMock, call
import pytest

from file_watch_diagnostics.cli.quick_check import (
    parse_args,
    check_system_limits,
    check_filesystem_compatibility,
    check_resource_constraints,
    check_event_delivery,
    run_quick_check,
    main
)


def test_parse_args():
    """Test argument parsing."""
    with patch('sys.argv', ['quick_check.py', '--directory', '/tmp', '--verbose']):
        args = parse_args()
        assert args.directory == '/tmp'
        assert args.verbose is True
    
    with patch('sys.argv', ['quick_check.py']):
        args = parse_args()
        assert args.directory == os.getcwd()
        assert args.verbose is False


@patch('file_watch_diagnostics.cli.quick_check.get_inotify_max_user_watches')
@patch('file_watch_diagnostics.cli.quick_check.get_current_inotify_watches')
def test_check_system_limits(mock_current, mock_max):
    """Test system limits checking."""
    mock_max.return_value = 1000
    mock_current.return_value = 100
    
    result = check_system_limits()
    assert result['status'] == 'ok'
    assert result['max_watches'] == 1000
    assert result['current_watches'] == 100
    
    # Test warning case (>70%)
    mock_current.return_value = 750
    result = check_system_limits()
    assert result['status'] == 'warning'
    
    # Test warning case (>90%)
    mock_current.return_value = 950
    result = check_system_limits()
    assert result['status'] == 'warning'
    
    # Test error case
    mock_max.return_value = "Error: Could not read max watches"
    result = check_system_limits()
    assert result['status'] == 'error'


@patch('file_watch_diagnostics.cli.quick_check.get_filesystem_type')
def test_check_filesystem_compatibility(mock_fs_type):
    """Test filesystem compatibility checking."""
    mock_fs_type.return_value = 'ext4'
    
    result = check_filesystem_compatibility('/tmp')
    assert result['status'] == 'ok'
    assert result['filesystem_type'] == 'ext4'
    
    # Test warning case
    mock_fs_type.return_value = 'nfs'
    result = check_filesystem_compatibility('/tmp')
    assert result['status'] == 'warning'
    
    # Test error case
    mock_fs_type.return_value = "Error: Could not determine filesystem type"
    result = check_filesystem_compatibility('/tmp')
    assert result['status'] == 'error'


@patch('psutil.virtual_memory')
@patch('psutil.cpu_percent')
def test_check_resource_constraints(mock_cpu, mock_memory):
    """Test resource constraints checking."""
    memory_mock = MagicMock()
    memory_mock.percent = 50
    mock_memory.return_value = memory_mock
    mock_cpu.return_value = 50
    
    result = check_resource_constraints()
    assert result['status'] == 'ok'
    assert result['memory_percent'] == 50
    assert result['cpu_percent'] == 50
    
    # Test warning case (high memory)
    memory_mock.percent = 95
    mock_memory.return_value = memory_mock
    result = check_resource_constraints()
    assert result['status'] == 'warning'
    
    # Test warning case (high CPU)
    memory_mock.percent = 50
    mock_memory.return_value = memory_mock
    mock_cpu.return_value = 95
    result = check_resource_constraints()
    assert result['status'] == 'warning'
    
    # Test warning case (both high)
    memory_mock.percent = 95
    mock_memory.return_value = memory_mock
    mock_cpu.return_value = 95
    result = check_resource_constraints()
    assert result['status'] == 'warning'


@patch('file_watch_diagnostics.cli.quick_check.create_event_collector')
@patch('file_watch_diagnostics.cli.quick_check.create_file_for_testing')
@patch('file_watch_diagnostics.cli.quick_check.modify_file_for_testing')
@patch('file_watch_diagnostics.cli.quick_check.delete_file_for_testing')
@patch('tempfile.TemporaryDirectory')
def test_check_event_delivery(mock_temp_dir, mock_delete, mock_modify, mock_create, mock_collector):
    """Test event delivery checking."""
    # Setup mocks
    mock_temp_dir.return_value.__enter__.return_value = '/tmp/test'
    mock_create.return_value = '/tmp/test/file.txt'
    
    collector_mock = MagicMock()
    collector_mock.get_events.return_value = ['create', 'modify', 'delete']
    mock_collector.return_value = collector_mock
    
    result = check_event_delivery('/tmp')
    assert result['status'] == 'ok'
    assert result['events_detected'] == 3
    
    # Test warning case (fewer events)
    collector_mock.get_events.return_value = ['create']
    result = check_event_delivery('/tmp')
    assert result['status'] == 'warning'
    
    # Test error case
    mock_create.side_effect = Exception("Test error")
    result = check_event_delivery('/tmp')
    assert result['status'] == 'error'


@patch('file_watch_diagnostics.cli.quick_check.check_system_limits')
@patch('file_watch_diagnostics.cli.quick_check.check_filesystem_compatibility')
@patch('file_watch_diagnostics.cli.quick_check.check_resource_constraints')
@patch('file_watch_diagnostics.cli.quick_check.check_event_delivery')
def test_run_quick_check(mock_event, mock_resource, mock_fs, mock_system):
    """Test running all quick checks."""
    # Setup mocks
    mock_system.return_value = {'status': 'ok'}
    mock_fs.return_value = {'status': 'ok'}
    mock_resource.return_value = {'status': 'ok'}
    mock_event.return_value = {'status': 'ok'}
    
    result = run_quick_check('/tmp')
    assert result['status'] == 'ok'
    assert result['directory'] == '/tmp'
    
    # Test warning case
    mock_fs.return_value = {'status': 'warning'}
    result = run_quick_check('/tmp')
    assert result['status'] == 'warning'
    
    # Test error case
    mock_event.return_value = {'status': 'error'}
    result = run_quick_check('/tmp')
    assert result['status'] == 'error'


@patch('file_watch_diagnostics.cli.quick_check.parse_args')
@patch('file_watch_diagnostics.cli.quick_check.run_quick_check')
@patch('file_watch_diagnostics.cli.quick_check.json.dumps')
@patch('builtins.print')
@patch('file_watch_diagnostics.cli.quick_check.sys.exit')
def test_main(mock_exit, mock_print, mock_json_dumps, mock_run, mock_parse):
    """Test main function."""
    # Setup mocks
    args_mock = MagicMock()
    args_mock.directory = '/tmp'
    args_mock.verbose = False
    args_mock.testing = False
    mock_parse.return_value = args_mock
    
    mock_run.return_value = {
        'directory': '/tmp',
        'system_limits': {'status': 'ok'},
        'filesystem_compatibility': {'status': 'ok'},
        'resource_constraints': {'status': 'ok'},
        'event_delivery': {'status': 'ok'},
        'status': 'ok'
    }
    
    main()
    
    # Verify print calls
    assert mock_print.call_count > 0
    
    # Verify exit was called with 0 for success
    mock_exit.assert_called_once_with(0)
    
    # Reset mocks
    mock_print.reset_mock()
    mock_exit.reset_mock()
    
    # Test with warning status
    mock_run.return_value['status'] = 'warning'
    
    main()
    
    # Verify exit was called with 1 for warning
    mock_exit.assert_called_once_with(1)
    
    # Reset mocks
    mock_print.reset_mock()
    mock_exit.reset_mock()
    
    # Test verbose output
    args_mock.verbose = True
    args_mock.testing = True
    mock_json_dumps.return_value = '{"formatted": "json"}'
    mock_run.return_value['status'] = 'ok'
    
    main()
    
    # Verify json_dumps was called
    mock_json_dumps.assert_called_once()
    # Verify the formatted JSON was printed
    assert call('{"formatted": "json"}') in mock_print.call_args_list
    # Verify exit was called with 0 for success
    mock_exit.assert_called_once_with(0)
