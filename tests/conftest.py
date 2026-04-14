import sys

import pytest


@pytest.fixture(autouse=True)
def _ensure_windows_only(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("windows_only") and sys.platform != "win32":
        pytest.skip("Windows-only test")
