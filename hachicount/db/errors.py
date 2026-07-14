"""Domain exceptions for the database layer."""


class UserNotFoundError(Exception):
    """Raised when an operation targets a user that does not exist."""

    def __init__(self, email: str) -> None:
        super().__init__(f"No user with email {email!r}")
        self.email = email
