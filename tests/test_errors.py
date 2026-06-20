import pytest
from pingcastle_mcp.errors import (
    PingCastleError, ConfigError, AuthError, NetworkError, NotFoundError, ScannerError,
)


@pytest.mark.parametrize("exc", [ConfigError, AuthError, NetworkError, NotFoundError, ScannerError])
def test_all_errors_subclass_base(exc):
    e = exc("boom")
    assert isinstance(e, PingCastleError)
    assert str(e) == "boom"
