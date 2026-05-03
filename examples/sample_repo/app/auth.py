"""Authentication helpers for the sample repository."""

from dataclasses import dataclass


@dataclass
class User:
    id: str
    email: str
    role: str = "member"


def validate_token(token: str) -> bool:
    """Return True when a token has the expected demo prefix."""
    return token.startswith("demo_") and len(token) > 8


def get_current_user(token: str) -> User | None:
    """Resolve the current user from a bearer token."""
    if not validate_token(token):
        return None
    return User(id="sample-user", email="sample@example.com")

