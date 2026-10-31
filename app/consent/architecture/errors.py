"""Public consent exceptions shared by the compatibility facade and operations."""

class ConsentAccessDeniedException(Exception):
    """Actor is not authorized to manage another subject's consents."""


class SubjectNotFoundException(Exception):
    """Consent subject does not exist."""
