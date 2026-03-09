"""
Shared fixtures and configuration for integration tests.

These tests require a valid EXAMPLE_API_KEY environment variable.
They make real API calls and should not be run in CI without proper setup.
"""

import os

import pytest
import pytest_asyncio

from mcp_example.api_client import ExampleClient


def pytest_configure(config):
    """Check for required environment variables before running tests."""
    if not os.environ.get("EXAMPLE_API_KEY"):
        pytest.exit(
            "ERROR: EXAMPLE_API_KEY environment variable is required.\n"
            "Set it before running integration tests:\n"
            "  export EXAMPLE_API_KEY=your_key_here\n"
            "  make test-integration"
        )


@pytest.fixture
def api_key() -> str:
    """Get the API key from environment."""
    key = os.environ.get("EXAMPLE_API_KEY")
    if not key:
        pytest.skip("EXAMPLE_API_KEY not set")
    return key


@pytest_asyncio.fixture
async def client(api_key: str) -> ExampleClient:
    """Create a client for testing."""
    client = ExampleClient(api_key=api_key)
    yield client
    await client.close()


# TODO: Add well-known test data constants
# class TestData:
#     """Well-known test data for integration tests."""
#     KNOWN_ID = "abc123"
