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
                events.append(self.events.get_nowait())
                count += 1
            except Empty:
                break
                
        return events
    
    def get_stats(self):
        """Get statistics about the monitoring session."""
        duration = None
        if self.start_time:
            end_time = self.stop_time if self.stop_time else datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
        return {
            'running': self.running,
            'start_time': self.start_time,
            'stop_time': self.stop_time,
            'duration_seconds': duration,
            'events_count': self.events.qsize()
        }


class WatchdogEventCollector(EventCollector):
    """Event collector using the watchdog library."""
    
    def __init__(self, max_events=1000):
        super().__init__(max_events)
        self.observer = None
        
    def start(self, path):
        """Start monitoring events with watchdog."""
        if not WATCHDOG_AVAILABLE:
            raise ImportError("watchdog library is not available")
            
        super().start(path)
        
        class EventHandler(watchdog.events.FileSystemEventHandler):
            def __init__(self, collector):
                self.collector = collector
                
            def on_any_event(self, event):
                if not self.collector.running:
                    return
                    
                self.collector.events.put({
                    'timestamp': datetime.now(),
                    'type': event.event_type,
                    'is_directory': event.is_directory,
                    'src_path': event.src_path,
                    'dest_path': getattr(event, 'dest_path', None)
                })
        
        path = Path(path)
        self.observer = watchdog.observers.Observer()
        self.observer.schedule(EventHandler(self), path, recursive=True)
        self.observer.start()
    
    def stop(self):
        """Stop monitoring events."""
        super().stop()
        if self.observer:
            self.observer.stop()
            self.observer.join()


class PyinotifyEventCollector(EventCollector):
    """Event collector using the pyinotify library."""
    
    def __init__(self, max_events=1000):
        super().__init__(max_events)
        self.watch_manager = None
        self.notifier = None
        self.thread = None
        
    def start(self, path):
        """Start monitoring events with pyinotify."""
        if not PYINOTIFY_AVAILABLE:
            raise ImportError("pyinotify library is not available")
            
        super().start(path)
        
        self.watch_manager = pyinotify.WatchManager()
        
        class EventHandler(pyinotify.ProcessEvent):
            def __init__(self, collector):
                self.collector = collector
                
            def process_default(self, event):
                if not self.collector.running:
                    return
                    
                self.collector.events.put({
                    'timestamp': datetime.now(),
                    'mask': event.mask,
                    'maskname': pyinotify.EventsCodes.maskname(event.mask),
                    'path': event.path,
                    'name': event.name,
                    'pathname': event.pathname,
                    'wd': event.wd,
                    'dir': bool(event.mask & pyinotify.IN_ISDIR)
                })
        
        # Monitor all events
        mask = pyinotify.ALL_EVENTS
        self.watch_manager.add_watch(path, mask, rec=True, auto_add=True)
        
        self.notifier = pyinotify.Notifier(self.watch_manager, EventHandler(self))
        
        # Run the notifier in a separate thread
        self.thread = threading.Thread(target=self._run_notifier)
        self.thread.daemon = True
        self.thread.start()
    
    def _run_notifier(self):
        """Run the notifier in a loop."""
        while self.running:
            try:
                self.notifier.process_events()
                if self.notifier.check_events(timeout=1000):
                    self.notifier.read_events()
            except Exception as e:
                print(f"Error in pyinotify: {e}")
                break
    
    def stop(self):
        """Stop monitoring events."""
        super().stop()
        if self.thread and self.thread.is_alive():
            self.running = False
            self.thread.join(timeout=2)


def create_event_collector(library='auto', max_events=1000):
    """Create an event collector using the specified library."""
    if library == 'auto':
        if WATCHDOG_AVAILABLE:
            return WatchdogEventCollector(max_events)
        elif PYINOTIFY_AVAILABLE:
            return PyinotifyEventCollector(max_events)
        else:
            raise ImportError("No file watching library available")
    elif library == 'watchdog':
        return WatchdogEventCollector(max_events)
    elif library == 'pyinotify':
        return PyinotifyEventCollector(max_events)
    else:
        raise ValueError(f"Unsupported library: {library}")


def monitor_events(path, duration_seconds=10, library='auto', max_events=1000):
    """Monitor file system events for the specified duration."""
    collector = create_event_collector(library, max_events)
    collector.start(path)
    
    try:
        time.sleep(duration_seconds)
    finally:
        collector.stop()
    
    return {
        'stats': collector.get_stats(),
        'events': collector.get_events()
    }


if __name__ == "__main__":
    import sys
    import json
    
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    print(f"Monitoring events in {path} for {duration} seconds...")
    result = monitor_events(path, duration)
    
    print(json.dumps(result, indent=2, default=str))
