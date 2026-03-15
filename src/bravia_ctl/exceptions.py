from __future__ import annotations


class BraviaError(Exception):
    pass


class BraviaConnectionError(BraviaError):
    pass


class BraviaAuthError(BraviaError):
    pass


class BraviaAPIError(BraviaError):
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"API error {code}: {message}")
