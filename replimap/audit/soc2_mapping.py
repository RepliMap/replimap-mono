"""
SOC2 Trust Service Criteria Mapping for Checkov Findings.

Maps Checkov check IDs to SOC2 controls for compliance reporting.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SOC2Control:
    """SOC2 Trust Service Criteria control mapping."""

    control: str
    category: str
    description: str


# Mapping of Checkov check IDs to SOC2 controls
# Comprehensive mapping covering 100+ Checkov AWS checks
SOC2_MAPPING: dict[str, SOC2Control] = {
    # =========================================================================
    # CC6.1 - Logical and Physical Access Controls
    # =========================================================================
    "CKV_AWS_40": SOC2Control("CC6.1", "Access Control", "IAM Password Policy"),
    "CKV_AWS_41": SOC2Control("CC6.1", "Access Control", "Root Account MFA"),
    "CKV_AWS_23": SOC2Control(
        "CC6.1", "Access Control", "Security Group Ingress Restriction"
    ),
    "CKV_AWS_24": SOC2Control(
        "CC6.1", "Access Control", "Security Group SSH Restriction"
    ),
    "CKV_AWS_25": SOC2Control(
        "CC6.1", "Access Control", "Security Group RDP Restriction"
    ),
    "CKV_AWS_49": SOC2Control("CC6.1", "Access Control", "IAM Policy Least Privilege"),
    "CKV_AWS_62": SOC2Control("CC6.1", "Access Control", "Lambda Not Public"),
    "CKV_AWS_26": SOC2Control("CC6.1", "Access Control", "SNS Topic Encryption"),
    # Additional CC6.1 - Access Control
    "CKV_AWS_1": SOC2Control("CC6.1", "Access Control", "S3 Bucket ACL Not Public"),
    "CKV_AWS_53": SOC2Control("CC6.1", "Access Control", "S3 Public Access Block Account"),
    "CKV_AWS_54": SOC2Control("CC6.1", "Access Control", "S3 Block Public ACLs"),
    "CKV_AWS_55": SOC2Control("CC6.1", "Access Control", "S3 Block Public Policy"),
    "CKV_AWS_56": SOC2Control("CC6.1", "Access Control", "S3 Ignore Public ACLs"),
    "CKV_AWS_57": SOC2Control("CC6.1", "Access Control", "S3 Restrict Public Buckets"),
    "CKV_AWS_70": SOC2Control("CC6.1", "Access Control", "Sagemaker Endpoint Config Encryption"),
    "CKV_AWS_79": SOC2Control("CC6.1", "Access Control", "EC2 IMDSv2 Required"),
    "CKV_AWS_8": SOC2Control("CC6.1", "Access Control", "Launch Config Public IP"),
    "CKV_AWS_88": SOC2Control("CC6.1", "Access Control", "EC2 in VPC"),
    "CKV_AWS_92": SOC2Control("CC6.1", "Access Control", "ELB v2 Listener TLS"),
    "CKV_AWS_97": SOC2Control("CC6.1", "Access Control", "ECS Task Definition User"),
    "CKV_AWS_107": SOC2Control("CC6.1", "Access Control", "IAM Policy Wildcard Actions"),
    "CKV_AWS_108": SOC2Control("CC6.1", "Access Control", "IAM Policy Wildcard Resources"),
    "CKV_AWS_109": SOC2Control("CC6.1", "Access Control", "IAM Policy Permissions Boundary"),
    "CKV_AWS_110": SOC2Control("CC6.1", "Access Control", "IAM Policy Allow Privilege Escalation"),
    "CKV_AWS_111": SOC2Control("CC6.1", "Access Control", "IAM Policy Write Access"),
    "CKV_AWS_130": SOC2Control("CC6.1", "Access Control", "VPC Subnet Public IP"),
    "CKV_AWS_142": SOC2Control("CC6.1", "Access Control", "RDS IAM Auth Enabled"),
    "CKV_AWS_161": SOC2Control("CC6.1", "Access Control", "RDS Publicly Accessible"),
    "CKV_AWS_226": SOC2Control("CC6.1", "Access Control", "ALB Drop Invalid Headers"),
    # =========================================================================
    # CC6.6 - Encryption at Rest
    # =========================================================================
    "CKV_AWS_19": SOC2Control("CC6.6", "Encryption", "S3 Bucket Encryption"),
    "CKV_AWS_3": SOC2Control("CC6.6", "Encryption", "EBS Volume Encryption"),
    "CKV_AWS_16": SOC2Control("CC6.6", "Encryption", "RDS Instance Encryption"),
    "CKV_AWS_17": SOC2Control("CC6.6", "Encryption", "RDS Snapshot Encryption"),
    "CKV_AWS_27": SOC2Control("CC6.6", "Encryption", "SQS Queue Encryption"),
    "CKV_AWS_7": SOC2Control("CC6.6", "Encryption", "KMS Key Rotation"),
    "CKV_AWS_33": SOC2Control("CC6.6", "Encryption", "KMS CMK Policy"),
    "CKV_AWS_64": SOC2Control("CC6.6", "Encryption", "Redshift Cluster Encryption"),
    "CKV_AWS_65": SOC2Control("CC6.6", "Encryption", "ECR Repository Encryption"),
    "CKV_AWS_84": SOC2Control("CC6.6", "Encryption", "ElastiCache Encryption at Rest"),
    # Additional CC6.6 - Encryption at Rest
    "CKV_AWS_34": SOC2Control("CC6.6", "Encryption", "CloudWatch Log Group Encryption"),
    "CKV_AWS_37": SOC2Control("CC6.6", "Encryption", "ECS Task Definition Encryption"),
    "CKV_AWS_47": SOC2Control("CC6.6", "Encryption", "DAX Cluster Encryption"),
    "CKV_AWS_58": SOC2Control("CC6.6", "Encryption", "EKS Secrets Encryption"),
    "CKV_AWS_63": SOC2Control("CC6.6", "Encryption", "CloudWatch Log Group Encryption v2"),
    "CKV_AWS_68": SOC2Control("CC6.6", "Encryption", "Neptune Cluster Encryption"),
    "CKV_AWS_69": SOC2Control("CC6.6", "Encryption", "OpenSearch Domain Encryption"),
    "CKV_AWS_74": SOC2Control("CC6.6", "Encryption", "DocumentDB Cluster Encryption"),
    "CKV_AWS_77": SOC2Control("CC6.6", "Encryption", "OpenSearch Fine-Grained Access"),
    "CKV_AWS_85": SOC2Control("CC6.6", "Encryption", "DocDB TLS Enabled"),
    "CKV_AWS_87": SOC2Control("CC6.6", "Encryption", "Redshift Enhanced VPC Routing"),
    "CKV_AWS_89": SOC2Control("CC6.6", "Encryption", "DMS Replication Instance Encryption"),
    "CKV_AWS_90": SOC2Control("CC6.6", "Encryption", "OpenSearch Encryption at Rest"),
    "CKV_AWS_99": SOC2Control("CC6.6", "Encryption", "Glue Data Catalog Encryption"),
    "CKV_AWS_100": SOC2Control("CC6.6", "Encryption", "Glue Connection SSL"),
    "CKV_AWS_101": SOC2Control("CC6.6", "Encryption", "Neptune Storage Encryption"),
    "CKV_AWS_119": SOC2Control("CC6.6", "Encryption", "DynamoDB Encryption"),
    "CKV_AWS_120": SOC2Control("CC6.6", "Encryption", "API Gateway Cache Encryption"),
    "CKV_AWS_122": SOC2Control("CC6.6", "Encryption", "CodeBuild Project Encryption"),
    "CKV_AWS_131": SOC2Control("CC6.6", "Encryption", "ALB Listener HTTPS"),
    "CKV_AWS_135": SOC2Control("CC6.6", "Encryption", "EC2 EBS Default Encryption"),
    "CKV_AWS_136": SOC2Control("CC6.6", "Encryption", "ECR Image Tag Immutable"),
    "CKV_AWS_149": SOC2Control("CC6.6", "Encryption", "Secrets Manager KMS Encryption"),
    "CKV_AWS_163": SOC2Control("CC6.6", "Encryption", "ECR Image Scan on Push"),
    "CKV_AWS_189": SOC2Control("CC6.6", "Encryption", "EFS Encryption at Rest"),
    "CKV_AWS_191": SOC2Control("CC6.6", "Encryption", "Lambda Environment Encryption"),
    # =========================================================================
    # CC6.7 - Encryption in Transit
    # =========================================================================
    "CKV_AWS_2": SOC2Control("CC6.7", "Encryption", "ALB HTTPS/TLS"),
    "CKV_AWS_20": SOC2Control("CC6.7", "Encryption", "S3 Bucket SSL Only"),
    "CKV_AWS_83": SOC2Control(
        "CC6.7", "Encryption", "ElastiCache Encryption in Transit"
    ),
    "CKV_AWS_103": SOC2Control("CC6.7", "Encryption", "ALB TLS 1.2+"),
    # Additional CC6.7 - Encryption in Transit
    "CKV_AWS_38": SOC2Control("CC6.7", "Encryption", "EKS Public Access Disabled"),
    "CKV_AWS_39": SOC2Control("CC6.7", "Encryption", "EKS Control Plane Logging"),
    "CKV_AWS_46": SOC2Control("CC6.7", "Encryption", "Secrets Manager Rotation"),
    "CKV_AWS_59": SOC2Control("CC6.7", "Encryption", "API Gateway Authorizer"),
    "CKV_AWS_86": SOC2Control("CC6.7", "Encryption", "CloudFront Origin Access Identity"),
    "CKV_AWS_93": SOC2Control("CC6.7", "Encryption", "CloudFront Viewer TLS 1.2"),
    "CKV_AWS_94": SOC2Control("CC6.7", "Encryption", "CloudFront Encryption in Transit"),
    "CKV_AWS_96": SOC2Control("CC6.7", "Encryption", "EMR Security Configuration"),
    "CKV_AWS_102": SOC2Control("CC6.7", "Encryption", "CloudFront Field Level Encryption"),
    "CKV_AWS_105": SOC2Control("CC6.7", "Encryption", "RDS TLS Enforcement"),
    "CKV_AWS_106": SOC2Control("CC6.7", "Encryption", "OpenSearch Node-to-Node Encryption"),
    "CKV_AWS_172": SOC2Control("CC6.7", "Encryption", "CloudFront SSL Protocol"),
    "CKV_AWS_173": SOC2Control("CC6.7", "Encryption", "API Gateway TLS 1.2"),
    "CKV_AWS_174": SOC2Control("CC6.7", "Encryption", "CloudWatch Log Group TLS"),
    # =========================================================================
    # CC7.2 - Monitoring and Detection
    # =========================================================================
    "CKV_AWS_67": SOC2Control("CC7.2", "Monitoring", "CloudTrail Enabled"),
    "CKV_AWS_21": SOC2Control("CC7.2", "Monitoring", "S3 Bucket Logging"),
    "CKV_AWS_48": SOC2Control("CC7.2", "Monitoring", "VPC Flow Logs Enabled"),
    "CKV_AWS_35": SOC2Control("CC7.2", "Monitoring", "CloudTrail Log Validation"),
    "CKV_AWS_36": SOC2Control(
        "CC7.2", "Monitoring", "CloudTrail S3 Bucket Access Logging"
    ),
    "CKV_AWS_50": SOC2Control("CC7.2", "Monitoring", "Lambda X-Ray Tracing"),
    "CKV_AWS_76": SOC2Control("CC7.2", "Monitoring", "API Gateway Access Logging"),
    "CKV_AWS_91": SOC2Control("CC7.2", "Monitoring", "RDS Enhanced Monitoring"),
    "CKV_AWS_104": SOC2Control("CC7.2", "Monitoring", "ALB Access Logging"),
    # Additional CC7.2 - Monitoring
    "CKV_AWS_66": SOC2Control("CC7.2", "Monitoring", "CloudWatch Log Group Retention"),
    "CKV_AWS_73": SOC2Control("CC7.2", "Monitoring", "API Gateway Execution Logging"),
    "CKV_AWS_75": SOC2Control("CC7.2", "Monitoring", "API Gateway Detailed Metrics"),
    "CKV_AWS_80": SOC2Control("CC7.2", "Monitoring", "MSK Cluster Logging"),
    "CKV_AWS_81": SOC2Control("CC7.2", "Monitoring", "MSK Cluster TLS"),
    "CKV_AWS_82": SOC2Control("CC7.2", "Monitoring", "Athena Workgroup Encryption"),
    "CKV_AWS_95": SOC2Control("CC7.2", "Monitoring", "WAF Web ACL Logging"),
    "CKV_AWS_118": SOC2Control("CC7.2", "Monitoring", "RDS Performance Insights"),
    "CKV_AWS_126": SOC2Control("CC7.2", "Monitoring", "Postgres Log Connections"),
    "CKV_AWS_127": SOC2Control("CC7.2", "Monitoring", "Postgres Log Disconnections"),
    "CKV_AWS_129": SOC2Control("CC7.2", "Monitoring", "Postgres Log Hostname"),
    "CKV_AWS_133": SOC2Control("CC7.2", "Monitoring", "CloudTrail CloudWatch Logs"),
    "CKV_AWS_153": SOC2Control("CC7.2", "Monitoring", "Lambda Function URLs Auth"),
    "CKV_AWS_158": SOC2Control("CC7.2", "Monitoring", "Lambda Tracing Active"),
    "CKV_AWS_162": SOC2Control("CC7.2", "Monitoring", "Transfer Server Logging"),
    "CKV_AWS_184": SOC2Control("CC7.2", "Monitoring", "OpenSearch Audit Logging"),
    # =========================================================================
    # CC7.3 - Incident Response
    # =========================================================================
    "CKV_AWS_52": SOC2Control("CC7.3", "Incident Response", "GuardDuty Enabled"),
    "CKV_AWS_78": SOC2Control("CC7.3", "Incident Response", "Config Rule Enabled"),
    # Additional CC7.3 - Incident Response
    "CKV_AWS_121": SOC2Control("CC7.3", "Incident Response", "Security Hub Enabled"),
    "CKV_AWS_160": SOC2Control("CC7.3", "Incident Response", "GuardDuty S3 Protection"),
    # =========================================================================
    # CC8.1 - Change Management
    # =========================================================================
    "CKV_AWS_18": SOC2Control("CC8.1", "Change Mgmt", "S3 Bucket Versioning"),
    "CKV_AWS_4": SOC2Control("CC8.1", "Change Mgmt", "EBS Snapshot Encryption"),
    # Additional CC8.1 - Change Management
    "CKV_AWS_132": SOC2Control("CC8.1", "Change Mgmt", "S3 Object Lock"),
    "CKV_AWS_137": SOC2Control("CC8.1", "Change Mgmt", "AMI Encryption"),
    "CKV_AWS_144": SOC2Control("CC8.1", "Change Mgmt", "S3 Cross-Region Replication"),
    "CKV_AWS_145": SOC2Control("CC8.1", "Change Mgmt", "S3 Bucket Key Enabled"),
    # =========================================================================
    # A1.2 - Availability
    # =========================================================================
    "CKV_AWS_5": SOC2Control("A1.2", "Availability", "DocumentDB Backup Retention"),
    "CKV_AWS_15": SOC2Control("A1.2", "Availability", "RDS Multi-AZ"),
    "CKV_AWS_28": SOC2Control("A1.2", "Availability", "DynamoDB Backup Enabled"),
    "CKV_AWS_128": SOC2Control("A1.2", "Availability", "RDS Deletion Protection"),
    # Additional A1.2 - Availability
    "CKV_AWS_6": SOC2Control("A1.2", "Availability", "ElastiCache Failover"),
    "CKV_AWS_29": SOC2Control("A1.2", "Availability", "Elasticsearch in VPC"),
    "CKV_AWS_44": SOC2Control("A1.2", "Availability", "Neptune Multi-AZ"),
    "CKV_AWS_71": SOC2Control("A1.2", "Availability", "Redshift Cluster Backup"),
    "CKV_AWS_72": SOC2Control("A1.2", "Availability", "Redshift Audit Logging"),
    "CKV_AWS_123": SOC2Control("A1.2", "Availability", "Auto-Scaling Multi-AZ"),
    "CKV_AWS_139": SOC2Control("A1.2", "Availability", "RDS Backup Retention 7+ Days"),
    "CKV_AWS_143": SOC2Control("A1.2", "Availability", "DynamoDB PITR"),
    "CKV_AWS_157": SOC2Control("A1.2", "Availability", "RDS Backup Retention Set"),
    "CKV_AWS_165": SOC2Control("A1.2", "Availability", "Auto-Scaling Health Check"),
    "CKV_AWS_192": SOC2Control("A1.2", "Availability", "DynamoDB Auto-Scaling"),
    # =========================================================================
    # C1.2 - Confidentiality
    # =========================================================================
    "CKV_AWS_10": SOC2Control("C1.2", "Confidentiality", "Launch Config Encrypted"),
    "CKV_AWS_45": SOC2Control("C1.2", "Confidentiality", "Lambda Env Encryption"),
    "CKV_AWS_60": SOC2Control("C1.2", "Confidentiality", "Lambda VPC Config"),
    "CKV_AWS_61": SOC2Control("C1.2", "Confidentiality", "Lambda DLQ Configured"),
    "CKV_AWS_98": SOC2Control("C1.2", "Confidentiality", "Sagemaker Notebook Root Access"),
    "CKV_AWS_115": SOC2Control("C1.2", "Confidentiality", "Lambda Reserved Concurrency"),
    "CKV_AWS_116": SOC2Control("C1.2", "Confidentiality", "Lambda DLQ or OnFailure"),
    "CKV_AWS_117": SOC2Control("C1.2", "Confidentiality", "Lambda in VPC"),
    "CKV_AWS_138": SOC2Control("C1.2", "Confidentiality", "EKS Private Endpoint"),
    "CKV_AWS_150": SOC2Control("C1.2", "Confidentiality", "EKS Endpoint Private Access"),
    # =========================================================================
    # P1.1 - Processing Integrity
    # =========================================================================
    "CKV_AWS_9": SOC2Control("P1.1", "Processing Integrity", "IAM CloudShell Access"),
    "CKV_AWS_12": SOC2Control("P1.1", "Processing Integrity", "Default VPC Not Used"),
    "CKV_AWS_13": SOC2Control("P1.1", "Processing Integrity", "Root Account Hardware MFA"),
    "CKV_AWS_14": SOC2Control("P1.1", "Processing Integrity", "Root Account Virtual MFA"),
    "CKV_AWS_51": SOC2Control("P1.1", "Processing Integrity", "ECR Lifecycle Policy"),
    "CKV_AWS_134": SOC2Control("P1.1", "Processing Integrity", "VPC Internet Gateway"),
}


def get_soc2_mapping(check_id: str) -> SOC2Control | None:
    """
    Get SOC2 control mapping for a Checkov check ID.

    Args:
        check_id: Checkov check ID (e.g., "CKV_AWS_19")

    Returns:
        SOC2Control if mapping exists, None otherwise
    """
    return SOC2_MAPPING.get(check_id)


def get_soc2_summary(check_ids: list[str]) -> dict[str, dict[str, int]]:
    """
    Generate SOC2 control summary from a list of check IDs.

    Args:
        check_ids: List of failed Checkov check IDs

    Returns:
        Dictionary mapping control IDs to category and count
    """
    summary: dict[str, dict[str, int]] = {}

    for check_id in check_ids:
        control = get_soc2_mapping(check_id)
        if control:
            if control.control not in summary:
                summary[control.control] = {
                    "category": control.category,
                    "count": 0,
                }
            summary[control.control]["count"] += 1

    return summary
