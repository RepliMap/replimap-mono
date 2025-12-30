"""
Tests for observability modules: logging and graph tracing.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock


class TestStructuredLogging:
    """Tests for structured logging configuration."""

    def test_configure_logging_default(self) -> None:
        """Test default logging configuration."""
        from replimap.core.logging import configure_logging, get_logger

        configure_logging(force=True)
        logger = get_logger("test")

        assert logger is not None

    def test_get_logger_returns_bound_logger(self) -> None:
        """Test get_logger returns a structlog BoundLogger."""
        from replimap.core.logging import configure_logging, get_logger

        configure_logging(force=True)
        logger = get_logger("test.module")

        # Should be callable with structured args
        # This just verifies no exception is raised
        logger.info("test_event", key="value", count=42)

    def test_log_context_manager(self) -> None:
        """Test LogContext adds and removes context."""
        from replimap.core.logging import LogContext, configure_logging, get_logger

        configure_logging(force=True)
        logger = get_logger("test")

        with LogContext(request_id="abc123", user="admin"):
            # Context should be bound
            logger.info("inside_context")

        # Context should be unbound
        logger.info("outside_context")

    def test_timer_context_manager(self) -> None:
        """Test Timer measures and logs duration."""
        import time

        from replimap.core.logging import Timer, configure_logging, get_logger

        configure_logging(force=True)
        logger = get_logger("test")

        with Timer(logger, "test_operation", service="test") as timer:
            time.sleep(0.01)  # 10ms

        assert timer.duration_ms is not None
        assert timer.duration_ms >= 10  # At least 10ms

    def test_scan_metrics_recording(self) -> None:
        """Test ScanMetrics records and reports metrics."""
        from replimap.core.logging import ScanMetrics, configure_logging, get_logger

        configure_logging(force=True)
        get_logger("test")  # Verify no error

        metrics = ScanMetrics()
        metrics.start()

        metrics.record_api_call("ec2", "describe_instances", 100.0)
        metrics.record_api_call("rds", "describe_db_instances", 200.0)
        metrics.record_resource("aws_instance", 10)
        metrics.record_resource("aws_db_instance", 5)
        metrics.record_error("rate_limit", "Throttled")

        metrics.stop()

        # Check calculated properties
        assert metrics.total_api_calls == 2
        assert metrics.total_resources == 15
        assert metrics.avg_api_latency_ms == 150.0
        assert metrics.total_duration_ms > 0

        # Convert to dict
        data = metrics.to_dict()
        assert data["total_api_calls"] == 2
        assert data["total_resources"] == 15
        assert data["error_count"] == 1

    def test_sensitive_data_redaction(self) -> None:
        """Test sensitive fields are redacted in logs."""
        from replimap.core.logging import _sanitize_sensitive

        event_dict = {
            "event": "test",
            "password": "secret123",
            "api_key": "key123",
            "username": "admin",  # Not sensitive
        }

        result = _sanitize_sensitive(None, "info", event_dict)

        assert result["password"] == "[REDACTED]"  # noqa: S105
        assert result["api_key"] == "[REDACTED]"
        assert result["username"] == "admin"  # Unchanged


class TestGraphTracer:
    """Tests for graph tracing functionality."""

    def test_tracer_disabled_noop(self) -> None:
        """Test disabled tracer is a no-op."""
        from replimap.core.graph_tracer import GraphPhase, GraphTracer

        tracer = GraphTracer(enabled=False)
        mock_graph = MagicMock()

        result = tracer.snapshot(GraphPhase.DISCOVERY, mock_graph)
        assert result is None

        diff = tracer.diff(GraphPhase.DISCOVERY, GraphPhase.LINKING)
        assert diff is None

    def test_tracer_creates_output_dir(self) -> None:
        """Test tracer creates output directory when enabled."""
        from replimap.core.graph_tracer import GraphTracer

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "trace"

            GraphTracer(output_dir=output_dir, enabled=True)

            assert output_dir.exists()

    def test_snapshot_captures_graph_state(self) -> None:
        """Test snapshot captures nodes and edges."""
        from replimap.core.graph_tracer import GraphPhase, GraphTracer

        with tempfile.TemporaryDirectory() as tmpdir:
            tracer = GraphTracer(output_dir=Path(tmpdir), enabled=True)

            # Create mock graph
            mock_node = MagicMock()
            mock_node.id = "vpc-123"
            mock_node.resource_type = "aws_vpc"
            mock_node.name = "test-vpc"

            mock_graph = MagicMock()
            mock_graph.nodes.return_value = ["vpc-123"]
            mock_graph.get_node.return_value = mock_node
            mock_graph._graph.edges.return_value = []

            snapshot = tracer.snapshot(GraphPhase.DISCOVERY, mock_graph)

            assert snapshot is not None
            assert snapshot.phase == GraphPhase.DISCOVERY
            assert snapshot.node_count == 1
            assert snapshot.edge_count == 0

    def test_snapshot_exports_json(self) -> None:
        """Test snapshot exports to JSON file."""
        from replimap.core.graph_tracer import GraphPhase, GraphTracer

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            tracer = GraphTracer(output_dir=output_dir, enabled=True)

            mock_node = MagicMock()
            mock_node.id = "vpc-123"
            mock_node.resource_type = "aws_vpc"
            mock_node.name = "test"

            mock_graph = MagicMock()
            mock_graph.nodes.return_value = ["vpc-123"]
            mock_graph.get_node.return_value = mock_node
            mock_graph._graph.edges.return_value = []

            tracer.snapshot(GraphPhase.DISCOVERY, mock_graph)

            json_file = output_dir / "graph_1_discovery.json"
            assert json_file.exists()

            data = json.loads(json_file.read_text())
            assert data["phase"] == "1_discovery"
            assert data["node_count"] == 1

    def test_snapshot_exports_graphml(self) -> None:
        """Test snapshot exports to GraphML file."""
        from replimap.core.graph_tracer import GraphPhase, GraphTracer

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            tracer = GraphTracer(output_dir=output_dir, enabled=True)

            mock_node = MagicMock()
            mock_node.id = "vpc-123"
            mock_node.resource_type = "aws_vpc"
            mock_node.name = "test"

            mock_graph = MagicMock()
            mock_graph.nodes.return_value = ["vpc-123"]
            mock_graph.get_node.return_value = mock_node
            mock_graph._graph.edges.return_value = []

            tracer.snapshot(GraphPhase.DISCOVERY, mock_graph)

            graphml_file = output_dir / "graph_1_discovery.graphml"
            assert graphml_file.exists()

            content = graphml_file.read_text()
            assert "<graphml" in content
            assert 'id="vpc-123"' in content

    def test_diff_calculates_changes(self) -> None:
        """Test diff correctly calculates node/edge changes."""
        from replimap.core.graph_tracer import GraphPhase, GraphTracer

        with tempfile.TemporaryDirectory() as tmpdir:
            tracer = GraphTracer(output_dir=Path(tmpdir), enabled=True)

            # First snapshot: 1 node
            mock_node1 = MagicMock()
            mock_node1.id = "vpc-123"
            mock_node1.resource_type = "aws_vpc"
            mock_node1.name = "test"

            mock_graph1 = MagicMock()
            mock_graph1.nodes.return_value = ["vpc-123"]
            mock_graph1.get_node.return_value = mock_node1
            mock_graph1._graph.edges.return_value = []

            tracer.snapshot(GraphPhase.DISCOVERY, mock_graph1)

            # Second snapshot: 2 nodes, 1 edge
            mock_node2 = MagicMock()
            mock_node2.id = "subnet-456"
            mock_node2.resource_type = "aws_subnet"
            mock_node2.name = "test-subnet"

            mock_graph2 = MagicMock()
            mock_graph2.nodes.return_value = ["vpc-123", "subnet-456"]
            mock_graph2.get_node.side_effect = lambda x: (
                mock_node1 if x == "vpc-123" else mock_node2
            )
            mock_graph2._graph.edges.return_value = [
                ("subnet-456", "vpc-123", {"dependency_type": "vpc_id"})
            ]

            tracer.snapshot(GraphPhase.LINKING, mock_graph2)

            # Calculate diff
            diff = tracer.diff(GraphPhase.DISCOVERY, GraphPhase.LINKING)

            assert diff is not None
            assert "subnet-456" in diff.nodes_added
            assert len(diff.nodes_removed) == 0
            assert len(diff.edges_added) == 1

    def test_export_summary(self) -> None:
        """Test export_summary creates summary file."""
        from replimap.core.graph_tracer import GraphPhase, GraphTracer

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            tracer = GraphTracer(output_dir=output_dir, enabled=True)

            mock_node = MagicMock()
            mock_node.id = "vpc-123"
            mock_node.resource_type = "aws_vpc"
            mock_node.name = "test"

            mock_graph = MagicMock()
            mock_graph.nodes.return_value = ["vpc-123"]
            mock_graph.get_node.return_value = mock_node
            mock_graph._graph.edges.return_value = []

            tracer.snapshot(GraphPhase.DISCOVERY, mock_graph)
            tracer.snapshot(GraphPhase.LINKING, mock_graph)

            summary_path = tracer.export_summary()

            assert summary_path is not None
            assert summary_path.exists()

            summary = json.loads(summary_path.read_text())
            assert "1_discovery" in summary["phases_captured"]
            assert "2_linking" in summary["phases_captured"]

    def test_graph_phase_ordering(self) -> None:
        """Test GraphPhase enum values sort correctly."""
        from replimap.core.graph_tracer import GraphPhase

        phases = list(GraphPhase)
        sorted_phases = sorted(phases, key=lambda x: x.value)

        assert sorted_phases[0] == GraphPhase.DISCOVERY
        assert sorted_phases[-1] == GraphPhase.FINAL


class TestGlobalTracerSingleton:
    """Tests for global tracer singleton pattern."""

    def test_init_tracer_creates_instance(self) -> None:
        """Test init_tracer creates global instance."""
        from replimap.core.graph_tracer import get_tracer, init_tracer

        with tempfile.TemporaryDirectory() as tmpdir:
            tracer = init_tracer(output_dir=Path(tmpdir), enabled=True)

            assert tracer is not None
            assert get_tracer() is tracer

    def test_get_tracer_before_init_returns_none(self) -> None:
        """Test get_tracer returns None before initialization."""
        import replimap.core.graph_tracer as gt

        # Reset global state
        gt._global_tracer = None

        assert gt.get_tracer() is None
