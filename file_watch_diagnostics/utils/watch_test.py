"""
Module for testing file watching with different libraries.
"""

import os
import time
import random
import string
import threading
import tempfile
from pathlib import Path
from datetime import datetime


def generate_random_string(length=10):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def create_file_for_testing(directory, content_size=1024):
    """Create a test file with random content."""
    filename = f"test_{generate_random_string()}.txt"
    path = Path(directory) / filename
    
    content = generate_random_string(content_size)
    
    with open(path, 'w') as f:
        f.write(content)
        
    return path


def modify_file_for_testing(path, content_size=1024):
    """Modify a test file with new random content."""
    content = generate_random_string(content_size)
    
    with open(path, 'w') as f:
        f.write(content)
        
    return path


def delete_file_for_testing(path):
    """Delete a test file."""
    os.unlink(path)


def run_watchdog_test(directory, duration_seconds=30, operation_interval=1.0):
    """Test file watching with the watchdog library."""
    try:
        import watchdog.events
        import watchdog.observers
    except ImportError:
        return {
            'status': 'error',
            'message': 'watchdog library is not available'
        }
    
    results = {
        'status': 'success',
        'events_detected': 0,
        'events_missed': 0,
        'operations': [],
        'errors': []
    }
    
    class EventHandler(watchdog.events.FileSystemEventHandler):
        def __init__(self):
            self.events = []
            self.lock = threading.Lock()
            
        def on_any_event(self, event):
            with self.lock:
                self.events.append({
                    'timestamp': datetime.now(),
                    'type': event.event_type,
                    'is_directory': event.is_directory,
                    'src_path': event.src_path,
                    'dest_path': getattr(event, 'dest_path', None)
                })
    
    # Create a temporary directory for testing
    test_dir = Path(directory) / f"watchdog_test_{generate_random_string()}"
    test_dir.mkdir(exist_ok=True)
    
    # Start the observer
    event_handler = EventHandler()
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, str(test_dir), recursive=True)
    
    start_time = datetime.now()
    observer.start()
    
    try:
        # Perform file operations
        operations_thread = threading.Thread(
            target=_perform_file_operations,
            args=(test_dir, duration_seconds, operation_interval, results)
        )
        operations_thread.daemon = True
        operations_thread.start()
        operations_thread.join()
        
        # Wait a bit for events to be processed
        time.sleep(1)
        
        # Check if all operations were detected
        with event_handler.lock:
            results['events_detected'] = len(event_handler.events)
            
            # Calculate missed events (operations without corresponding events)
            # This is a simplistic approach and might not be 100% accurate
            operation_paths = set()
            for op in results['operations']:
                if 'path' in op:
                    operation_paths.add(op['path'])
            
            event_paths = set()
            for event in event_handler.events:
                if 'src_path' in event:
                    event_paths.add(event['src_path'])
                if 'dest_path' in event and event['dest_path']:
                    event_paths.add(event['dest_path'])
            
            # Count operations that didn't have a corresponding event
            results['events_missed'] = len(operation_paths - event_paths)
            
    except Exception as e:
        results['status'] = 'error'
        results['errors'].append(str(e))
    finally:
        observer.stop()
        observer.join()
        
        # Calculate duration
        end_time = datetime.now()
        results['duration_seconds'] = (end_time - start_time).total_seconds()
        
        # Clean up test directory
        try:
            for item in test_dir.glob('*'):
                if item.is_file():
                    item.unlink()
            test_dir.rmdir()
        except Exception as e:
            results['errors'].append(f"Cleanup error: {str(e)}")
    
    return results


def run_pyinotify_test(directory, duration_seconds=30, operation_interval=1.0):
    """Test file watching with the pyinotify library."""
    try:
        import pyinotify
    except ImportError:
        return {
            'status': 'error',
            'message': 'pyinotify library is not available'
        }
    
    results = {
        'status': 'success',
        'events_detected': 0,
        'events_missed': 0,
        'operations': [],
        'errors': []
    }
    
    # Create a temporary directory for testing
    test_dir = Path(directory) / f"pyinotify_test_{generate_random_string()}"
    test_dir.mkdir(exist_ok=True)
    
    # Set up pyinotify
    wm = pyinotify.WatchManager()
    mask = pyinotify.ALL_EVENTS
    
    events = []
    events_lock = threading.Lock()
    
    class EventHandler(pyinotify.ProcessEvent):
        def process_default(self, event):
            with events_lock:
                events.append({
                    'timestamp': datetime.now(),
                    'mask': event.mask,
                    'maskname': pyinotify.EventsCodes.maskname(event.mask),
                    'path': event.path,
                    'name': event.name,
                    'pathname': event.pathname,
                    'wd': event.wd
                })
    
    handler = EventHandler()
    notifier = pyinotify.ThreadedNotifier(wm, handler)
    wm.add_watch(str(test_dir), mask, rec=True, auto_add=True)
    
    start_time = datetime.now()
    notifier.start()
    
    try:
        # Perform file operations
        operations_thread = threading.Thread(
            target=_perform_file_operations,
            args=(test_dir, duration_seconds, operation_interval, results)
        )
        operations_thread.daemon = True
        operations_thread.start()
        operations_thread.join()
        
        # Wait a bit for events to be processed
        time.sleep(1)
        
        # Check if all operations were detected
        with events_lock:
            results['events_detected'] = len(events)
            
            # Calculate missed events (operations without corresponding events)
            operation_paths = set()
            for op in results['operations']:
                if 'path' in op:
                    operation_paths.add(op['path'])
            
            event_paths = set()
            for event in events:
                if 'pathname' in event:
                    event_paths.add(event['pathname'])
            
            # Count operations that didn't have a corresponding event
            results['events_missed'] = len(operation_paths - event_paths)
            
    except Exception as e:
        results['status'] = 'error'
        results['errors'].append(str(e))
    finally:
        notifier.stop()
        
        # Calculate duration
        end_time = datetime.now()
        results['duration_seconds'] = (end_time - start_time).total_seconds()
        
        # Clean up test directory
        try:
            for item in test_dir.glob('*'):
                if item.is_file():
                    item.unlink()
            test_dir.rmdir()
        except Exception as e:
            results['errors'].append(f"Cleanup error: {str(e)}")
    
    return results


def run_all_library_tests(directory, duration_seconds=30, operation_interval=1.0):
    """Test file watching with all available libraries."""
    results = {}
    
    # Test watchdog
    try:
        results['watchdog'] = run_watchdog_test(directory, duration_seconds, operation_interval)
    except Exception as e:
        results['watchdog'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # Test pyinotify
    try:
        results['pyinotify'] = run_pyinotify_test(directory, duration_seconds, operation_interval)
    except Exception as e:
        results['pyinotify'] = {
            'status': 'error',
            'message': str(e)
        }
    
    return results


def _perform_file_operations(directory, duration_seconds, interval, results):
    """Perform various file operations for testing."""
    start_time = time.time()
    end_time = start_time + duration_seconds
    
    while time.time() < end_time:
        try:
            # Create a file
            path = create_file_for_testing(directory)
            results['operations'].append({
                'timestamp': datetime.now(),
                'type': 'create',
                'path': str(path)
            })
            
            # Wait a bit
            time.sleep(interval)
            
            # Modify the file
            modify_file_for_testing(path)
            results['operations'].append({
                'timestamp': datetime.now(),
                'type': 'modify',
                'path': str(path)
            })
            
            # Wait a bit
            time.sleep(interval)
            
            # Delete the file
            delete_file_for_testing(path)
            results['operations'].append({
                'timestamp': datetime.now(),
                'type': 'delete',
                'path': str(path)
            })
            
            # Wait a bit
            time.sleep(interval)
            
        except Exception as e:
            results['errors'].append(f"Operation error: {str(e)}")


if __name__ == "__main__":
    import sys
    import json
    
    directory = sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir()
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    print(f"Testing file watching in {directory} for {duration} seconds...")
    results = run_all_library_tests(directory, duration)
    
    print(json.dumps(results, indent=2, default=str))
