"""
Global concurrency management for graceful shutdown.

All code that needs thread pools should use create_thread_pool() instead of
ThreadPoolExecutor() directly. This allows centralized shutdown on Ctrl-C.

Usage:
    from replimap.core.concurrency import create_thread_pool

    executor = create_thread_pool(max_workers=10, thread_name_prefix="scanner-")
    try:
        # ... submit tasks
    finally:
        executor.shutdown(wait=True)  # Only for normal completion

    # No need for KeyboardInterrupt handling - global handler does it
"""

from __future__ import annotations

import logging
import weakref
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# WeakSet auto-removes executors when they're garbage collected
_active_executors: weakref.WeakSet[ThreadPoolExecutor] = weakref.WeakSet()
_shutdown_requested: bool = False


def create_thread_pool(
    max_workers: int | None = None,
    thread_name_prefix: str = "replimap-",
) -> ThreadPoolExecutor:
    """
    Factory method: Create a tracked ThreadPoolExecutor.

    Use this instead of ThreadPoolExecutor() directly.
    All pools created this way will be shut down on Ctrl-C.

    Args:
        max_workers: Maximum number of threads
        thread_name_prefix: Prefix for thread names (helps debugging)

    Returns:
        A ThreadPoolExecutor that's registered for global shutdown
    """
    executor = ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix=thread_name_prefix,
    )
    _active_executors.add(executor)
    logger.debug(f"Created thread pool: {thread_name_prefix} (workers={max_workers})")
    return executor


def shutdown_all_executors(wait: bool = False) -> int:
    """
    Emergency shutdown: Kill all active thread pools.

    Called by signal handler on Ctrl-C.

    Args:
        wait: If True, wait for threads to finish (usually False for Ctrl-C)

    Returns:
        Number of executors that were shut down
    """
    global _shutdown_requested
    _shutdown_requested = True

    count = len(_active_executors)
    if count == 0:
        return 0

    logger.debug(f"Shutting down {count} active thread pool(s)...")

    # Copy to avoid modification during iteration
    for executor in list(_active_executors):
        try:
            executor.shutdown(wait=wait, cancel_futures=True)
        except Exception as e:
            logger.debug(f"Error shutting down executor: {e}")

    return count


def is_shutdown_requested() -> bool:
    """Check if shutdown was requested (for cooperative cancellation)."""
    return _shutdown_requested


def check_shutdown() -> None:
    """
    Call this in long-running loops for faster cooperative cancellation.

    Raises:
        KeyboardInterrupt: If shutdown was requested

    Usage:
        for page in paginator.paginate():
            check_shutdown()  # Exit early if Ctrl-C pressed
            process(page)
    """
    if _shutdown_requested:
        raise KeyboardInterrupt("Shutdown requested")


def reset_shutdown_state() -> None:
    """Reset shutdown state (mainly for testing)."""
    global _shutdown_requested
    _shutdown_requested = False
