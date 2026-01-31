"""
Persistence Layer

Pluggable storage backends for user state.

Usage:
    from persistence import create_backend

    backend = create_backend("in_memory")
    backend.save("user_123", state)
    state = backend.load("user_123")
"""

from .backend import PersistenceBackend, PersistenceError
from .in_memory import InMemoryBackend


def create_backend(backend_type: str, **kwargs) -> PersistenceBackend:
    """
    Factory function for creating persistence backends.

    Args:
        backend_type: Type of backend ("in_memory", "redis", "postgres")
        **kwargs: Backend-specific configuration

    Returns:
        PersistenceBackend instance

    Raises:
        ValueError: If backend_type is unknown

    Examples:
        >>> backend = create_backend("in_memory")
        >>> backend = create_backend("redis", redis_url="redis://localhost:6379")
    """
    if backend_type == "in_memory":
        return InMemoryBackend()
    elif backend_type == "redis":
        # Future: from .redis import RedisBackend
        # return RedisBackend(kwargs.get("redis_url"))
        raise NotImplementedError("Redis backend not yet implemented")
    elif backend_type == "postgres":
        # Future: from .postgres import PostgresBackend
        # return PostgresBackend(kwargs.get("db_url"))
        raise NotImplementedError("Postgres backend not yet implemented")
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")


__all__ = [
    "PersistenceBackend",
    "PersistenceError",
    "InMemoryBackend",
    "create_backend",
]
