"""
Main module for file watch diagnostics.
"""

import os
import sys
import json
import time
import logging
import platform
import psutil
from datetime import datetime
from pathlib import Path

from .utils.system_limits import check_system_limits, get_filesystem_info
from .utils.event_monitor import monitor_events
from .utils.watch_test import run_all_library_tests
from .utils.logging_utils import setup_logger, get_console, get_progress, create_log_filename


class FileWatchDiagnostics:
    """Main class for file watch diagnostics."""
    
    def __init__(self, target_dir=None, log_dir=None, log_level="INFO"):
        """Initialize the diagnostics tool."""
        self.target_dir = Path(target_dir or os.getcwd()).resolve()
        self.log_dir = log_dir
        
        # Create log file
        self.log_file = create_log_filename(self.log_dir)
        
        # Set up logger
        log_level_num = getattr(logging, log_level.upper(), logging.INFO)
        self.logger = setup_logger("file_watch_diagnostics", self.log_file, log_level_num)
        
        # Set up rich console if available
        self.console = get_console()
        self.progress = get_progress()
        
        # Results dictionary
        self.results = {
            'timestamp': datetime.now(),
            'target_directory': str(self.target_dir),
            'system_info': {},
            'system_limits': {},
            'filesystem_info': {},
            'event_monitoring': {},
            'library_tests': {}
        }
        
        # Initialize results file path
        self.results_file = None
    
    def run_all_diagnostics(self):
        """Run all diagnostic tests."""
        self._log_header("Starting File Watch Diagnostics")
        self._log_info(f"Target directory: {self.target_dir}")
        self._log_info(f"Log file: {self.log_file}")
        
        # Check system information
        self._run_system_info_check()
        
        # Check system limits
        self._run_system_limits_check()
        
        # Check filesystem information
        self._run_filesystem_info_check()
        
        # Monitor events
        self._run_event_monitoring()
        
        # Test file watching libraries
        self._run_library_tests()
        
        # Save results
        self._save_results()
        
        self._log_header("Diagnostics Complete")
        self._log_info(f"Results saved to: {self.results_file}")
        
        return self.results
    
    def _run_system_info_check(self):
        """Check system information."""
        self._log_header("Checking System Information")
        
        import platform
        import psutil
        
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'processor': platform.processor(),
            'cpu_count': os.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'memory_available_gb': psutil.virtual_memory().available / (1024**3)
        }
        
        self._log_info(f"Platform: {system_info['platform']}")
        self._log_info(f"Python version: {system_info['python_version']}")
        self._log_info(f"CPU count: {system_info['cpu_count']}")
        self._log_info(f"Memory total: {system_info['memory_total_gb']:.2f} GB")
        self._log_info(f"Memory available: {system_info['memory_available_gb']:.2f} GB")
        
        self.results['system_info'] = system_info
    
    def _run_system_limits_check(self):
        """Check system limits related to file watching."""
        self._log_header("Checking System Limits")
        
        system_limits = check_system_limits()
        
        self._log_info(f"Max user watches: {system_limits['max_user_watches']}")
        self._log_info(f"Max user instances: {system_limits['max_user_instances']}")
        self._log_info(f"Max queued events: {system_limits['max_queued_events']}")
        self._log_info(f"Current watches: {system_limits['current_watches']}")
        
        if isinstance(system_limits['watch_details'], list):
            self._log_info(f"Top processes using inotify watches:")
            for i, proc in enumerate(system_limits['watch_details'][:5]):
                self._log_info(f"  {i+1}. PID {proc['pid']} ({proc['name']}): {proc['watch_count']} watches")
        
        self.results['system_limits'] = system_limits
    
    def _run_filesystem_info_check(self):
        """Check filesystem information."""
        self._log_header("Checking Filesystem Information")
        
        filesystem_info = get_filesystem_info(self.target_dir)
        
        if isinstance(filesystem_info, dict):
            self._log_info(f"Filesystem type: {filesystem_info['filesystem_type']}")
            self._log_info(f"Total space: {filesystem_info['total_space_gb']:.2f} GB")
            self._log_info(f"Free space: {filesystem_info['free_space_gb']:.2f} GB")
            self._log_info(f"Inodes total: {filesystem_info['inodes_total']}")
            self._log_info(f"Inodes free: {filesystem_info['inodes_free']}")
            self._log_info(f"Max filename length: {filesystem_info['max_filename_length']}")
        else:
            self._log_error(f"Error getting filesystem info: {filesystem_info}")
        
        self.results['filesystem_info'] = filesystem_info
    
    def _run_event_monitoring(self):
        """Monitor file system events."""
        self._log_header("Monitoring File System Events")
        
        duration = 10  # seconds
        self._log_info(f"Monitoring events for {duration} seconds...")
        
        # Monitor with watchdog
        try:
            self._log_info("Using watchdog library...")
            watchdog_results = monitor_events(self.target_dir, duration, 'watchdog')
            self._log_info(f"Collected {len(watchdog_results['events'])} events")
            self.results['event_monitoring']['watchdog'] = watchdog_results
        except ImportError:
            self._log_warning("watchdog library is not available")
            self.results['event_monitoring']['watchdog'] = {
                'status': 'error',
                'message': 'watchdog library is not available'
            }
        except Exception as e:
            self._log_error(f"Error monitoring with watchdog: {str(e)}")
            self.results['event_monitoring']['watchdog'] = {
                'status': 'error',
                'message': str(e)
            }
        
        # Monitor with pyinotify
        try:
            self._log_info("Using pyinotify library...")
            pyinotify_results = monitor_events(self.target_dir, duration, 'pyinotify')
            self._log_info(f"Collected {len(pyinotify_results['events'])} events")
            self.results['event_monitoring']['pyinotify'] = pyinotify_results
        except ImportError:
            self._log_warning("pyinotify library is not available")
            self.results['event_monitoring']['pyinotify'] = {
                'status': 'error',
                'message': 'pyinotify library is not available'
            }
        except Exception as e:
            self._log_error(f"Error monitoring with pyinotify: {str(e)}")
            self.results['event_monitoring']['pyinotify'] = {
                'status': 'error',
                'message': str(e)
            }
    
    def _run_library_tests(self):
        """Test file watching libraries."""
        self._log_header("Testing File Watching Libraries")
        
        duration = 20  # seconds
        self._log_info(f"Running tests for {duration} seconds...")
        
        library_tests = run_all_library_tests(self.target_dir, duration)
        
        for library, results in library_tests.items():
            if results['status'] == 'success':
                self._log_info(f"{library}: Detected {results['events_detected']} events, missed {results['events_missed']} events")
            else:
                self._log_warning(f"{library}: {results.get('message', 'Unknown error')}")
        
        self.results['library_tests'] = library_tests
    
    def _save_results(self):
        """Save results to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"file_watch_diagnostics_{timestamp}.json"
        
        if self.log_dir:
            path = Path(self.log_dir) / filename
        else:
            path = Path(filename)
        
        with open(path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.results_file = str(path)
    
    def _log_header(self, message):
        """Log a header message."""
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info(message)
        self.logger.info("=" * 80)
        
        if self.console:
            self.console.print(f"\n[bold cyan]{message}[/bold cyan]")
    
    def _log_info(self, message):
        """Log an info message."""
        self.logger.info(message)
        
        if self.console:
            self.console.print(f"[green]INFO:[/green] {message}")
    
    def _log_warning(self, message):
        """Log a warning message."""
        self.logger.warning(message)
        
        if self.console:
            self.console.print(f"[yellow]WARNING:[/yellow] {message}")
    
    def _log_error(self, message):
        """Log an error message."""
        self.logger.error(message)
        
        if self.console:
            self.console.print(f"[bold red]ERROR:[/bold red] {message}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="File Watch Diagnostics Tool")
    parser.add_argument("directory", nargs="?", default=None, 
                        help="Directory to monitor (default: current directory)")
    parser.add_argument("--log-dir", "-l", default=None,
                        help="Directory to store log files (default: current directory)")
    parser.add_argument("--log-level", "-v", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Log level (default: INFO)")
    
    args = parser.parse_args()
    
    diagnostics = FileWatchDiagnostics(args.directory, args.log_dir, args.log_level)
    diagnostics.run_all_diagnostics()


if __name__ == "__main__":
    import argparse
    main()
