"""
Global concurrency management for graceful shutdown and rate-limited execution.

All code that needs thread pools should use create_thread_pool() instead of
ThreadPoolExecutor() directly. This allows centralized shutdown on Ctrl-C.

For parallel mapping with automatic rate limiting coordination, use parallel_map()
or get_executor() to access the global thread pool.

Usage:
    # Traditional approach (multiple pools)
    from replimap.core.concurrency import create_thread_pool

    executor = create_thread_pool(max_workers=10, thread_name_prefix="scanner-")
    try:
        # ... submit tasks
    finally:
        executor.shutdown(wait=True)  # Only for normal completion

    # New approach (global pool)
    from replimap.core.concurrency import parallel_map

    results = parallel_map(scan_vpc, vpc_ids)
"""

from __future__ import annotations

import logging
import weakref
import threading
import atexit
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import Callable, Iterable, TypeVar, Optional, Any

logger = logging.getLogger(__name__)

T = TypeVar('T')

# WeakSet auto-removes executors when they're garbage collected
_active_executors: weakref.WeakSet[ThreadPoolExecutor] = weakref.WeakSet()
_shutdown_requested: bool = False

# Configuration for global executor
DEFAULT_MAX_WORKERS = 20  # Total concurrent API calls across all scanners


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


# Global Executor Pattern (for rate-limited parallel execution)


class GlobalExecutor:
    """
    Thread-safe singleton for global thread pool management.

    All scanners should use this instead of creating their own ThreadPoolExecutor
    to prevent thread explosion and coordinate with rate limiting.
    """

    _instance: Optional[GlobalExecutor] = None
    _lock = threading.Lock()

    def __new__(cls, max_workers: int = DEFAULT_MAX_WORKERS):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self, max_workers: int = DEFAULT_MAX_WORKERS):
        if self._initialized:
            return

        self._initialized = True
        self._max_workers = max_workers
        self._executor: Optional[ThreadPoolExecutor] = None
        self._executor_lock = threading.Lock()

        # Register shutdown on program exit
        atexit.register(self.shutdown)

        logger.info(f"GlobalExecutor initialized (max_workers={max_workers})")

    @property
    def executor(self) -> ThreadPoolExecutor:
        """Lazy initialization of thread pool"""
        if self._executor is None:
            with self._executor_lock:
                if self._executor is None:
                    self._executor = create_thread_pool(
                        max_workers=self._max_workers,
                        thread_name_prefix="replimap-worker-"
                    )
        return self._executor

    def submit(self, fn: Callable[..., T], *args, **kwargs) -> Future[T]:
        """Submit a task to the global thread pool"""
        return self.executor.submit(fn, *args, **kwargs)

    def map(
        self,
        fn: Callable[..., T],
        items: Iterable,
        timeout: Optional[float] = None,
    ) -> list[T]:
        """
        Map function over items using global thread pool.

        Args:
            fn: Function to apply
            items: Iterable of items
            timeout: Optional timeout per item

        Returns:
            List of results (preserves order)
        """
        items_list = list(items)
        if not items_list:
            return []

        futures = [self.submit(fn, item) for item in items_list]
        results = []
        errors = []

        for i, future in enumerate(futures):
            try:
                result = future.result(timeout=timeout)
                results.append(result)
            except Exception as e:
                logger.error(f"Task {i} failed: {e}")
                errors.append((i, e))
                results.append(None)

        if errors:
            logger.warning(f"Parallel map completed with {len(errors)} errors")

        return results

    def map_unordered(
        self,
        fn: Callable[..., T],
        items: Iterable,
        timeout: Optional[float] = None,
    ) -> Iterable[T]:
        """
        Map function over items, yielding results as they complete.

        More efficient than map() when order doesn't matter.
        """
        items_list = list(items)
        if not items_list:
            return

        futures = [self.submit(fn, item) for item in items_list]

        for future in as_completed(futures, timeout=timeout):
            try:
                yield future.result()
            except Exception as e:
                logger.error(f"Task failed: {e}")

    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool"""
        if self._executor:
            logger.info("Shutting down global executor...")
            self._executor.shutdown(wait=wait)
            self._executor = None

    @classmethod
    def reset(cls):
        """Reset singleton (for testing)"""
        with cls._lock:
            if cls._instance and cls._instance._executor:
                cls._instance._executor.shutdown(wait=False)
            cls._instance = None


# Convenience functions for global executor

def get_executor() -> GlobalExecutor:
    """Get global executor instance"""
    return GlobalExecutor()


def parallel_map(
    fn: Callable[..., T],
    items: Iterable,
    timeout: Optional[float] = None,
) -> list[T]:
    """
    Execute function in parallel using global thread pool.

    Replacement for:
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(fn, items))

    Usage:
        results = parallel_map(scan_vpc, vpc_ids)
    """
    return get_executor().map(fn, items, timeout)


def parallel_map_unordered(
    fn: Callable[..., T],
    items: Iterable,
    timeout: Optional[float] = None,
) -> Iterable[T]:
    """Execute function in parallel, yielding results as they complete"""
    return get_executor().map_unordered(fn, items, timeout)


def submit_task(fn: Callable[..., T], *args, **kwargs) -> Future[T]:
    """Submit a single task to global thread pool"""
    return get_executor().submit(fn, *args, **kwargs)
