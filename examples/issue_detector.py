#!/usr/bin/env python3
"""
Script to detect common file watching issues.
"""

import os
import sys
import time
import threading
from pathlib import Path

# Add parent directory to path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_watch_diagnostics.utils.system_limits import (
    get_inotify_max_user_watches,
    get_current_inotify_watches,
    get_inotify_watch_details,
    get_filesystem_info
)
from file_watch_diagnostics.utils.event_monitor import create_event_collector
from file_watch_diagnostics.utils.watch_test import (
    create_test_file,
    modify_test_file,
    delete_test_file,
    generate_random_string
)


def check_inotify_limits():
    """Check if we're approaching inotify limits."""
    max_watches = get_inotify_max_user_watches()
    current_watches = get_current_inotify_watches()
    
    print("=== Inotify Limits Check ===")
    print(f"Max user watches: {max_watches}")
    print(f"Current watches: {current_watches}")
    
    if isinstance(max_watches, int) and isinstance(current_watches, int):
        usage_percent = (current_watches / max_watches) * 100
        print(f"Watch usage: {usage_percent:.1f}% ({current_watches}/{max_watches})")
        
        if usage_percent > 80:
            print("\n[ISSUE DETECTED] You're approaching the inotify watch limit!")
            print("This can cause file watching to miss events or stop working entirely.")
            print("\nRecommended solution:")
            print("Increase the inotify watch limit by running:")
            print("  echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p")
            return True
    
    return False


def check_filesystem_compatibility(path):
    """Check if the filesystem has compatibility issues with inotify."""
    fs_info = get_filesystem_info(path)
    
    print("\n=== Filesystem Compatibility Check ===")
    
    if isinstance(fs_info, dict):
        fs_type = fs_info.get('filesystem_type', '').lower()
        print(f"Filesystem type: {fs_type}")
        
        problematic_fs = ['nfs', 'smbfs', 'cifs', 'fuse', 'sshfs']
        
        if any(fs in fs_type for fs in problematic_fs):
            print("\n[ISSUE DETECTED] You're using a filesystem that may have limited inotify support!")
            print(f"Filesystem type '{fs_type}' can have issues with file watching.")
            print("\nRecommended solutions:")
            print("1. If possible, move your project to a local filesystem (ext4, xfs, etc.)")
            print("2. Use polling-based file watching instead of inotify")
            print("3. For NFS, check if the server supports inotify events")
            return True
    else:
        print(f"Error getting filesystem info: {fs_info}")
    
    return False


def test_event_delivery(path, duration=10):
    """Test if events are being delivered correctly."""
    print("\n=== Event Delivery Test ===")
    print(f"Testing event delivery in {path} for {duration} seconds...")
    
    # Create a test directory
    test_dir = Path(path) / f"event_test_{generate_random_string()}"
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Start event collector
        collector = create_event_collector()
        collector.start(test_dir)
        
        # Perform file operations in a separate thread
        operations = []
        
        def perform_operations():
            for i in range(5):
                # Create a file
                file_path = create_test_file(test_dir)
                operations.append(('create', str(file_path)))
                time.sleep(0.5)
                
                # Modify the file
                modify_test_file(file_path)
                operations.append(('modify', str(file_path)))
                time.sleep(0.5)
                
                # Delete the file
                delete_test_file(file_path)
                operations.append(('delete', str(file_path)))
                time.sleep(0.5)
        
        thread = threading.Thread(target=perform_operations)
        thread.daemon = True
        thread.start()
        thread.join()
        
        # Wait a bit for events to be processed
        time.sleep(2)
        
        # Stop the collector
        collector.stop()
        
        # Get events
        events = collector.get_events()
        
        # Check if all operations were detected
        print(f"Performed {len(operations)} operations")
        print(f"Detected {len(events)} events")
        
        if len(events) < len(operations):
            print("\n[ISSUE DETECTED] Some file events were not detected!")
            print(f"Expected at least {len(operations)} events, but only got {len(events)}")
            print("\nPossible causes:")
            print("1. Inotify watch limit reached")
            print("2. Filesystem doesn't fully support inotify")
            print("3. Events are being coalesced or dropped")
            print("4. System resource constraints")
            return True
    finally:
        # Clean up
        for item in test_dir.glob('*'):
            if item.is_file():
                try:
                    item.unlink()
                except:
                    pass
        try:
            test_dir.rmdir()
        except:
            pass
    
    return False


def check_resource_constraints():
    """Check for system resource constraints that might affect file watching."""
    print("\n=== Resource Constraints Check ===")
    
    import psutil
    
    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"CPU usage: {cpu_percent}%")
    
    # Check memory usage
    memory = psutil.virtual_memory()
    print(f"Memory usage: {memory.percent}% (Available: {memory.available / (1024**3):.2f} GB)")
    
    # Check for resource constraints
    issues_detected = False
    
    if cpu_percent > 90:
        print("\n[ISSUE DETECTED] High CPU usage!")
        print("This can cause file watching to miss events due to resource starvation.")
        issues_detected = True
    
    if memory.percent > 90:
        print("\n[ISSUE DETECTED] High memory usage!")
        print("This can cause file watching to miss events or fail due to resource starvation.")
        issues_detected = True
    
    # Check for high process count
    process_count = len(psutil.pids())
    print(f"Process count: {process_count}")
    
    if process_count > 500:
        print("\n[ISSUE DETECTED] High process count!")
        print("This can cause file watching to miss events due to scheduling issues.")
        issues_detected = True
    
    return issues_detected


def check_watch_distribution():
    """Check if any processes are using an excessive number of watches."""
    print("\n=== Watch Distribution Check ===")
    
    watch_details = get_inotify_watch_details()
    
    if not isinstance(watch_details, list):
        print(f"Error getting watch details: {watch_details}")
        return False
    
    if not watch_details:
        print("No processes using inotify watches found.")
        return False
    
    print("Top processes using inotify watches:")
    for i, proc in enumerate(watch_details[:10]):
        print(f"  {i+1}. PID {proc['pid']} ({proc['name']}): {proc['watch_count']} watches")
    
    # Check for processes using a lot of watches
    max_watches = get_inotify_max_user_watches()
    if isinstance(max_watches, int):
        for proc in watch_details:
            if proc['watch_count'] > max_watches * 0.2:  # Using more than 20% of available watches
                print(f"\n[ISSUE DETECTED] Process PID {proc['pid']} ({proc['name']}) is using a large number of watches!")
                print(f"This process is using {proc['watch_count']} watches, which is more than 20% of the maximum.")
                print("\nRecommended solutions:")
                print("1. Investigate why this process needs so many watches")
                print("2. Consider increasing the inotify watch limit")
                print("3. Restart the process to release watches")
                return True
    
    return False


def main():
    """Main function to detect file watching issues."""
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    print(f"File Watch Issue Detector")
    print(f"Target directory: {target_dir}")
    print("=" * 60)
    
    issues_found = False
    
    # Check inotify limits
    if check_inotify_limits():
        issues_found = True
    
    # Check filesystem compatibility
    if check_filesystem_compatibility(target_dir):
        issues_found = True
    
    # Check watch distribution
    if check_watch_distribution():
        issues_found = True
    
    # Check resource constraints
    if check_resource_constraints():
        issues_found = True
    
    # Test event delivery
    if test_event_delivery(target_dir):
        issues_found = True
    
    print("\n" + "=" * 60)
    if issues_found:
        print("Issues were detected that could affect file watching!")
        print("Review the recommendations above to resolve these issues.")
    else:
        print("No file watching issues detected!")
        print("If you're still experiencing problems, try running the full diagnostics tool:")
        print("  python file_watch_diagnostics_cli.py")


if __name__ == "__main__":
    main()
