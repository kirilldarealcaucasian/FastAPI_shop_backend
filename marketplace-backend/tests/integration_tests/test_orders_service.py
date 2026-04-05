import pytest

pytestmark = pytest.mark.skip(
    reason="Legacy integration test relies on removed image/storage repositories and old unit-of-work contract."
)
