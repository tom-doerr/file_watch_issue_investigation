"""
Integration tests for the quick check functionality.
Tests the end-to-end functionality of the quick check system.
"""

import os
import json
import tempfile
import pytest

from file_watch_diagnostics.cli.quick_check import (
    check_system_limits,
    check_filesystem_compatibility,
    check_resource_constraints,
    check_event_delivery,
    run_quick_check
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.mark.timeout(5)  # Set a 5-second timeout
@pytest.mark.integration
def test_check_system_limits_integration():
    """Test the check_system_limits function with the actual system."""
    # Run the system limits check
    result = check_system_limits()
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert 'status' in result
    assert result['status'] in ['ok', 'warning', 'error']
    assert 'max_watches' in result
    assert 'current_watches' in result
    
    # Calculate percent used
    if 'max_watches' in result and 'current_watches' in result:
        if isinstance(result['max_watches'], int) and isinstance(result['current_watches'], int):
            percent_used = (result['current_watches'] / result['max_watches']) * 100
            
            # If status is ok, percent_used should be less than 70%
            if result['status'] == 'ok':
                assert percent_used < 70
            
            # If status is warning, percent_used should be between 70% and 100%
            if result['status'] == 'warning':
                assert 70 <= percent_used <= 100
    
    # If status is error, there should be an error message
    if result['status'] == 'error':
        assert 'error' in result


@pytest.mark.timeout(5)  # Set a 5-second timeout
@pytest.mark.integration
def test_check_filesystem_compatibility_integration(temp_dir):
    """Test the check_filesystem_compatibility function with the actual filesystem."""
    # Run the filesystem compatibility check
    result = check_filesystem_compatibility(temp_dir)
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert 'status' in result
    assert result['status'] in ['ok', 'warning', 'error']
    assert 'filesystem_type' in result
    
    # If status is not ok, there should be a message
    if result['status'] != 'ok':
        assert 'message' in result


@pytest.mark.timeout(5)  # Set a 5-second timeout
@pytest.mark.integration
def test_check_resource_constraints_integration():
    """Test the check_resource_constraints function with the actual system."""
    # Run the resource constraints check
    result = check_resource_constraints()
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert 'status' in result
    assert result['status'] in ['ok', 'warning', 'error']
    
    # Check that either memory_available_gb or memory_percent is in the result
    assert 'memory_percent' in result or 'memory_available_gb' in result
    
    # Check that either cpu_count or cpu_percent is in the result
    assert 'cpu_percent' in result or 'cpu_count' in result
    
    # If memory_percent is present, it should be between 0 and 100
    if 'memory_percent' in result:
        assert 0 <= result['memory_percent'] <= 100
    
    # If cpu_percent is present, it should be between 0 and 100
    if 'cpu_percent' in result:
        assert 0 <= result['cpu_percent'] <= 100
    
    # If memory_available_gb is present, it should be a positive number
    if 'memory_available_gb' in result:
        assert result['memory_available_gb'] > 0
    
    # If cpu_count is present, it should be a positive integer
    if 'cpu_count' in result:
        assert result['cpu_count'] > 0
        assert isinstance(result['cpu_count'], int)
    
    # If status is not ok, there should be a message
    if result['status'] != 'ok':
        assert 'message' in result


@pytest.mark.timeout(10)  # Set a 10-second timeout
@pytest.mark.integration
def test_check_event_delivery_integration(temp_dir):
    """Test the check_event_delivery function with the actual filesystem."""
    try:
        # Run the event delivery check with testing mode enabled
        result = check_event_delivery(temp_dir, testing=True)
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert 'status' in result
        assert result['status'] in ['ok', 'warning', 'error']
        
        # There should be information about events
        assert 'events_detected' in result
        
        # If status is not ok, there should be a message
        if result['status'] != 'ok':
            assert 'message' in result
    except OSError as e:
        if "inotify watch limit reached" in str(e):
            pytest.skip("Skipping test due to inotify watch limit reached")
        else:
            raise


@pytest.mark.timeout(15)  # Set a 15-second timeout
@pytest.mark.integration
def test_run_quick_check_integration(temp_dir):
    """Test the run_quick_check function with the actual system."""
    try:
        # Run the quick check with testing mode enabled
        result = run_quick_check(temp_dir, testing=True)
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert 'status' in result
        assert result['status'] in ['ok', 'warning', 'error']
        assert 'directory' in result
        assert result['directory'] == temp_dir
        
        # Check that all individual checks were performed
        assert 'system_limits' in result
        assert 'filesystem_compatibility' in result
        assert 'resource_constraints' in result
        
        # The event_delivery check might fail due to watch limits
        # So we'll check for either a result or an error
        if 'event_delivery' in result:
            assert isinstance(result['event_delivery'], dict)
    except OSError as e:
        if "inotify watch limit reached" in str(e):
            pytest.skip("Skipping test due to inotify watch limit reached")
        else:
            raise
