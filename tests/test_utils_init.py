"""
Tests for the utils module initialization.
"""

import pytest
from file_watch_diagnostics.utils import __doc__


def test_utils_module_doc():
    """Test that the utils module has a docstring."""
    assert __doc__ is not None
    assert "Utility functions for file watch diagnostics." in __doc__
