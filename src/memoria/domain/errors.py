class MemoriaError(Exception):
    """Base exception for Memoria."""


class PatchValidationError(MemoriaError):
    """Raised when a patch is valid JSON but violates Memoria policy."""


class NotFoundError(MemoriaError):
    """Raised when a requested memory object does not exist."""
