"""
Tests for the event_monitor module.
"""

import os
import sys
import time
import pytest
import tempfile
from unittest import mock
from pathlib import Path
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_watch_diagnostics.utils.event_monitor import (
    EventCollector,
    create_event_collector,
    monitor_events
)


def test_event_collector_init():
    """Test initializing an event collector."""
    collector = EventCollector()
    assert collector.running == False
    assert collector.start_time is None
    assert collector.stop_time is None
    assert collector.events.qsize() == 0


def test_event_collector_start_stop():
    """Test starting and stopping an event collector."""
    collector = EventCollector()
    
    # Start the collector
    collector.start("/tmp")
    assert collector.running == True
    assert collector.start_time is not None
    assert collector.stop_time is None
    
    # Stop the collector
    collector.stop()
    assert collector.running == False
    assert collector.start_time is not None
    assert collector.stop_time is not None


def test_event_collector_get_events():
    """Test getting events from an event collector."""
    collector = EventCollector()
    
    # Add some events
    collector.events.put({"event": 1})
    collector.events.put({"event": 2})
    collector.events.put({"event": 3})
    
    # Get all events
    events = collector.get_events()
    assert len(events) == 3
    assert events[0]["event"] == 1
    assert events[1]["event"] == 2
    assert events[2]["event"] == 3
    
    # Queue should be empty now
    assert collector.events.qsize() == 0


def test_event_collector_get_events_with_limit():
    """Test getting events with a limit."""
    collector = EventCollector()
    
    # Add some events
    collector.events.put({"event": 1})
    collector.events.put({"event": 2})
    collector.events.put({"event": 3})
    
    # Get limited events
    events = collector.get_events(max_count=2)
    assert len(events) == 2
    assert events[0]["event"] == 1
    assert events[1]["event"] == 2
    
    # One event should remain
    assert collector.events.qsize() == 1


def test_event_collector_get_stats():
    """Test getting stats from an event collector."""
    collector = EventCollector()
    
    # Get stats before starting
    stats = collector.get_stats()
    assert stats["running"] == False
    assert stats["start_time"] is None
    assert stats["stop_time"] is None
    assert stats["duration_seconds"] is None
    assert stats["events_count"] == 0
    
    # Start the collector
    collector.start("/tmp")
    
    # Add some events
    collector.events.put({"event": 1})
    collector.events.put({"event": 2})
    
    # Get stats after starting
    stats = collector.get_stats()
    assert stats["running"] == True
    assert stats["start_time"] is not None
    assert stats["stop_time"] is None
    assert stats["duration_seconds"] is not None
    assert stats["events_count"] == 2
    
    # Stop the collector
    collector.stop()
    
    # Get stats after stopping
    stats = collector.get_stats()
    assert stats["running"] == False
    assert stats["start_time"] is not None
    assert stats["stop_time"] is not None
    assert stats["duration_seconds"] is not None
    assert stats["events_count"] == 2


def test_create_event_collector():
    """Test creating an event collector."""
    # Test with auto library selection
    with mock.patch("file_watch_diagnostics.utils.event_monitor.WATCHDOG_AVAILABLE", True):
        with mock.patch("file_watch_diagnostics.utils.event_monitor.PYINOTIFY_AVAILABLE", True):
            collector = create_event_collector()
            assert collector.__class__.__name__ == "WatchdogEventCollector"
    
    # Test with explicit library selection
    with mock.patch("file_watch_diagnostics.utils.event_monitor.WATCHDOG_AVAILABLE", True):
        collector = create_event_collector(library="watchdog")
        assert collector.__class__.__name__ == "WatchdogEventCollector"
    
    # Test with unavailable library
    with mock.patch("file_watch_diagnostics.utils.event_monitor.WATCHDOG_AVAILABLE", False):
        with mock.patch("file_watch_diagnostics.utils.event_monitor.PYINOTIFY_AVAILABLE", False):
            with pytest.raises(ImportError):
                create_event_collector()
    
    # Test with invalid library
    with pytest.raises(ValueError):
        create_event_collector(library="invalid")


def test_monitor_events():
    """Test monitoring events."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the create_event_collector function
        mock_collector = mock.MagicMock()
        mock_collector.get_stats.return_value = {"running": False}
        mock_collector.get_events.return_value = [{"event": 1}, {"event": 2}]
        
        with mock.patch("file_watch_diagnostics.utils.event_monitor.create_event_collector", return_value=mock_collector):
            # Monitor events for a short duration
            result = monitor_events(temp_dir, duration_seconds=0.1)
            
            # Check that the collector was started and stopped
            mock_collector.start.assert_called_once_with(temp_dir)
            mock_collector.stop.assert_called_once()
            
            # Check the result
            assert "stats" in result
            assert "events" in result
            assert len(result["events"]) == 2
