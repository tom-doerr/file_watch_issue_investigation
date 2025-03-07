"""
Tests for the logging_utils module.
"""

import os
import sys
import logging
import tempfile
from unittest import mock
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_watch_diagnostics.utils.logging_utils import (
    setup_logger,
    get_console,
    get_progress,
    create_log_filename
)


def test_setup_logger():
    """Test setting up a logger."""
    # Test with console handler only
    logger = setup_logger("test_logger")
    
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.Handler)
    
    # Test with file handler
    with tempfile.NamedTemporaryFile(suffix=".log") as temp_file:
        logger = setup_logger("test_logger_file", log_file=temp_file.name)
        
        assert logger.name == "test_logger_file"
        assert len(logger.handlers) == 2
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        
        # Test logging
        logger.info("Test message")
        
        # Check that the message was written to the file
        with open(temp_file.name, 'r') as f:
            content = f.read()
            assert "Test message" in content


def test_setup_logger_with_level():
    """Test setting up a logger with a custom level."""
    logger = setup_logger("test_logger_level", level=logging.WARNING)
    
    assert logger.level == logging.WARNING
    assert logger.handlers[0].level == logging.WARNING


def test_get_console():
    """Test getting a console."""
    # Test with rich available
    with mock.patch("file_watch_diagnostics.utils.logging_utils.RICH_AVAILABLE", True):
        with mock.patch("file_watch_diagnostics.utils.logging_utils.Console") as mock_console:
            console = get_console()
            mock_console.assert_called_once()
    
    # Test with rich not available
    with mock.patch("file_watch_diagnostics.utils.logging_utils.RICH_AVAILABLE", False):
        console = get_console()
        assert console is None


def test_get_progress():
    """Test getting a progress bar."""
    # Test with rich available
    with mock.patch("file_watch_diagnostics.utils.logging_utils.RICH_AVAILABLE", True):
        with mock.patch("file_watch_diagnostics.utils.logging_utils.Progress") as mock_progress:
            progress = get_progress()
            mock_progress.assert_called_once()
    
    # Test with rich not available
    with mock.patch("file_watch_diagnostics.utils.logging_utils.RICH_AVAILABLE", False):
        progress = get_progress()
        assert progress is None


def test_create_log_filename():
    """Test creating a log filename."""
    # Test with default parameters
    filename = create_log_filename()
    assert "file_watch_diagnostics_" in filename
    assert filename.endswith(".log")
    
    # Test with custom base directory
    with tempfile.TemporaryDirectory() as temp_dir:
        filename = create_log_filename(base_dir=temp_dir)
        assert temp_dir in filename
        assert "file_watch_diagnostics_" in filename
        assert filename.endswith(".log")
    
    # Test with custom prefix
    filename = create_log_filename(prefix="custom_prefix")
    assert "custom_prefix_" in filename
    assert filename.endswith(".log")
