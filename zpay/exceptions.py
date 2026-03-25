"""ZPay custom exceptions."""


class ZPayError(Exception):
    """Base exception for all ZPay errors."""


class ZPayAPIError(ZPayError):
    """Raised when the ZPay API returns a failure response (code != 1)."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def __repr__(self) -> str:
        return f"ZPayAPIError(code={self.code!r}, message={self.message!r})"


class ZPaySignatureError(ZPayError):
    """Raised when signature verification fails."""
