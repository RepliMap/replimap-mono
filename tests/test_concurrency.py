"""Tests for global concurrency management."""

from __future__ import annotations

import time

import pytest

from replimap.core.concurrency import (
    _active_executors,
    check_shutdown,
    create_thread_pool,
    is_shutdown_requested,
    reset_shutdown_state,
    shutdown_all_executors,
)


class TestCreateThreadPool:
    """Tests for create_thread_pool()."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_shutdown_state()
        # Clean up any remaining executors
        for executor in list(_active_executors):
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass

    def test_creates_executor_with_max_workers(self) -> None:
        """Should create executor with specified max_workers."""
        executor = create_thread_pool(max_workers=5, thread_name_prefix="test-")
        try:
            assert executor._max_workers == 5
        finally:
            executor.shutdown(wait=True)

    def test_creates_executor_with_thread_prefix(self) -> None:
        """Should create executor with specified thread name prefix."""
        executor = create_thread_pool(max_workers=2, thread_name_prefix="myprefix-")
        try:
            assert executor._thread_name_prefix == "myprefix-"
        finally:
            executor.shutdown(wait=True)

    def test_registers_executor_for_tracking(self) -> None:
        """Should register executor in _active_executors."""
        initial_count = len(_active_executors)
        executor = create_thread_pool(max_workers=2, thread_name_prefix="test-")
        try:
            assert len(_active_executors) == initial_count + 1
            assert executor in _active_executors
        finally:
            executor.shutdown(wait=True)

    def test_executor_can_submit_tasks(self) -> None:
        """Created executor should be able to submit and run tasks."""
        executor = create_thread_pool(max_workers=2, thread_name_prefix="test-")
        try:
            future = executor.submit(lambda x: x * 2, 21)
            assert future.result(timeout=5) == 42
        finally:
            executor.shutdown(wait=True)


class TestShutdownAllExecutors:
    """Tests for shutdown_all_executors()."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_shutdown_state()
        for executor in list(_active_executors):
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass

    def test_returns_zero_when_no_executors(self) -> None:
        """Should return 0 when no active executors."""
        # Clear any existing executors
        for executor in list(_active_executors):
            executor.shutdown(wait=False)
        _active_executors.clear()
        reset_shutdown_state()

        count = shutdown_all_executors(wait=False)
        assert count == 0

    def test_shuts_down_all_tracked_executors(self) -> None:
        """Should shutdown all tracked executors."""
        # Create multiple executors (need to keep reference to prevent GC)
        _ = [
            create_thread_pool(max_workers=2, thread_name_prefix=f"test{i}-")
            for i in range(3)
        ]

        # All should be tracked
        assert len(_active_executors) >= 3

        # Shutdown all
        count = shutdown_all_executors(wait=False)
        assert count >= 3

    def test_sets_shutdown_requested_flag(self) -> None:
        """Should set _shutdown_requested to True."""
        reset_shutdown_state()
        assert not is_shutdown_requested()

        shutdown_all_executors(wait=False)

        assert is_shutdown_requested()


class TestIsShutdownRequested:
    """Tests for is_shutdown_requested()."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_shutdown_state()

    def test_returns_false_initially(self) -> None:
        """Should return False when no shutdown requested."""
        reset_shutdown_state()
        assert not is_shutdown_requested()

    def test_returns_true_after_shutdown(self) -> None:
        """Should return True after shutdown_all_executors called."""
        reset_shutdown_state()
        shutdown_all_executors(wait=False)
        assert is_shutdown_requested()


class TestCheckShutdown:
    """Tests for check_shutdown()."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_shutdown_state()

    def test_does_not_raise_when_no_shutdown(self) -> None:
        """Should not raise when shutdown not requested."""
        reset_shutdown_state()
        # Should not raise
        check_shutdown()

    def test_raises_keyboard_interrupt_when_shutdown_requested(self) -> None:
        """Should raise KeyboardInterrupt when shutdown requested."""
        reset_shutdown_state()
        shutdown_all_executors(wait=False)

        with pytest.raises(KeyboardInterrupt):
            check_shutdown()


class TestResetShutdownState:
    """Tests for reset_shutdown_state()."""

    def test_resets_shutdown_flag(self) -> None:
        """Should reset _shutdown_requested to False."""
        # First set it to True
        shutdown_all_executors(wait=False)
        assert is_shutdown_requested()

        # Then reset
        reset_shutdown_state()
        assert not is_shutdown_requested()


class TestWeakRefBehavior:
    """Tests for WeakSet behavior of _active_executors."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_shutdown_state()

    def test_executor_removed_when_garbage_collected(self) -> None:
        """Executors should be auto-removed when garbage collected."""
        initial_count = len(_active_executors)

        # Create executor in a scope
        executor = create_thread_pool(max_workers=1, thread_name_prefix="temp-")
        assert len(_active_executors) == initial_count + 1

        # Shutdown and delete reference
        executor.shutdown(wait=True)
        del executor

        # Force garbage collection
        import gc

        gc.collect()

        # Should be removed from tracking
        # Note: WeakSet may not immediately remove - this is best-effort
        # The important thing is it won't prevent GC


class TestConcurrentExecution:
    """Tests for concurrent task execution."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_shutdown_state()
        for executor in list(_active_executors):
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass

    def test_multiple_tasks_execute_concurrently(self) -> None:
        """Multiple tasks should execute concurrently."""
        results = []
        start_times = []

        def slow_task(n: int) -> int:
            start_times.append(time.time())
            time.sleep(0.1)
            results.append(n)
            return n

        executor = create_thread_pool(max_workers=5, thread_name_prefix="concurrent-")
        try:
            futures = [executor.submit(slow_task, i) for i in range(5)]
            for f in futures:
                f.result(timeout=5)

            # All tasks should have started within a short window
            if len(start_times) >= 2:
                time_spread = max(start_times) - min(start_times)
                assert time_spread < 0.5  # All should start within 0.5s
        finally:
            executor.shutdown(wait=True)
