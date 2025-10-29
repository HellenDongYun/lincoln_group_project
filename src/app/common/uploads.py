"""Utilities for working with uploaded files."""

from collections.abc import Iterable


def is_allowed_file(filename: str | None, allowed_extensions: Iterable[str]) -> bool:
    """Return True when *filename* has an extension in *allowed_extensions*.

    The comparison is case-insensitive and treats empty filenames as invalid.
    """
    if not filename or '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    normalized_extensions = {ext.lower() for ext in allowed_extensions}
    return extension in normalized_extensions
