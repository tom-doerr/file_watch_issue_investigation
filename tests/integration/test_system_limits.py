"""
Integration tests for the system limits functionality.
Tests the interaction with the actual system configuration.
"""

import os
import tempfile
import pytest

from file_watch_diagnostics.utils.system_limits import (
    get_inotify_max_user_watches,
    get_inotify_max_user_instances,
    get_inotify_max_queued_events,
    get_current_inotify_watches,
    get_inotify_watch_details,
    get_filesystem_type,
    get_filesystem_info,
    check_system_limits
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.mark.timeout(5)  # Set a 5-second timeout
@pytest.mark.integration
def test_inotify_limits_integration():
    """Test retrieving actual inotify limits from the system."""
    # Get the max user watches
    max_watches = get_inotify_max_user_watches()
    
    # This should be a positive integer on Linux systems with inotify
    if isinstance(max_watches, int):
        assert max_watches > 0
    else:
        # If not an integer, it should be an error message
        assert isinstance(max_watches, str)
        assert max_watches.startswith("Error")
    
    # Get the max user instances
    max_instances = get_inotify_max_user_instances()
    
    # This should be a positive integer on Linux systems with inotify
    if isinstance(max_instances, int):
        assert max_instances > 0
    else:
        # If not an integer, it should be an error message
        assert isinstance(max_instances, str)
        assert max_instances.startswith("Error")
    
    # Get the max queued events
    max_queued = get_inotify_max_queued_events()
    
    # This should be a positive integer on Linux systems with inotify
    if isinstance(max_queued, int):
        assert max_queued > 0
    else:
        # If not an integer, it should be an error message
        assert isinstance(max_queued, str)
        assert max_queued.startswith("Error")


@pytest.mark.timeout(5)  # Set a 5-second timeout
@pytest.mark.integration
def test_current_watches_integration():
    """Test retrieving current inotify watches from the system."""
    # Get the current watches
    current_watches = get_current_inotify_watches()
    
    # This should be a non-negative integer on Linux systems with inotify
    if isinstance(current_watches, int):
        assert current_watches >= 0
    else:
        # If not an integer, it should be an error message
        assert isinstance(current_watches, str)
        assert current_watches.startswith("Error")
    
    # Get watch details
    watch_details = get_inotify_watch_details()
    
    # This should be a list or an error message
    if isinstance(watch_details, list):
        # Each item should be a dictionary with pid, name, and watch count
        for item in watch_details:
            assert isinstance(item, dict)
            assert 'pid' in item
            assert 'name' in item
            
            # Check for either 'watches' or 'watch_count' key
            assert 'watches' in item or 'watch_count' in item
            
            # Validate pid
            assert isinstance(item['pid'], int)
            
            # Validate name
            assert isinstance(item['name'], str)
            
            # Validate watch count
            if 'watches' in item:
                assert isinstance(item['watches'], int)
            if 'watch_count' in item:
                assert isinstance(item['watch_count'], int)
    else:
        # If not a list, it should be an error message
        assert isinstance(watch_details, str)
        assert watch_details.startswith("Error")


@pytest.mark.timeout(5)  # Set a 5-second timeout
@pytest.mark.integration
def test_filesystem_info_integration(temp_dir):
    """Test retrieving filesystem information from the system."""
    # Get the filesystem type
    fs_type = get_filesystem_type(temp_dir)
    
    # This should be a string representing the filesystem type
    assert isinstance(fs_type, str)
    assert len(fs_type) > 0
    
    # Get detailed filesystem info
    fs_info = get_filesystem_info(temp_dir)
    
    # This should be a dictionary with filesystem details
    assert isinstance(fs_info, dict)
    assert 'filesystem_type' in fs_info
    assert 'total_space_gb' in fs_info
    assert 'free_space_gb' in fs_info
    
    # Values should be of the correct type
    assert isinstance(fs_info['filesystem_type'], str)
    assert isinstance(fs_info['total_space_gb'], float)
    assert isinstance(fs_info['free_space_gb'], float)
    
    # Free space should be less than or equal to total space
    assert fs_info['free_space_gb'] <= fs_info['total_space_gb']


@pytest.mark.timeout(5)  # Set a 5-second timeout
@pytest.mark.integration
def test_check_system_limits_integration():
    """Test the check_system_limits function with the actual system."""
    # Run the system limits check
    limits = check_system_limits()
    
    # This should be a dictionary with system limits
    assert isinstance(limits, dict)
    assert 'max_user_watches' in limits
    assert 'max_user_instances' in limits
    assert 'max_queued_events' in limits
    assert 'current_watches' in limits
    
    # If watch_per_process is present, it should be a list
    if 'watch_per_process' in limits:
        assert isinstance(limits['watch_per_process'], list)
        
        # Each item should be a dictionary with pid, name, and watches
        for item in limits['watch_per_process']:
            assert isinstance(item, dict)
            assert 'pid' in item
            assert 'name' in item
            assert 'watches' in item
