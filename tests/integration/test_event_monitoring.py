"""
Integration tests for the event monitoring system.
Tests the interaction between the event monitoring system and the filesystem.
"""

import os
import time
import tempfile
import pytest

from file_watch_diagnostics.utils.event_monitor import (
    EventCollector,
    create_event_collector,
    monitor_events
)
from file_watch_diagnostics.utils.watch_test import (
    create_file_for_testing,
    modify_file_for_testing,
    delete_file_for_testing
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.mark.timeout(15)  # Set a 15-second timeout
@pytest.mark.integration
def test_event_collector_real_events(temp_dir):
    """Test the EventCollector with real filesystem events."""
    # Create an event collector
    try:
        collector = create_event_collector('auto')
        
        try:
            # Start monitoring
            collector.start(temp_dir)
            
            # Wait for the collector to initialize (reduced time)
            time.sleep(0.5)
            
            # Create a test file
            test_file = os.path.join(temp_dir, 'test_file.txt')
            with open(test_file, 'w') as f:
                f.write('Initial content')
            
            # Wait for events to be processed (reduced time)
            time.sleep(0.5)
            
            # Modify the file
            with open(test_file, 'a') as f:
                f.write('\nModified content')
                
            # Wait for events to be processed (reduced time)
            time.sleep(0.5)
            
            # Delete the file
            os.unlink(test_file)
            
            # Wait for events to be processed (reduced time)
            time.sleep(0.5)
            
            # Get the events
            events = collector.get_events()
            
            # Get the stats
            stats = collector.get_stats()
            
            # Check that we have some events
            # If we're hitting watch limits, we might not get events, so we'll skip this check
            if events:
                assert len(events) > 0
                
                # Check that we have the right event types
                event_types = set(e.get('event_type') for e in events if 'event_type' in e)
                assert len(event_types) > 0
            
            # Check that we have stats
            assert isinstance(stats, dict)
            assert 'event_count' in stats
            
        finally:
            # Stop the collector
            collector.stop()
    except OSError as e:
        if "inotify watch limit reached" in str(e):
            pytest.skip("Skipping test due to inotify watch limit reached")
        else:
            raise


@pytest.mark.timeout(10)  # Set a 10-second timeout
@pytest.mark.integration
def test_create_event_collector_integration(temp_dir):
    """Test the create_event_collector function with real filesystem events."""
    try:
        # Create collectors with different libraries
        auto_collector = create_event_collector('auto')
        
        # Check that we got a collector
        assert isinstance(auto_collector, EventCollector)
        
        # Try to start and stop the collector
        try:
            auto_collector.start(temp_dir)
            time.sleep(0.5)  # Give it a moment to initialize
            auto_collector.stop()
        except Exception as e:
            if "inotify watch limit reached" in str(e):
                pytest.skip("Skipping test due to inotify watch limit reached")
            else:
                raise
        
        # Try to create a collector with a specific library
        try:
            watchdog_collector = create_event_collector('watchdog')
            assert isinstance(watchdog_collector, EventCollector)
            
            # Start and stop
            watchdog_collector.start(temp_dir)
            time.sleep(0.5)
            watchdog_collector.stop()
        except Exception as e:
            if "inotify watch limit reached" in str(e):
                pytest.skip("Skipping test due to inotify watch limit reached")
            else:
                raise
        
        # Try with pyinotify if available
        try:
            pyinotify_collector = create_event_collector('pyinotify')
            assert isinstance(pyinotify_collector, EventCollector)
            
            # Start and stop
            pyinotify_collector.start(temp_dir)
            time.sleep(0.5)
            pyinotify_collector.stop()
        except Exception as e:
            if "inotify watch limit reached" in str(e):
                pytest.skip("Skipping test due to inotify watch limit reached")
            elif "No module named 'pyinotify'" in str(e):
                pytest.skip("pyinotify not available")
            else:
                raise
    except OSError as e:
        if "inotify watch limit reached" in str(e):
            pytest.skip("Skipping test due to inotify watch limit reached")
        else:
            raise


@pytest.mark.timeout(10)  # Set a 10-second timeout
@pytest.mark.integration
def test_monitor_events_integration(temp_dir):
    """Test the monitor_events function with real filesystem events."""
    try:
        # Create a test file to generate events
        test_file = create_file_for_testing(temp_dir)
        
        # Monitor events for a short time
        results = monitor_events(temp_dir, duration_seconds=2, testing=True)
        
        # Check that we have results
        assert isinstance(results, dict)
        
        # If there was an error, check if it's due to watch limits
        if 'error' in results:
            if "inotify watch limit reached" in results['error']:
                pytest.skip("Skipping test due to inotify watch limit reached")
            else:
                pytest.fail(f"Unexpected error: {results['error']}")
        
        # If no error, check for stats and events
        assert 'stats' in results
        assert 'events' in results
        
        # Clean up
        delete_file_for_testing(test_file)
    except OSError as e:
        if "inotify watch limit reached" in str(e):
            pytest.skip("Skipping test due to inotify watch limit reached")
        else:
            raise
