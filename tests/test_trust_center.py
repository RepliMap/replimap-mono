"""
Tests for P1-9: Trust Center Audit System.

Tests verify:
1. APICallRecord and AuditSession data models
2. OperationClassifier for READ/WRITE/DELETE/ADMIN categorization
3. TrustCenter singleton and session management
4. Report generation and compliance statements
5. Export utilities (JSON, CSV, text)
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from replimap.audit.classifier import OperationClassifier, classifier
from replimap.audit.exporters import (
    export_csv,
    export_json,
    export_summary_csv,
    generate_compliance_text,
    save_compliance_text,
)
from replimap.audit.models import (
    APICallRecord,
    APICategory,
    AuditEventType,
    AuditSession,
    TrustCenterReport,
)
from replimap.audit.trust_center import TrustCenter


class TestAPICategory:
    """Test APICategory enum."""

    def test_category_values(self):
        """Test category enum values."""
        assert APICategory.READ.value == "read"
        assert APICategory.WRITE.value == "write"
        assert APICategory.DELETE.value == "delete"
        assert APICategory.ADMIN.value == "admin"
        assert APICategory.UNKNOWN.value == "unknown"

    def test_category_str(self):
        """Test category string representation."""
        assert str(APICategory.READ) == "read"
        assert str(APICategory.WRITE) == "write"


class TestAuditEventType:
    """Test AuditEventType enum."""

    def test_event_type_values(self):
        """Test event type enum values."""
        assert AuditEventType.API_CALL.value == "api_call"
        assert AuditEventType.SESSION_START.value == "session_start"
        assert AuditEventType.SESSION_END.value == "session_end"
        assert AuditEventType.ERROR.value == "error"


class TestAPICallRecord:
    """Test APICallRecord model."""

    def test_create_record(self):
        """Test creating an API call record."""
        record = APICallRecord(
            timestamp=datetime.utcnow(),
            duration_ms=150,
            service="ec2",
            operation="DescribeInstances",
            region="us-east-1",
            request_id="req-12345",
            category=APICategory.READ,
        )

        assert record.service == "ec2"
        assert record.operation == "DescribeInstances"
        assert record.is_read_only
        assert record.is_success

    def test_is_read_only(self):
        """Test read-only check."""
        read_record = APICallRecord(
            timestamp=datetime.utcnow(),
            duration_ms=100,
            service="ec2",
            operation="DescribeInstances",
            region="us-east-1",
            request_id="req-1",
            category=APICategory.READ,
        )
        assert read_record.is_read_only

        write_record = APICallRecord(
            timestamp=datetime.utcnow(),
            duration_ms=100,
            service="ec2",
            operation="RunInstances",
            region="us-east-1",
            request_id="req-2",
            category=APICategory.WRITE,
        )
        assert not write_record.is_read_only

    def test_is_success(self):
        """Test success check."""
        success = APICallRecord(
            timestamp=datetime.utcnow(),
            duration_ms=100,
            service="ec2",
            operation="DescribeInstances",
            region="us-east-1",
            request_id="req-1",
            category=APICategory.READ,
            http_status=200,
        )
        assert success.is_success

        error = APICallRecord(
            timestamp=datetime.utcnow(),
            duration_ms=100,
            service="ec2",
            operation="DescribeInstances",
            region="us-east-1",
            request_id="req-2",
            category=APICategory.READ,
            http_status=403,
            error_code="AccessDenied",
        )
        assert not error.is_success

    def test_to_dict(self):
        """Test serialization."""
        record = APICallRecord(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            duration_ms=150,
            service="ec2",
            operation="DescribeInstances",
            region="us-east-1",
            request_id="req-12345",
            category=APICategory.READ,
            account_id="123456789012",
        )

        data = record.to_dict()
        assert data["service"] == "ec2"
        assert data["operation"] == "DescribeInstances"
        assert data["is_read_only"] is True
        assert data["category"] == "read"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "timestamp": "2024-01-15T10:30:00",
            "duration_ms": 150,
            "service": "ec2",
            "operation": "DescribeInstances",
            "region": "us-east-1",
            "request_id": "req-12345",
            "category": "read",
        }

        record = APICallRecord.from_dict(data)
        assert record.service == "ec2"
        assert record.operation == "DescribeInstances"
        assert record.category == APICategory.READ


class TestAuditSession:
    """Test AuditSession model."""

    def test_create_session(self):
        """Test creating an audit session."""
        session = AuditSession(
            session_id="sess-12345",
            session_name="production_scan",
        )

        assert session.session_id == "sess-12345"
        assert session.total_calls == 0
        assert session.is_read_only

    def test_add_record(self):
        """Test adding records to session."""
        session = AuditSession(session_id="sess-1")

        # Add read calls
        for i in range(5):
            session.add_record(
                APICallRecord(
                    timestamp=datetime.utcnow(),
                    duration_ms=100,
                    service="ec2",
                    operation="DescribeInstances",
                    region="us-east-1",
                    request_id=f"req-{i}",
                    category=APICategory.READ,
                )
            )

        assert session.total_calls == 5
        assert session.read_calls == 5
        assert session.is_read_only
        assert session.read_only_percentage == 100.0

    def test_mixed_operations(self):
        """Test session with mixed operations."""
        session = AuditSession(session_id="sess-1")

        # 3 read, 1 write, 1 delete
        for _ in range(3):
            session.add_record(
                APICallRecord(
                    timestamp=datetime.utcnow(),
                    duration_ms=100,
                    service="ec2",
                    operation="DescribeInstances",
                    region="us-east-1",
                    request_id="req-r",
                    category=APICategory.READ,
                )
            )

        session.add_record(
            APICallRecord(
                timestamp=datetime.utcnow(),
                duration_ms=100,
                service="ec2",
                operation="RunInstances",
                region="us-east-1",
                request_id="req-w",
                category=APICategory.WRITE,
            )
        )

        session.add_record(
            APICallRecord(
                timestamp=datetime.utcnow(),
                duration_ms=100,
                service="ec2",
                operation="TerminateInstances",
                region="us-east-1",
                request_id="req-d",
                category=APICategory.DELETE,
            )
        )

        assert session.total_calls == 5
        assert session.read_calls == 3
        assert session.write_calls == 1
        assert session.delete_calls == 1
        assert not session.is_read_only
        assert session.read_only_percentage == 60.0

    def test_close_session(self):
        """Test closing a session."""
        session = AuditSession(session_id="sess-1")
        assert session.end_time is None
        assert session.duration_seconds is None

        session.close()
        assert session.end_time is not None
        assert session.duration_seconds is not None
        assert session.duration_seconds >= 0

    def test_to_dict(self):
        """Test session serialization."""
        session = AuditSession(
            session_id="sess-12345",
            session_name="test_scan",
            metadata={"environment": "production"},
        )
        session.add_record(
            APICallRecord(
                timestamp=datetime.utcnow(),
                duration_ms=100,
                service="ec2",
                operation="DescribeInstances",
                region="us-east-1",
                request_id="req-1",
                category=APICategory.READ,
            )
        )
        session.close()

        data = session.to_dict()
        assert data["session_id"] == "sess-12345"
        assert data["session_name"] == "test_scan"
        assert data["total_calls"] == 1
        assert data["is_read_only"] is True
        assert "production" in str(data["metadata"])

    def test_from_dict(self):
        """Test session deserialization."""
        data = {
            "session_id": "sess-12345",
            "session_name": "test_scan",
            "start_time": "2024-01-15T10:00:00",
            "end_time": "2024-01-15T10:30:00",
            "total_calls": 10,
            "read_calls": 10,
            "write_calls": 0,
            "delete_calls": 0,
            "admin_calls": 0,
        }

        session = AuditSession.from_dict(data)
        assert session.session_id == "sess-12345"
        assert session.total_calls == 10
        assert session.is_read_only


class TestOperationClassifier:
    """Test OperationClassifier."""

    def test_read_operations(self):
        """Test classification of read operations."""
        assert classifier.classify("DescribeInstances") == APICategory.READ
        assert classifier.classify("GetBucketLocation") == APICategory.READ
        assert classifier.classify("ListObjects") == APICategory.READ
        assert classifier.classify("HeadObject") == APICategory.READ
        assert classifier.classify("LookupEvents") == APICategory.READ
        assert classifier.classify("SearchProducts") == APICategory.READ

    def test_write_operations(self):
        """Test classification of write operations."""
        assert classifier.classify("CreateBucket") == APICategory.WRITE
        assert classifier.classify("PutObject") == APICategory.WRITE
        assert classifier.classify("UpdateTable") == APICategory.WRITE
        assert classifier.classify("ModifyInstanceAttribute") == APICategory.WRITE
        assert classifier.classify("TagResource") == APICategory.WRITE
        assert classifier.classify("StartInstances") == APICategory.WRITE

    def test_delete_operations(self):
        """Test classification of delete operations."""
        assert classifier.classify("DeleteBucket") == APICategory.DELETE
        assert classifier.classify("RemoveTagsFromResource") == APICategory.DELETE
        assert classifier.classify("TerminateInstances") == APICategory.DELETE
        assert classifier.classify("DetachVolume") == APICategory.DELETE
        assert classifier.classify("StopInstances") == APICategory.DELETE
        assert classifier.classify("CancelSpotInstanceRequests") == APICategory.DELETE

    def test_admin_operations(self):
        """Test classification of admin operations."""
        assert classifier.classify("CreateUser") == APICategory.ADMIN
        assert classifier.classify("DeleteRole") == APICategory.ADMIN
        assert classifier.classify("AttachRolePolicy") == APICategory.ADMIN
        assert classifier.classify("AssumeRole") == APICategory.ADMIN
        assert classifier.classify("CreateOrganization") == APICategory.ADMIN

    def test_special_cases(self):
        """Test special case classifications."""
        # S3 special cases
        assert classifier.classify("HeadBucket") == APICategory.READ
        assert classifier.classify("GetBucketAcl") == APICategory.READ
        assert classifier.classify("PutBucketPolicy") == APICategory.WRITE
        assert classifier.classify("AbortMultipartUpload") == APICategory.DELETE

        # EC2 special cases
        assert classifier.classify("RunInstances") == APICategory.WRITE
        assert classifier.classify("TerminateInstances") == APICategory.DELETE
        assert classifier.classify("AuthorizeSecurityGroupIngress") == APICategory.WRITE
        assert classifier.classify("RevokeSecurityGroupEgress") == APICategory.DELETE

        # STS read-like operations
        assert classifier.classify("GetCallerIdentity") == APICategory.READ

    def test_is_read_only(self):
        """Test is_read_only helper."""
        assert classifier.is_read_only("DescribeInstances")
        assert classifier.is_read_only("GetObject")
        assert not classifier.is_read_only("CreateBucket")
        assert not classifier.is_read_only("DeleteObject")

    def test_is_destructive(self):
        """Test is_destructive helper."""
        assert not classifier.is_destructive("DescribeInstances")
        assert classifier.is_destructive("CreateInstance")
        assert classifier.is_destructive("DeleteBucket")
        assert classifier.is_destructive("AssumeRole")

    def test_classify_with_confidence(self):
        """Test classification with confidence level."""
        # Exact match (special case)
        cat, conf = classifier.classify_with_confidence("TerminateInstances")
        assert cat == APICategory.DELETE
        assert conf == "exact"

        # Prefix match
        cat2, conf2 = classifier.classify_with_confidence("DescribeNewOperation")
        assert cat2 == APICategory.READ
        assert conf2 == "prefix"

        # Unknown
        cat3, conf3 = classifier.classify_with_confidence("CompletelyUnknownOp")
        assert cat3 == APICategory.UNKNOWN
        assert conf3 == "unknown"


class TestTrustCenter:
    """Test TrustCenter singleton."""

    def setup_method(self):
        """Reset TrustCenter before each test."""
        TrustCenter.reset_instance()

    def teardown_method(self):
        """Clean up after each test."""
        TrustCenter.reset_instance()

    def test_singleton_pattern(self):
        """Test singleton pattern."""
        tc1 = TrustCenter.get_instance()
        tc2 = TrustCenter.get_instance()
        assert tc1 is tc2

    def test_initial_state(self):
        """Test initial state."""
        tc = TrustCenter.get_instance()
        assert not tc.is_enabled
        assert tc.get_current_session() is None

    def test_quick_summary(self):
        """Test quick summary generation."""
        tc = TrustCenter.get_instance()
        summary = tc.get_quick_summary()

        assert "enabled" in summary
        assert "total_calls" in summary
        assert "read_only_percentage" in summary
        assert summary["is_fully_read_only"] is True

    def test_session_management(self):
        """Test session creation and management."""
        tc = TrustCenter.get_instance()

        with tc.session("test_scan", metadata={"env": "test"}) as session_id:
            assert session_id is not None
            assert tc.get_current_session() is not None

            current = tc.get_current_session()
            assert current.session_name == "test_scan"

        # After context exits
        # Session should be saved
        session = tc.get_session(session_id)
        assert session is not None
        assert session.end_time is not None

    def test_record_manual(self):
        """Test manual API call recording."""
        tc = TrustCenter.get_instance()

        with tc.session("manual_test") as session_id:
            tc.record_manual(
                service="ec2",
                operation="DescribeInstances",
                region="us-east-1",
                duration_ms=100,
            )

            tc.record_manual(
                service="s3",
                operation="ListBuckets",
                region="us-east-1",
                duration_ms=50,
            )

        session = tc.get_session(session_id)
        assert session.total_calls == 2
        assert session.read_calls == 2
        assert session.is_read_only

    def test_generate_report(self):
        """Test report generation."""
        tc = TrustCenter.get_instance()

        with tc.session("report_test") as session_id:
            for i in range(5):
                tc.record_manual(
                    service="ec2",
                    operation="DescribeInstances",
                    region="us-east-1",
                    duration_ms=100 + i,
                )

        report = tc.generate_report(session_ids=[session_id])

        assert report.total_sessions == 1
        assert report.total_api_calls == 5
        assert report.read_only_percentage == 100.0
        assert report.is_fully_read_only
        assert "COMPLIANT" in report.compliance_statement

    def test_report_with_write_operations(self):
        """Test report with non-read operations."""
        tc = TrustCenter.get_instance()

        with tc.session("mixed_test") as session_id:
            # 3 reads
            for _ in range(3):
                tc.record_manual(
                    service="ec2",
                    operation="DescribeInstances",
                    region="us-east-1",
                )
            # 1 write
            tc.record_manual(
                service="ec2",
                operation="RunInstances",
                region="us-east-1",
            )

        report = tc.generate_report(session_ids=[session_id])

        assert not report.is_fully_read_only
        assert report.read_only_percentage == 75.0
        assert "WARNING" in report.compliance_statement
        assert "RunInstances" in report.write_operations

    def test_list_sessions(self):
        """Test session listing."""
        tc = TrustCenter.get_instance()

        with tc.session("session_1"):
            pass
        with tc.session("session_2"):
            pass
        with tc.session("session_3"):
            pass

        sessions = tc.list_sessions()
        assert len(sessions) == 3

    def test_clear_sessions(self):
        """Test clearing sessions."""
        tc = TrustCenter.get_instance()

        with tc.session("test"):
            pass

        count = tc.clear_sessions()
        assert count == 1
        assert len(tc.list_sessions()) == 0


class TestTrustCenterReport:
    """Test TrustCenterReport model."""

    def test_to_dict(self):
        """Test report serialization."""
        report = TrustCenterReport(
            report_id="rpt-12345",
            generated_at=datetime(2024, 1, 15, 12, 0, 0),
            report_period_start=datetime(2024, 1, 1),
            report_period_end=datetime(2024, 1, 15),
            tool_name="RepliMap",
            tool_version="1.0.0",
            total_sessions=5,
            total_api_calls=100,
            total_duration_seconds=300.0,
            read_only_percentage=100.0,
            is_fully_read_only=True,
            calls_by_category={"read": 100},
            unique_services=["ec2", "s3", "rds"],
            calls_by_service={"ec2": 50, "s3": 30, "rds": 20},
            unique_operations=["DescribeInstances", "ListBuckets"],
            write_operations=[],
            total_errors=0,
            error_rate_percentage=0.0,
            compliance_statement="COMPLIANT: 100% READ-ONLY",
            session_summaries=[],
        )

        data = report.to_dict()
        assert data["report_id"] == "rpt-12345"
        assert data["summary"]["total_api_calls"] == 100
        assert data["summary"]["is_fully_read_only"] is True
        assert "ec2" in data["unique_services"]


class TestExporters:
    """Test export utilities."""

    def test_export_json(self):
        """Test JSON export."""
        report = TrustCenterReport(
            report_id="rpt-12345",
            generated_at=datetime.utcnow(),
            report_period_start=datetime.utcnow() - timedelta(days=7),
            report_period_end=datetime.utcnow(),
            tool_name="RepliMap",
            tool_version="1.0.0",
            total_sessions=1,
            total_api_calls=10,
            total_duration_seconds=60.0,
            read_only_percentage=100.0,
            is_fully_read_only=True,
            calls_by_category={"read": 10},
            unique_services=["ec2"],
            calls_by_service={"ec2": 10},
            unique_operations=["DescribeInstances"],
            write_operations=[],
            total_errors=0,
            error_rate_percentage=0.0,
            compliance_statement="COMPLIANT",
            session_summaries=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.json"
            export_json(report, path)

            assert path.exists()
            content = path.read_text()
            assert "rpt-12345" in content
            assert "RepliMap" in content

    def test_export_csv(self):
        """Test CSV export."""
        session = AuditSession(session_id="sess-1", session_name="test")
        session.add_record(
            APICallRecord(
                timestamp=datetime.utcnow(),
                duration_ms=100,
                service="ec2",
                operation="DescribeInstances",
                region="us-east-1",
                request_id="req-1",
                category=APICategory.READ,
            )
        )
        session.add_record(
            APICallRecord(
                timestamp=datetime.utcnow(),
                duration_ms=150,
                service="s3",
                operation="ListBuckets",
                region="us-east-1",
                request_id="req-2",
                category=APICategory.READ,
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "records.csv"
            export_csv([session], path)

            assert path.exists()
            content = path.read_text()
            assert "Session ID" in content
            assert "DescribeInstances" in content
            assert "ListBuckets" in content

    def test_export_summary_csv(self):
        """Test summary CSV export."""
        report = TrustCenterReport(
            report_id="rpt-12345",
            generated_at=datetime.utcnow(),
            report_period_start=datetime.utcnow() - timedelta(days=7),
            report_period_end=datetime.utcnow(),
            tool_name="RepliMap",
            tool_version="1.0.0",
            total_sessions=2,
            total_api_calls=50,
            total_duration_seconds=120.0,
            read_only_percentage=100.0,
            is_fully_read_only=True,
            calls_by_category={"read": 50},
            unique_services=["ec2", "s3"],
            calls_by_service={"ec2": 30, "s3": 20},
            unique_operations=["DescribeInstances", "ListBuckets"],
            write_operations=[],
            total_errors=0,
            error_rate_percentage=0.0,
            compliance_statement="COMPLIANT: 100% READ-ONLY",
            session_summaries=[
                {"session_id": "sess-1", "session_name": "scan1", "total_calls": 30},
                {"session_id": "sess-2", "session_name": "scan2", "total_calls": 20},
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "summary.csv"
            export_summary_csv(report, path)

            assert path.exists()
            content = path.read_text()
            assert "Trust Center Audit Report" in content
            assert "Total API Calls" in content
            assert "50" in content

    def test_generate_compliance_text(self):
        """Test compliance text generation."""
        report = TrustCenterReport(
            report_id="rpt-12345",
            generated_at=datetime.utcnow(),
            report_period_start=datetime.utcnow() - timedelta(days=7),
            report_period_end=datetime.utcnow(),
            tool_name="RepliMap",
            tool_version="1.0.0",
            total_sessions=1,
            total_api_calls=100,
            total_duration_seconds=300.0,
            read_only_percentage=100.0,
            is_fully_read_only=True,
            calls_by_category={"read": 100},
            unique_services=["ec2"],
            calls_by_service={"ec2": 100},
            unique_operations=["DescribeInstances"],
            write_operations=[],
            total_errors=0,
            error_rate_percentage=0.0,
            compliance_statement="COMPLIANT: 100% READ-ONLY operations",
            session_summaries=[],
        )

        text = generate_compliance_text(report)

        assert "TRUST CENTER COMPLIANCE REPORT" in text
        assert "EXECUTIVE SUMMARY" in text
        assert "Read-Only Operations" in text
        assert "100.0%" in text
        assert "COMPLIANT" in text

    def test_save_compliance_text(self):
        """Test saving compliance text."""
        report = TrustCenterReport(
            report_id="rpt-12345",
            generated_at=datetime.utcnow(),
            report_period_start=datetime.utcnow() - timedelta(days=7),
            report_period_end=datetime.utcnow(),
            tool_name="RepliMap",
            tool_version="1.0.0",
            total_sessions=1,
            total_api_calls=10,
            total_duration_seconds=60.0,
            read_only_percentage=100.0,
            is_fully_read_only=True,
            calls_by_category={"read": 10},
            unique_services=["ec2"],
            calls_by_service={"ec2": 10},
            unique_operations=["DescribeInstances"],
            write_operations=[],
            total_errors=0,
            error_rate_percentage=0.0,
            compliance_statement="COMPLIANT",
            session_summaries=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "compliance.txt"
            save_compliance_text(report, path)

            assert path.exists()
            content = path.read_text()
            assert "TRUST CENTER" in content


class TestAuditHooksUnit:
    """Unit tests for AuditHooks (without boto3)."""

    def test_sensitive_params(self):
        """Test sensitive parameter list."""
        from replimap.audit.hooks import AuditHooks

        hooks = AuditHooks()
        sensitive = hooks.SENSITIVE_PARAMS

        assert "Password" in sensitive
        assert "SecretKey" in sensitive
        assert "AccessKey" in sensitive
        assert "SessionToken" in sensitive
        assert "MasterUserPassword" in sensitive

    def test_sanitize_params(self):
        """Test parameter sanitization."""
        from replimap.audit.hooks import AuditHooks

        hooks = AuditHooks()

        params = {
            "BucketName": "my-bucket",
            "Password": "secret123",
            "MasterUserPassword": "admin-secret",
            "Tags": [{"Key": "Name", "Value": "test"}],
            "Credentials": {"AccessKey": "AKIAIOSFODNN7EXAMPLE"},
        }

        sanitized = hooks._sanitize_params(params)

        assert sanitized["BucketName"] == "my-bucket"
        assert sanitized["Password"] == "***REDACTED***"
        assert sanitized["MasterUserPassword"] == "***REDACTED***"
        assert sanitized["Tags"] == [{"Key": "Name", "Value": "test"}]
        assert sanitized["Credentials"]["AccessKey"] == "***REDACTED***"

    def test_registered_session_count(self):
        """Test session count property."""
        from replimap.audit.hooks import AuditHooks

        hooks = AuditHooks()
        assert hooks.registered_session_count == 0
