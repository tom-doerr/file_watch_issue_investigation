"""
Module for logging utilities.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def setup_logger(name, log_file=None, level=logging.INFO, use_rich=True):
    """Set up a logger with console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    if use_rich and RICH_AVAILABLE:
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=False,
            show_path=False
        )
    else:
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
    
    console_handler.setLevel(level)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is provided)
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    return logger


def get_console():
    """Get a Rich console if available, otherwise return None."""
    if RICH_AVAILABLE:
        return Console()
    return None


def get_progress():
    """Get a Rich progress bar if available, otherwise return None."""
    if RICH_AVAILABLE:
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        )
    return None


def create_log_filename(base_dir=None, prefix="file_watch_diagnostics"):
    """Create a log filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.log"
    
    if base_dir:
        path = Path(base_dir) / filename
    else:
        path = Path(filename)
    
    return str(path)


if __name__ == "__main__":
    # Example usage
    logger = setup_logger("test_logger")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    if RICH_AVAILABLE:
        console = get_console()
        console.print("[bold green]Rich is available![/bold green]")
        
        with get_progress() as progress:
            task = progress.add_task("Processing...", total=100)
            for i in range(100):
                progress.update(task, advance=1)
                import time
                time.sleep(0.01)
