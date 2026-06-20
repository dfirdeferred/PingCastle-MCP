class PingCastleError(Exception):
    """Base class for all pingcastle-mcp errors."""


class ConfigError(PingCastleError):
    """Missing or invalid configuration (URL/key)."""


class AuthError(PingCastleError):
    """Login failed or token rejected."""


class NetworkError(PingCastleError):
    """Host unreachable or TLS failure."""


class NotFoundError(PingCastleError):
    """Requested resource id does not exist."""


class ScannerError(PingCastleError):
    """PingCastle.exe missing, failed, timed out, or upload failed."""
