#!/usr/bin/env python3
"""
Example script demonstrating basic usage of the file_watch_diagnostics package.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_watch_diagnostics.diagnostics import FileWatchDiagnostics
from file_watch_diagnostics.utils.system_limits import check_system_limits
from file_watch_diagnostics.utils.event_monitor import monitor_events


def run_quick_diagnostics():
    """Run a quick diagnostic check."""
    print("Running quick system limits check...")
    limits = check_system_limits()
    
    print(f"Max user watches: {limits['max_user_watches']}")
    print(f"Current watches: {limits['current_watches']}")
    
    if isinstance(limits['watch_details'], list) and limits['watch_details']:
        print("\nTop processes using inotify watches:")
        for i, proc in enumerate(limits['watch_details'][:5]):
            print(f"  {i+1}. PID {proc['pid']} ({proc['name']}): {proc['watch_count']} watches")
    
    # Check if we're approaching the limit
    if isinstance(limits['max_user_watches'], int) and isinstance(limits['current_watches'], int):
        usage_percent = (limits['current_watches'] / limits['max_user_watches']) * 100
        print(f"\nWatch usage: {usage_percent:.1f}% ({limits['current_watches']}/{limits['max_user_watches']})")
        
        if usage_percent > 80:
            print("WARNING: You're approaching the inotify watch limit!")
            print("Consider increasing the limit by running:")
            print("  echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p")


def monitor_directory_events(directory, duration=5):
    """Monitor events in a directory for a short duration."""
    print(f"\nMonitoring events in {directory} for {duration} seconds...")
    
    try:
        results = monitor_events(directory, duration)
        
        print(f"Detected {len(results['events'])} events:")
        for i, event in enumerate(results['events'][:10]):
            if i >= 5:
                print("  ...")
                break
                
            event_type = event.get('type', event.get('maskname', 'unknown'))
            path = event.get('src_path', event.get('pathname', 'unknown'))
            print(f"  {i+1}. {event_type}: {path}")
    except ImportError as e:
        print(f"Error: {e}")
        print("Make sure you have watchdog or pyinotify installed.")


def run_full_diagnostics(directory):
    """Run full diagnostics on a directory."""
    print(f"\nRunning full diagnostics on {directory}...")
    
    diagnostics = FileWatchDiagnostics(directory)
    results = diagnostics.run_all_diagnostics()
    
    print(f"\nDiagnostics complete. Results saved to: {diagnostics.results_file}")
    
    return results


if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    print(f"File Watch Diagnostics Example")
    print(f"Target directory: {target_dir}")
    
    # Run quick diagnostics
    run_quick_diagnostics()
    
    # Monitor events
    monitor_directory_events(target_dir)
    
    # Run full diagnostics with a flag
    if len(sys.argv) > 2 and sys.argv[2].lower() in ('--full', '-f'):
        run_full_diagnostics(target_dir)
    else:
        print("\nTo run full diagnostics, add the --full flag:")
        print(f"  python {sys.argv[0]} [directory] --full")
