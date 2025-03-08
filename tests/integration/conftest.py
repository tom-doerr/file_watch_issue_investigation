"""
Configuration for integration tests.
"""

import pytest


def pytest_configure(config):
    """Register the integration marker."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )


def pytest_addoption(parser):
    """Add command-line options for integration tests."""
    parser.addoption(
        "--skip-integration",
        action="store_true",
        default=False,
        help="skip integration tests",
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests if --skip-integration is specified."""
    if config.getoption("--skip-integration"):
        skip_integration = pytest.mark.skip(reason="--skip-integration option was used")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
