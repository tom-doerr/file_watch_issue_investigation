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
    
    def __init__(self, target_dir=None, log_dir=None, log_level="INFO", testing_mode=False):
        """Initialize the diagnostics tool.
        
        Args:
            target_dir: Directory to monitor
            log_dir: Directory to store logs
            log_level: Logging level
            testing_mode: If True, use shorter wait times for testing
        """
        self.target_dir = Path(target_dir or os.getcwd()).resolve()
        self.log_dir = log_dir
        self.testing_mode = testing_mode
        
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
        
        self._log_info(f"Max user watches: {system_limits.get('max_user_watches', 'Unknown')}")
        self._log_info(f"Max user instances: {system_limits.get('max_user_instances', 'Unknown')}")
        self._log_info(f"Max queued events: {system_limits.get('max_queued_events', 'Unknown')}")
        self._log_info(f"Current watches: {system_limits.get('current_watches', 'Unknown')}")
        
        if system_limits.get('watch_per_process'):
            self._log_info("Top processes by watch count:")
            for proc in system_limits['watch_per_process'][:5]:
                self._log_info(f"  {proc['name']} (PID {proc['pid']}): {proc['watches']} watches")
        
        self.results['system_limits'] = system_limits
    
    def _run_filesystem_info_check(self):
        """Check filesystem information."""
        self._log_header("Checking Filesystem Information")
        
        filesystem_info = get_filesystem_info(self.target_dir)
        
        self._log_info(f"Directory: {self.target_dir}")
        
        if isinstance(filesystem_info, dict):
            self._log_info(f"Filesystem type: {filesystem_info.get('filesystem_type', 'Unknown')}")
            self._log_info(f"Total space: {filesystem_info.get('total_space_gb', 0):.2f} GB")
            self._log_info(f"Free space: {filesystem_info.get('free_space_gb', 0):.2f} GB")
            self._log_info(f"Inodes total: {filesystem_info.get('inodes_total', 'Unknown')}")
            self._log_info(f"Inodes free: {filesystem_info.get('inodes_free', 'Unknown')}")
            
            # Check if filesystem is compatible with inotify
            fs_type = filesystem_info.get('filesystem_type', '').lower()
            incompatible_fs = ['nfs', 'cifs', 'smbfs', 'ncpfs', 'afs']
            if any(fs in fs_type for fs in incompatible_fs):
                self._log_warning(f"Filesystem {fs_type} may not be fully compatible with inotify")
        else:
            self._log_warning(f"Error getting filesystem info: {filesystem_info}")
        
        self.results['filesystem_info'] = filesystem_info
    
    def _run_event_monitoring(self):
        """Monitor file system events."""
        self._log_section_header("Monitoring File System Events")
        
        self._log_info("Creating and modifying test files to generate events...")
        
        # Check if we're running in a test environment
        testing_mode = self.testing_mode or 'pytest' in sys.modules
        
        event_results = monitor_events(self.target_dir, testing=testing_mode)
        
        # Check if there was an error
        if 'error' in event_results:
            self._log_warning(f"Error monitoring events: {event_results['error']}")
            event_summary = {
                'status': 'error',
                'message': str(event_results['error']),
                'events_detected': 0,
                'event_types': None,
                'avg_latency_ms': 0.0
            }
        else:
            # Get the stats
            stats = event_results.get('stats', {})
            events = event_results.get('events', [])
            
            # Calculate summary
            event_count = stats.get('event_count', 0)
            event_types = list(set(e.get('event_type') for e in events if 'event_type' in e))
            avg_latency = stats.get('avg_latency_ms', 0.0)
            
            # Log the results
            self._log_info(f"Events detected: {event_count}")
            self._log_info(f"Event types: {event_types if event_types else None}")
            self._log_info(f"Event latency (avg): {avg_latency:.2f} ms")
            
            if event_count == 0:
                self._log_warning("No events were detected. This may indicate a problem with file watching.")
                
            event_summary = {
                'status': 'warning' if event_count == 0 else 'ok',
                'events_detected': event_count,
                'event_types': event_types,
                'avg_latency_ms': avg_latency
            }
        
        # Store the results
        self.results['event_monitoring'] = event_summary
    
    def _run_library_tests(self):
        """Run tests with different file watching libraries."""
        self._log_section_header("Testing File Watching Libraries")
        
        # Use shorter duration for testing
        duration = 5 if self.testing_mode else 30
        interval = 0.5 if self.testing_mode else 1.0
        
        # Run the tests
        try:
            library_results = run_all_library_tests(self.target_dir, duration_seconds=duration, operation_interval=interval)
            
            # Log the results
            for library, result in library_results.items():
                status = result.get('status', 'unknown')
                message = result.get('message', '')
                
                if status == 'ok':
                    self._log_info(f"{library}: {message or 'OK'}")
                elif status == 'error':
                    self._log_warning(f"{library}: {message or 'Error'}")
                else:
                    self._log_info(f"{library}: {status} - {message}")
            
            # Store the results
            self.results['library_tests'] = library_results
            
            return library_results
        except Exception as e:
            self._log_warning(f"Error running library tests: {str(e)}")
            self.results['library_tests'] = {
                'status': 'error',
                'message': str(e)
            }
            return self.results['library_tests']
    
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
    
    def save_results(self, output_file=None):
        """Save results to a JSON file.
        
        Args:
            output_file: Optional path to save results to. If not provided,
                         a default filename will be generated.
        
        Returns:
            The path to the saved file.
        """
        if output_file:
            path = Path(output_file)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"file_watch_diagnostics_{timestamp}.json"
            
            if self.log_dir:
                path = Path(self.log_dir) / filename
            else:
                path = Path(filename)
        
        with open(path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.results_file = str(path)
        return self.results_file
    
    def _log_header(self, message):
        """Log a header message."""
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info(message)
        self.logger.info("=" * 80)
        
        if self.console:
            self.console.print(f"\n[bold cyan]{message}[/bold cyan]")
    
    def _log_section_header(self, message):
        """Log a section header."""
        separator = "=" * 70
        self.logger.info(separator)
        self.logger.info(message)
        self.logger.info(separator)
        
        if self.console:
            self.console.print(f"\n[bold]{message}[/bold]")
    
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
    import argparse
    
    parser = argparse.ArgumentParser(description="File Watch Diagnostics Tool")
    parser.add_argument("directory", nargs="?", default=None, help="Directory to monitor")
    parser.add_argument("--log-dir", help="Directory to store log files")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Log level")
    parser.add_argument("--testing-mode", action="store_true", help="Use shorter wait times for testing")
    
    args = parser.parse_args()
    
    diagnostics = FileWatchDiagnostics(args.directory, args.log_dir, args.log_level, args.testing_mode)
    results = diagnostics.run_all_diagnostics()
    
    return 0


if __name__ == "__main__":
    import argparse
    main()
