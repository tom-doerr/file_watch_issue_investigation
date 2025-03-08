#!/usr/bin/env python3
"""
CLI entry point for file watch diagnostics.
"""

import argparse
import sys
from file_watch_diagnostics.diagnostics import FileWatchDiagnostics

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
    parser.add_argument("--testing-mode", action="store_true",
                        help="Run in testing mode with shorter wait times")
    
    args = parser.parse_args()
    
    diagnostics = FileWatchDiagnostics(
        args.directory, 
        args.log_dir, 
        args.log_level,
        testing_mode=args.testing_mode
    )
    diagnostics.run_all_diagnostics()
    sys.exit(0)


if __name__ == "__main__":
    main()
