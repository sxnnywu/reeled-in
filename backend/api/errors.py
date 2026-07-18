"""CONTRACTS §9 error envelope: {"error": {"code", "message"}}. Owner: C (Seb)."""


class ApiError(Exception):
    """Raise anywhere in a route; main.py's handler renders the §9 envelope."""

    def __init__(self, code: str, message: str, http_status: int = 400):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


def not_found(what: str) -> ApiError:
    return ApiError("not_found", f"{what} does not exist", 404)
