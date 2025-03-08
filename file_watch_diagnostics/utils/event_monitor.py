"""
Module for monitoring file system events.
"""

import time
import threading
from pathlib import Path
from datetime import datetime
from queue import Queue, Empty

# Import different file watching libraries
try:
    import watchdog.events
    import watchdog.observers
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

try:
    import pyinotify
    PYINOTIFY_AVAILABLE = True
except ImportError:
    PYINOTIFY_AVAILABLE = False


class EventCollector:
    """Base class for collecting file system events."""
    
    def __init__(self, max_events=1000):
        self.events = Queue(maxsize=max_events)
        self.running = False
        self.start_time = None
        self.stop_time = None
    
    def start(self, path):
        """Start monitoring events."""
        self.running = True
        self.start_time = datetime.now()
    
    def stop(self):
        """Stop monitoring events."""
        self.running = False
        self.stop_time = datetime.now()
    
    def get_events(self, max_count=None):
        """Get collected events."""
        events = []
        count = 0
        
        while not self.events.empty():
            if max_count is not None and count >= max_count:
                break
            
            try:
                event = self.events.get_nowait()
                events.append(event)
                count += 1
            except Empty:
                break
        
        return events
    
    def get_stats(self):
        """Get statistics about the monitoring session."""
        if self.start_time is None:
            return {'status': 'not_started'}
        
        if self.stop_time is None:
            duration = (datetime.now() - self.start_time).total_seconds()
            status = 'running'
        else:
            duration = (self.stop_time - self.start_time).total_seconds()
            status = 'stopped'
        
        events = self.get_events()
        event_count = len(events)
        
        # Calculate average latency if events have timestamps
        latencies = []
        for event in events:
            if isinstance(event, dict) and 'timestamp' in event and 'created_at' in event:
                latency = (event['timestamp'] - event['created_at']).total_seconds() * 1000
                latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return {
            'status': status,
            'duration_seconds': duration,
            'event_count': event_count,
            'avg_latency_ms': avg_latency
        }


class WatchdogEventHandler(watchdog.events.FileSystemEventHandler):
    """Event handler for watchdog events."""
    
    def __init__(self, collector):
        self.collector = collector
    
    def on_any_event(self, event):
        """Handle any file system event."""
        if not self.collector.running:
            return
        
        self.collector.events.put({
            'event_type': event.event_type,
            'src_path': event.src_path,
            'is_directory': event.is_directory,
            'timestamp': datetime.now(),
            'created_at': datetime.now()
        })


class WatchdogEventCollector(EventCollector):
    """Event collector using the watchdog library."""
    
    def __init__(self, max_events=1000):
        super().__init__(max_events)
        self.observer = None
    
    def start(self, path):
        """Start monitoring events with watchdog."""
        super().start(path)
        
        self.observer = watchdog.observers.Observer()
        event_handler = WatchdogEventHandler(self)
        self.observer.schedule(event_handler, path, recursive=True)
        self.observer.start()
    
    def stop(self):
        """Stop monitoring events."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        super().stop()


class PyinotifyEventHandler(pyinotify.ProcessEvent):
    """Event handler for pyinotify events."""
    
    def __init__(self, collector):
        self.collector = collector
    
    def process_default(self, event):
        """Process any event."""
        if not self.collector.running:
            return
        
        # Map pyinotify masks to event types
        event_type_map = {
            pyinotify.IN_CREATE: 'created',
            pyinotify.IN_DELETE: 'deleted',
            pyinotify.IN_MODIFY: 'modified',
            pyinotify.IN_MOVED_FROM: 'moved',
            pyinotify.IN_MOVED_TO: 'moved'
        }
        
        # Determine event type
        event_type = 'unknown'
        for mask, type_name in event_type_map.items():
            if event.mask & mask:
                event_type = type_name
                break
        
        self.collector.events.put({
            'event_type': event_type,
            'src_path': event.pathname,
            'is_directory': bool(event.mask & pyinotify.IN_ISDIR),
            'timestamp': datetime.now(),
            'created_at': datetime.now()
        })


class PyinotifyEventCollector(EventCollector):
    """Event collector using the pyinotify library."""
    
    def __init__(self, max_events=1000):
        super().__init__(max_events)
        self.watch_manager = None
        self.notifier = None
        self.thread = None
    
    def start(self, path):
        """Start monitoring events with pyinotify."""
        super().start(path)
        
        self.watch_manager = pyinotify.WatchManager()
        handler = PyinotifyEventHandler(self)
        self.notifier = pyinotify.Notifier(self.watch_manager, handler)
        
        # Monitor all events
        mask = (pyinotify.IN_CREATE | pyinotify.IN_DELETE | 
                pyinotify.IN_MODIFY | pyinotify.IN_MOVED_FROM | 
                pyinotify.IN_MOVED_TO)
        
        self.watch_manager.add_watch(path, mask, rec=True, auto_add=True)
        
        # Start notifier in a separate thread
        self.thread = threading.Thread(target=self._run_notifier)
        self.thread.daemon = True
        self.thread.start()
    
    def _run_notifier(self):
        """Run the notifier in a loop."""
        while self.running:
            self.notifier.process_events()
            if self.notifier.check_events(timeout=1000):
                self.notifier.read_events()
    
    def stop(self):
        """Stop monitoring events."""
        super().stop()
        
        if self.thread:
            self.thread.join(1)  # Wait for thread to finish with timeout


def create_event_collector(library='auto', max_events=1000):
    """Create an event collector using the specified library."""
    if library == 'auto':
        if WATCHDOG_AVAILABLE:
            return WatchdogEventCollector(max_events)
        elif PYINOTIFY_AVAILABLE:
            return PyinotifyEventCollector(max_events)
        else:
            raise ImportError("No file watching library available")
    elif library == 'watchdog' and WATCHDOG_AVAILABLE:
        return WatchdogEventCollector(max_events)
    elif library == 'pyinotify' and PYINOTIFY_AVAILABLE:
        return PyinotifyEventCollector(max_events)
    else:
        raise ValueError(f"Unsupported library: {library}")


def monitor_events(path, duration_seconds=5, library='auto', max_events=100, testing=False):
    """Monitor file system events in a directory.
    
    Args:
        path: Path to monitor
        duration_seconds: Duration to monitor in seconds
        library: Library to use ('auto', 'watchdog', 'pyinotify')
        max_events: Maximum number of events to collect
        testing: If True, use a shorter duration for testing (1 second)
    
    Returns:
        Dictionary with stats and events
    """
    try:
        collector = create_event_collector(library, max_events)
        collector.start(path)
        
        # Use a shorter duration for testing
        actual_duration = 1 if testing else duration_seconds
        
        try:
            time.sleep(actual_duration)
        finally:
            collector.stop()
        
        return {
            'stats': collector.get_stats(),
            'events': collector.get_events()
        }
    except Exception as e:
        return {
            'error': str(e)
        }


if __name__ == "__main__":
    import sys
    import json
    
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print(f"Monitoring events in {path} for {duration} seconds...")
    result = monitor_events(path, duration)
    
    print(json.dumps(result, indent=2, default=str))
