"""
Sovereign Grade Secure File Storage.

Provides atomic file operations with enforced permissions for credential caching
and other sensitive data. Never writes content before setting permissions.

Key Security Properties:
- Atomic writes: temp file -> chmod -> rename (no race condition window)
- Pre-write chmod: Permissions set on file descriptor BEFORE any content written
- Permission validation on read: Strict mode refuses insecure files
- Directory enforcement: Secure directories (0o700) for all storage

Usage:
    from replimap.core.security.storage import SecureStorage

    # Atomic write with secure permissions
    SecureStorage.write_json(Path.home() / ".replimap" / "cache" / "creds.json", data)

    # Read with permission validation
    data = SecureStorage.read_json(path, strict=True)  # Raises if insecure
"""

from __future__ import annotations

import json
import logging
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Union

logger = logging.getLogger(__name__)


class SecureStorage:
    """
    Secure file storage with atomic writes and permission enforcement.

    All operations enforce:
    - File permissions: 0o600 (owner read/write only)
    - Directory permissions: 0o700 (owner full access only)
    - Atomic writes to prevent race conditions
    - Permission validation on read
    """

    # Secure permission modes
    SECURE_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR  # 0o600
    SECURE_DIR_MODE = stat.S_IRWXU  # 0o700

    # Bits that indicate insecure permissions (any group/other access)
    INSECURE_BITS = stat.S_IRWXG | stat.S_IRWXO

    @staticmethod
    def ensure_secure_dir(path: Union[str, Path]) -> None:
        """
        Ensure directory exists with secure permissions (0o700).

        Creates parent directories as needed, all with 0o700.

        Args:
            path: Directory path to secure

        Raises:
            OSError: If directory creation fails
        """
        path = Path(path)

        if path.exists():
            # Directory exists - verify and fix permissions
            current_mode = stat.S_IMODE(path.stat().st_mode)
            if current_mode != SecureStorage.SECURE_DIR_MODE:
                logger.debug(
                    f"Fixing directory permissions: {path} "
                    f"(0o{current_mode:o} -> 0o700)"
                )
                os.chmod(path, SecureStorage.SECURE_DIR_MODE)
        else:
            # Create directory with secure permissions
            # Use umask to ensure correct permissions even with concurrent access
            old_umask = os.umask(0o077)  # Block all group/other access
            try:
                path.mkdir(parents=True, exist_ok=True)
                # Explicitly set permissions (umask may not apply to mkdir -p parents)
                os.chmod(path, SecureStorage.SECURE_DIR_MODE)
                logger.debug(f"Created secure directory: {path} (0o700)")
            finally:
                os.umask(old_umask)

    @staticmethod
    def write_json(path: Union[str, Path], data: Any) -> None:
        """
        Atomically write JSON file with secure permissions.

        Security Process:
        1. Ensure parent directory exists with 0o700
        2. Create temp file in same directory (same filesystem for atomic rename)
        3. Set permissions to 0o600 BEFORE writing any content
        4. Write JSON content
        5. Atomic rename to target path
        6. Clean up temp file on failure

        Args:
            path: Target file path
            data: Data to serialize as JSON

        Raises:
            OSError: If file operations fail
            TypeError: If data is not JSON serializable
        """
        path = Path(path)
        parent_dir = path.parent

        # Ensure parent directory is secure
        SecureStorage.ensure_secure_dir(parent_dir)

        # Create temp file in same directory for atomic rename
        fd = None
        temp_path = None

        try:
            # mkstemp returns (file_descriptor, path)
            # Create in same directory to ensure same filesystem
            fd, temp_path = tempfile.mkstemp(
                suffix=".tmp",
                prefix=f".{path.name}.",
                dir=parent_dir,
            )

            # CRITICAL: Set permissions BEFORE writing any content
            # Use fchmod on file descriptor to avoid race with path
            os.fchmod(fd, SecureStorage.SECURE_FILE_MODE)

            # Write content through file descriptor
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                fd = None  # fdopen takes ownership of fd
                json.dump(data, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())  # Ensure data hits disk

            # Atomic rename (same filesystem guarantees atomicity)
            os.rename(temp_path, path)
            temp_path = None  # Rename succeeded

            logger.debug(f"Wrote secure file: {path} (0o600)")

        except Exception:
            # Clean up temp file on failure
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise

    @staticmethod
    def read_json(path: Union[str, Path], strict: bool = True) -> Any:
        """
        Read JSON file with permission validation.

        Validates that file permissions are secure before reading.
        In strict mode, refuses to read insecure files.
        In non-strict mode, warns but continues.

        Args:
            path: File path to read
            strict: If True, raise PermissionError for insecure files.
                   If False, log warning but continue reading.

        Returns:
            Parsed JSON data

        Raises:
            FileNotFoundError: File doesn't exist
            PermissionError: File has insecure permissions (strict mode only)
            json.JSONDecodeError: Invalid JSON content
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Check permissions
        is_secure, message = SecureStorage.verify_permissions(path)

        if not is_secure:
            if strict:
                raise PermissionError(
                    f"Insecure file permissions on {path}: {message}. "
                    f"Expected 0o600 (owner read/write only). "
                    f"Fix with: chmod 600 {path}"
                )
            else:
                logger.warning(
                    f"Insecure file permissions on {path}: {message}. "
                    f"Reading anyway (strict=False)."
                )

        # Read and parse JSON
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def verify_permissions(path: Union[str, Path]) -> tuple[bool, str]:
        """
        Verify file or directory has secure permissions.

        Checks that no group or other access bits are set.

        Args:
            path: Path to verify

        Returns:
            Tuple of (is_secure, message)
            - is_secure: True if permissions are secure
            - message: Description of current permissions or issue
        """
        path = Path(path)

        if not path.exists():
            return False, "Path does not exist"

        try:
            file_stat = path.stat()
            mode = stat.S_IMODE(file_stat.st_mode)

            # Check if any insecure bits are set
            insecure_bits = mode & SecureStorage.INSECURE_BITS

            if insecure_bits:
                # Decode which bits are problematic
                issues = []
                if mode & stat.S_IRGRP:
                    issues.append("group-readable")
                if mode & stat.S_IWGRP:
                    issues.append("group-writable")
                if mode & stat.S_IXGRP:
                    issues.append("group-executable")
                if mode & stat.S_IROTH:
                    issues.append("world-readable")
                if mode & stat.S_IWOTH:
                    issues.append("world-writable")
                if mode & stat.S_IXOTH:
                    issues.append("world-executable")

                return False, f"File is {', '.join(issues)} (mode: 0o{mode:o})"

            # Permissions are secure
            return True, f"Secure (mode: 0o{mode:o})"

        except OSError as e:
            return False, f"Cannot stat file: {e}"

    @staticmethod
    def delete_secure(path: Union[str, Path]) -> bool:
        """
        Securely delete a file.

        Args:
            path: File path to delete

        Returns:
            True if file was deleted, False if it didn't exist
        """
        path = Path(path)

        if not path.exists():
            return False

        try:
            os.unlink(path)
            logger.debug(f"Deleted file: {path}")
            return True
        except OSError as e:
            logger.warning(f"Failed to delete {path}: {e}")
            return False

    @staticmethod
    def read_json_or_default(
        path: Union[str, Path],
        default: Any = None,
        strict: bool = True,
    ) -> Any:
        """
        Read JSON file, returning default if file doesn't exist.

        Convenience method that handles missing files gracefully.

        Args:
            path: File path to read
            default: Value to return if file doesn't exist
            strict: Permission validation strictness

        Returns:
            Parsed JSON data or default value
        """
        try:
            return SecureStorage.read_json(path, strict=strict)
        except FileNotFoundError:
            return default
