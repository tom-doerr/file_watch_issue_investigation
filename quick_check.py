#!/usr/bin/env python3
"""
Quick check script for file watching issues.
"""

import os
import sys
import time
import argparse
import tempfile
import json
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file_watch_diagnostics.utils.system_limits import (
    get_inotify_max_user_watches,
    get_current_inotify_watches,
    get_inotify_watch_details,
    get_filesystem_info,
    get_filesystem_type
)
from file_watch_diagnostics.utils.event_monitor import create_event_collector
from file_watch_diagnostics.utils.watch_test import (
    create_file_for_testing,
    modify_file_for_testing,
    delete_file_for_testing
)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Quick check for file watching issues")
    parser.add_argument("--directory", "-d", type=str, default=os.getcwd(),
                        help="Directory to check (default: current directory)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    return parser.parse_args()


def check_system_limits():
    """Check system limits related to file watching."""
    max_watches = get_inotify_max_user_watches()
    current_watches = get_current_inotify_watches()
    
    result = {
        "max_watches": max_watches,
        "current_watches": current_watches,
        "status": "ok"
    }
    
    if isinstance(max_watches, str) and "Error" in max_watches:
        result["status"] = "error"
        result["message"] = max_watches
    elif isinstance(current_watches, str) and "Error" in current_watches:
        result["status"] = "error"
        result["message"] = current_watches
    elif isinstance(max_watches, int) and isinstance(current_watches, int):
        if current_watches >= max_watches * 0.9:
            result["status"] = "warning"
            result["message"] = f"Using {current_watches}/{max_watches} watches (>90%)"
        elif current_watches >= max_watches * 0.7:
            result["status"] = "warning"
            result["message"] = f"Using {current_watches}/{max_watches} watches (>70%)"
    
    return result


def check_filesystem_compatibility(directory=None):
    """Check if the filesystem is compatible with inotify."""
    directory = directory or os.getcwd()
    fs_type = get_filesystem_type(directory)
    
    result = {
        "filesystem_type": fs_type,
        "status": "ok"
    }
    
    if isinstance(fs_type, str) and "Error" in fs_type:
        result["status"] = "error"
        result["message"] = fs_type
    elif fs_type in ["nfs", "cifs", "smbfs", "sshfs", "fuse"]:
        result["status"] = "warning"
        result["message"] = f"Filesystem type '{fs_type}' may have limited inotify support"
    
    return result


def check_resource_constraints():
    """Check for resource constraints that might affect file watching."""
    import psutil
    
    result = {
        "status": "ok"
    }
    
    # Check memory usage
    memory = psutil.virtual_memory()
    result["memory_percent"] = memory.percent
    
    if memory.percent > 90:
        result["status"] = "warning"
        result["message"] = f"High memory usage ({memory.percent}%)"
    
    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=0.5)
    result["cpu_percent"] = cpu_percent
    
    if cpu_percent > 90:
        if result["status"] == "warning":
            result["message"] += f", high CPU usage ({cpu_percent}%)"
        else:
            result["status"] = "warning"
            result["message"] = f"High CPU usage ({cpu_percent}%)"
    
    return result


def check_event_delivery(directory=None):
    """Check if file events are being delivered correctly."""
    directory = directory or os.getcwd()
    
    with tempfile.TemporaryDirectory(dir=directory) as temp_dir:
        # Create an event collector directly
        event_collector = create_event_collector()
        event_collector.start(temp_dir)
        
        # Perform file operations
        time.sleep(1)  # Give the monitor time to start
        
        try:
            # Create a file
            test_file = create_file_for_testing(temp_dir)
            time.sleep(0.5)
            
            # Modify the file
            modify_file_for_testing(test_file)
            time.sleep(0.5)
            
            # Delete the file
            delete_file_for_testing(test_file)
            time.sleep(0.5)
            
        except Exception as e:
            event_collector.stop()
            return {
                "status": "error",
                "message": f"Error during file operations: {str(e)}"
            }
        
        # Wait for events to be processed
        time.sleep(2)
        
        # Stop the collector and get events
        event_collector.stop()
        events = event_collector.get_events()
        
        result = {
            "events_detected": len(events),
            "status": "ok"
        }
        
        if len(events) < 3:  # We should have at least 3 events (create, modify, delete)
            result["status"] = "warning"
            result["message"] = f"Only detected {len(events)} events, expected at least 3"
        
        return result


def run_quick_check(directory=None):
    """Run all quick checks."""
    directory = directory or os.getcwd()
    
    results = {
        "directory": directory,
        "system_limits": check_system_limits(),
        "filesystem_compatibility": check_filesystem_compatibility(directory),
        "resource_constraints": check_resource_constraints(),
        "event_delivery": check_event_delivery(directory)
    }
    
    # Determine overall status
    if any(r["status"] == "error" for r in results.values() if isinstance(r, dict) and "status" in r):
        results["status"] = "error"
    elif any(r["status"] == "warning" for r in results.values() if isinstance(r, dict) and "status" in r):
        results["status"] = "warning"
    else:
        results["status"] = "ok"
    
    return results


def main():
    """Main entry point."""
    args = parse_args()
    
    print(f"Running quick check in {args.directory}...")
    
    results = run_quick_check(args.directory)
    
    print("\nResults:")
    print(f"  System Limits: {results['system_limits']['status'].upper()}")
    if results['system_limits']['status'] != "ok":
        print(f"    - {results['system_limits'].get('message', 'Unknown issue')}")
    
    print(f"  Filesystem Compatibility: {results['filesystem_compatibility']['status'].upper()}")
    if results['filesystem_compatibility']['status'] != "ok":
        print(f"    - {results['filesystem_compatibility'].get('message', 'Unknown issue')}")
    
    print(f"  Resource Constraints: {results['resource_constraints']['status'].upper()}")
    if results['resource_constraints']['status'] != "ok":
        print(f"    - {results['resource_constraints'].get('message', 'Unknown issue')}")
    
    print(f"  Event Delivery: {results['event_delivery']['status'].upper()}")
    if results['event_delivery']['status'] != "ok":
        print(f"    - {results['event_delivery'].get('message', 'Unknown issue')}")
    
    print(f"\nOverall Status: {results['status'].upper()}")
    
    if args.verbose:
        print("\nDetailed Results:")
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
