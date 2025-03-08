"""
Configuration for pytest.
"""

import pytest


def pytest_collection_modifyitems(items):
    """Enable integration tests by default."""
    for item in items:
        # Remove skip mark from integration tests
        if "integration" in item.keywords:
            item.add_marker(pytest.mark.integration)
            for marker in item.own_markers:
                if marker.name == "skip" and "integration test" in str(marker.args):
                    item.own_markers.remove(marker)
