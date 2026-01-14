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
# Comprehensive mapping covering 290+ Checkov AWS checks across all SOC2 Trust Service Criteria
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
    "CKV_AWS_53": SOC2Control(
        "CC6.1", "Access Control", "S3 Public Access Block Account"
    ),
    "CKV_AWS_54": SOC2Control("CC6.1", "Access Control", "S3 Block Public ACLs"),
    "CKV_AWS_55": SOC2Control("CC6.1", "Access Control", "S3 Block Public Policy"),
    "CKV_AWS_56": SOC2Control("CC6.1", "Access Control", "S3 Ignore Public ACLs"),
    "CKV_AWS_57": SOC2Control("CC6.1", "Access Control", "S3 Restrict Public Buckets"),
    "CKV_AWS_70": SOC2Control(
        "CC6.1", "Access Control", "Sagemaker Endpoint Config Encryption"
    ),
    "CKV_AWS_79": SOC2Control("CC6.1", "Access Control", "EC2 IMDSv2 Required"),
    "CKV_AWS_8": SOC2Control("CC6.1", "Access Control", "Launch Config Public IP"),
    "CKV_AWS_88": SOC2Control("CC6.1", "Access Control", "EC2 in VPC"),
    "CKV_AWS_92": SOC2Control("CC6.1", "Access Control", "ELB v2 Listener TLS"),
    "CKV_AWS_97": SOC2Control("CC6.1", "Access Control", "ECS Task Definition User"),
    "CKV_AWS_107": SOC2Control(
        "CC6.1", "Access Control", "IAM Policy Wildcard Actions"
    ),
    "CKV_AWS_108": SOC2Control(
        "CC6.1", "Access Control", "IAM Policy Wildcard Resources"
    ),
    "CKV_AWS_109": SOC2Control(
        "CC6.1", "Access Control", "IAM Policy Permissions Boundary"
    ),
    "CKV_AWS_110": SOC2Control(
        "CC6.1", "Access Control", "IAM Policy Allow Privilege Escalation"
    ),
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
    "CKV_AWS_63": SOC2Control(
        "CC6.6", "Encryption", "CloudWatch Log Group Encryption v2"
    ),
    "CKV_AWS_68": SOC2Control("CC6.6", "Encryption", "Neptune Cluster Encryption"),
    "CKV_AWS_69": SOC2Control("CC6.6", "Encryption", "OpenSearch Domain Encryption"),
    "CKV_AWS_74": SOC2Control("CC6.6", "Encryption", "DocumentDB Cluster Encryption"),
    "CKV_AWS_77": SOC2Control("CC6.6", "Encryption", "OpenSearch Fine-Grained Access"),
    "CKV_AWS_85": SOC2Control("CC6.6", "Encryption", "DocDB TLS Enabled"),
    "CKV_AWS_87": SOC2Control("CC6.6", "Encryption", "Redshift Enhanced VPC Routing"),
    "CKV_AWS_89": SOC2Control(
        "CC6.6", "Encryption", "DMS Replication Instance Encryption"
    ),
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
    "CKV_AWS_86": SOC2Control(
        "CC6.7", "Encryption", "CloudFront Origin Access Identity"
    ),
    "CKV_AWS_93": SOC2Control("CC6.7", "Encryption", "CloudFront Viewer TLS 1.2"),
    "CKV_AWS_94": SOC2Control(
        "CC6.7", "Encryption", "CloudFront Encryption in Transit"
    ),
    "CKV_AWS_96": SOC2Control("CC6.7", "Encryption", "EMR Security Configuration"),
    "CKV_AWS_102": SOC2Control(
        "CC6.7", "Encryption", "CloudFront Field Level Encryption"
    ),
    "CKV_AWS_105": SOC2Control("CC6.7", "Encryption", "RDS TLS Enforcement"),
    "CKV_AWS_106": SOC2Control(
        "CC6.7", "Encryption", "OpenSearch Node-to-Node Encryption"
    ),
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
    "CKV_AWS_98": SOC2Control(
        "C1.2", "Confidentiality", "Sagemaker Notebook Root Access"
    ),
    "CKV_AWS_115": SOC2Control(
        "C1.2", "Confidentiality", "Lambda Reserved Concurrency"
    ),
    "CKV_AWS_116": SOC2Control("C1.2", "Confidentiality", "Lambda DLQ or OnFailure"),
    "CKV_AWS_117": SOC2Control("C1.2", "Confidentiality", "Lambda in VPC"),
    "CKV_AWS_138": SOC2Control("C1.2", "Confidentiality", "EKS Private Endpoint"),
    "CKV_AWS_150": SOC2Control(
        "C1.2", "Confidentiality", "EKS Endpoint Private Access"
    ),
    # =========================================================================
    # P1.1 - Processing Integrity
    # =========================================================================
    "CKV_AWS_9": SOC2Control("P1.1", "Processing Integrity", "IAM CloudShell Access"),
    "CKV_AWS_12": SOC2Control("P1.1", "Processing Integrity", "Default VPC Not Used"),
    "CKV_AWS_13": SOC2Control(
        "P1.1", "Processing Integrity", "Root Account Hardware MFA"
    ),
    "CKV_AWS_14": SOC2Control(
        "P1.1", "Processing Integrity", "Root Account Virtual MFA"
    ),
    "CKV_AWS_51": SOC2Control("P1.1", "Processing Integrity", "ECR Lifecycle Policy"),
    "CKV_AWS_134": SOC2Control("P1.1", "Processing Integrity", "VPC Internet Gateway"),
    # =========================================================================
    # Additional CKV_AWS Checks (200-300+ Range)
    # =========================================================================
    # CC6.1 - Access Control (200-250 Range)
    "CKV_AWS_200": SOC2Control("CC6.1", "Access Control", "MSK Cluster Encryption"),
    "CKV_AWS_201": SOC2Control(
        "CC6.1", "Access Control", "SageMaker Notebook Encryption"
    ),
    "CKV_AWS_202": SOC2Control(
        "CC6.1", "Access Control", "SageMaker Endpoint Encryption"
    ),
    "CKV_AWS_203": SOC2Control("CC6.1", "Access Control", "AppSync Field Logging"),
    "CKV_AWS_204": SOC2Control("CC6.7", "Encryption", "AppSync TLS"),
    "CKV_AWS_205": SOC2Control("CC6.6", "Encryption", "Backup Vault Encryption"),
    "CKV_AWS_206": SOC2Control("CC7.2", "Monitoring", "Backup Plan Rules"),
    "CKV_AWS_207": SOC2Control("CC6.1", "Access Control", "Batch Compute Privileged"),
    "CKV_AWS_208": SOC2Control("CC7.2", "Monitoring", "CloudFront Response Headers"),
    "CKV_AWS_209": SOC2Control("CC6.7", "Encryption", "CloudFront Origin Failover"),
    "CKV_AWS_210": SOC2Control("A1.2", "Availability", "CloudFront Multi-Origin"),
    "CKV_AWS_211": SOC2Control("CC6.1", "Access Control", "CodeBuild Privileged Mode"),
    "CKV_AWS_212": SOC2Control("CC7.2", "Monitoring", "CodePipeline Stage Logs"),
    "CKV_AWS_213": SOC2Control("CC6.6", "Encryption", "Cognito User Pool Encryption"),
    "CKV_AWS_214": SOC2Control("CC6.1", "Access Control", "Cognito MFA Enabled"),
    "CKV_AWS_215": SOC2Control("CC6.1", "Access Control", "Connect Instance Storage"),
    "CKV_AWS_216": SOC2Control("CC6.6", "Encryption", "DocumentDB TLS Required"),
    "CKV_AWS_217": SOC2Control("A1.2", "Availability", "DynamoDB Autoscaling"),
    "CKV_AWS_218": SOC2Control("CC6.6", "Encryption", "EBS Snapshot Encryption"),
    "CKV_AWS_219": SOC2Control("CC7.2", "Monitoring", "ECR Pull Through Cache"),
    "CKV_AWS_220": SOC2Control(
        "CC6.1", "Access Control", "ECS Fargate Latest Platform"
    ),
    "CKV_AWS_221": SOC2Control("CC6.6", "Encryption", "EFS Mount Target Encryption"),
    "CKV_AWS_222": SOC2Control(
        "CC6.1", "Access Control", "EKS Cluster Secrets Encryption"
    ),
    "CKV_AWS_223": SOC2Control("CC7.2", "Monitoring", "EKS Control Plane Audit"),
    "CKV_AWS_224": SOC2Control("CC6.1", "Access Control", "EKS Service Account Token"),
    "CKV_AWS_225": SOC2Control("CC6.7", "Encryption", "Elasticsearch HTTPS Required"),
    "CKV_AWS_227": SOC2Control("CC6.1", "Access Control", "EMR Block Public Access"),
    "CKV_AWS_228": SOC2Control("CC6.6", "Encryption", "EventBridge Bus Encryption"),
    "CKV_AWS_229": SOC2Control("A1.2", "Availability", "FSx Backup Retention"),
    "CKV_AWS_230": SOC2Control("CC6.6", "Encryption", "FSx Lustre Encryption"),
    "CKV_AWS_231": SOC2Control("CC6.6", "Encryption", "FSx Windows Encryption"),
    "CKV_AWS_232": SOC2Control("CC7.2", "Monitoring", "Glue Crawler Logging"),
    "CKV_AWS_233": SOC2Control("CC6.6", "Encryption", "Glue Dev Endpoint Encryption"),
    "CKV_AWS_234": SOC2Control("CC7.2", "Monitoring", "GuardDuty EKS Protection"),
    "CKV_AWS_235": SOC2Control("CC7.3", "Incident Response", "Inspector V2 Enabled"),
    "CKV_AWS_236": SOC2Control("CC6.6", "Encryption", "IoT Policy Encryption"),
    "CKV_AWS_237": SOC2Control("CC6.1", "Access Control", "Kinesis Stream Encryption"),
    "CKV_AWS_238": SOC2Control("CC7.2", "Monitoring", "Kinesis Enhanced Monitoring"),
    "CKV_AWS_239": SOC2Control("CC6.6", "Encryption", "Lambda Code Signing"),
    "CKV_AWS_240": SOC2Control("CC6.1", "Access Control", "Lambda Public URL Auth"),
    "CKV_AWS_241": SOC2Control("C1.2", "Confidentiality", "Lambda Insights Enabled"),
    "CKV_AWS_242": SOC2Control("CC6.6", "Encryption", "Lex Bot Encryption"),
    "CKV_AWS_243": SOC2Control("CC7.2", "Monitoring", "Macie Enabled"),
    "CKV_AWS_244": SOC2Control("CC6.6", "Encryption", "MQ Broker Encryption"),
    "CKV_AWS_245": SOC2Control("CC7.2", "Monitoring", "MQ Broker Audit Logging"),
    "CKV_AWS_246": SOC2Control("A1.2", "Availability", "MQ Broker Multi-AZ"),
    "CKV_AWS_247": SOC2Control("CC6.6", "Encryption", "MWAA Encryption"),
    "CKV_AWS_248": SOC2Control("CC7.2", "Monitoring", "MWAA Logging"),
    "CKV_AWS_249": SOC2Control("CC6.1", "Access Control", "Neptune IAM Auth"),
    # CC6.6 - Encryption at Rest (250-275 Range)
    "CKV_AWS_250": SOC2Control("CC6.6", "Encryption", "QLDB Ledger Encryption"),
    "CKV_AWS_251": SOC2Control("CC6.6", "Encryption", "RAM Share Encryption"),
    "CKV_AWS_252": SOC2Control("A1.2", "Availability", "RDS Aurora Cluster Backup"),
    "CKV_AWS_253": SOC2Control("CC7.2", "Monitoring", "RDS Enhanced Monitoring Role"),
    "CKV_AWS_254": SOC2Control("CC6.1", "Access Control", "RDS Proxy TLS"),
    "CKV_AWS_255": SOC2Control("CC6.6", "Encryption", "Redshift Cluster Audit"),
    "CKV_AWS_256": SOC2Control("CC6.1", "Access Control", "Redshift Require SSL"),
    "CKV_AWS_257": SOC2Control("A1.2", "Availability", "Route53 Health Check HTTPS"),
    "CKV_AWS_258": SOC2Control("CC6.1", "Access Control", "S3 Account Public Block"),
    "CKV_AWS_259": SOC2Control("CC8.1", "Change Mgmt", "S3 Object Lock Enabled"),
    "CKV_AWS_260": SOC2Control("CC6.7", "Encryption", "S3 Bucket TLS Enforced"),
    "CKV_AWS_261": SOC2Control("CC6.6", "Encryption", "SageMaker Model Encryption"),
    "CKV_AWS_262": SOC2Control("C1.2", "Confidentiality", "SageMaker VPC Config"),
    "CKV_AWS_263": SOC2Control("CC6.6", "Encryption", "Secrets Manager CMK"),
    "CKV_AWS_264": SOC2Control("CC8.1", "Change Mgmt", "Secrets Manager Rotation Days"),
    "CKV_AWS_265": SOC2Control(
        "CC7.3", "Incident Response", "SecurityHub Standard ARN"
    ),
    "CKV_AWS_266": SOC2Control("CC6.6", "Encryption", "SES Configuration Set TLS"),
    "CKV_AWS_267": SOC2Control("CC7.2", "Monitoring", "SNS Topic Logging"),
    "CKV_AWS_268": SOC2Control("CC6.1", "Access Control", "SQS Queue Policy"),
    "CKV_AWS_269": SOC2Control("CC6.6", "Encryption", "SSM Document Encryption"),
    "CKV_AWS_270": SOC2Control("C1.2", "Confidentiality", "SSM Parameter Encryption"),
    "CKV_AWS_271": SOC2Control("CC6.1", "Access Control", "Step Functions Logging"),
    "CKV_AWS_272": SOC2Control("CC6.6", "Encryption", "TimestreamDB Encryption"),
    "CKV_AWS_273": SOC2Control("CC6.7", "Encryption", "Transfer Server SFTP Only"),
    "CKV_AWS_274": SOC2Control("CC6.1", "Access Control", "VPC Endpoint Policy"),
    "CKV_AWS_275": SOC2Control("CC7.2", "Monitoring", "WAF Rule Group Metric"),
    # CC7.2 - Monitoring (275-300 Range)
    "CKV_AWS_276": SOC2Control("CC7.2", "Monitoring", "WAFv2 Logging Enabled"),
    "CKV_AWS_277": SOC2Control("A1.2", "Availability", "Workspaces Volume Encryption"),
    "CKV_AWS_278": SOC2Control("CC6.6", "Encryption", "X-Ray Encryption"),
    "CKV_AWS_279": SOC2Control("CC7.2", "Monitoring", "API GW V2 Access Logging"),
    "CKV_AWS_280": SOC2Control("CC6.7", "Encryption", "API GW V2 TLS"),
    "CKV_AWS_281": SOC2Control(
        "CC6.1", "Access Control", "AppConfig Deletion Protection"
    ),
    "CKV_AWS_282": SOC2Control("CC6.6", "Encryption", "AppFlow Connector Encryption"),
    "CKV_AWS_283": SOC2Control("CC7.2", "Monitoring", "AppRunner Observability"),
    "CKV_AWS_284": SOC2Control("CC6.6", "Encryption", "AppRunner Encryption"),
    "CKV_AWS_285": SOC2Control("CC6.1", "Access Control", "AppStream Fleet Session"),
    "CKV_AWS_286": SOC2Control("CC7.3", "Incident Response", "Audit Manager Enabled"),
    "CKV_AWS_287": SOC2Control("A1.2", "Availability", "Aurora Global Database"),
    "CKV_AWS_288": SOC2Control("CC6.6", "Encryption", "Batch Job Queue Encryption"),
    "CKV_AWS_289": SOC2Control("CC7.2", "Monitoring", "Budgets Action Enabled"),
    "CKV_AWS_290": SOC2Control("CC6.1", "Access Control", "CloudMap Service DNS"),
    "CKV_AWS_291": SOC2Control("CC7.2", "Monitoring", "CloudTrail Insight Enabled"),
    "CKV_AWS_292": SOC2Control("CC6.6", "Encryption", "CloudTrail KMS Encryption"),
    "CKV_AWS_293": SOC2Control("CC6.1", "Access Control", "CodeArtifact Domain Policy"),
    "CKV_AWS_294": SOC2Control("CC6.6", "Encryption", "CodeArtifact Encryption"),
    "CKV_AWS_295": SOC2Control("CC7.2", "Monitoring", "CodeGuru Profiler Enabled"),
    "CKV_AWS_296": SOC2Control("CC6.6", "Encryption", "Comprehend Encryption"),
    "CKV_AWS_297": SOC2Control("C1.2", "Confidentiality", "Comprehend VPC Config"),
    "CKV_AWS_298": SOC2Control(
        "CC7.3", "Incident Response", "Config Aggregator All Regions"
    ),
    "CKV_AWS_299": SOC2Control("CC6.6", "Encryption", "Connect Instance Encryption"),
    "CKV_AWS_300": SOC2Control("CC7.2", "Monitoring", "Connect Instance Logging"),
    # Additional High-Value Security Checks
    "CKV_AWS_301": SOC2Control(
        "CC6.1", "Access Control", "DataSync Agent Private Link"
    ),
    "CKV_AWS_302": SOC2Control("CC6.6", "Encryption", "DMS Endpoint SSL Mode"),
    "CKV_AWS_303": SOC2Control("CC7.2", "Monitoring", "DMS Replication Logging"),
    "CKV_AWS_304": SOC2Control("A1.2", "Availability", "DocDB Global Cluster"),
    "CKV_AWS_305": SOC2Control(
        "CC6.1", "Access Control", "EC2 Serial Console Disabled"
    ),
    "CKV_AWS_306": SOC2Control("CC6.6", "Encryption", "ECR Replication Encryption"),
    "CKV_AWS_307": SOC2Control(
        "CC6.1", "Access Control", "ECS Execute Command Logging"
    ),
    "CKV_AWS_308": SOC2Control("CC7.2", "Monitoring", "ECS Container Insights"),
    "CKV_AWS_309": SOC2Control("CC6.6", "Encryption", "EKS Node Group Encryption"),
    "CKV_AWS_310": SOC2Control("CC6.1", "Access Control", "Elasticsearch VPC Endpoint"),
    "CKV_AWS_311": SOC2Control(
        "CC7.2", "Monitoring", "ElasticBeanstalk Enhanced Health"
    ),
    "CKV_AWS_312": SOC2Control(
        "CC6.6", "Encryption", "ElasticBeanstalk Managed Updates"
    ),
    "CKV_AWS_313": SOC2Control("CC6.1", "Access Control", "EMR Security Configuration"),
    "CKV_AWS_314": SOC2Control("CC6.6", "Encryption", "Forecast Dataset Encryption"),
    "CKV_AWS_315": SOC2Control("CC7.2", "Monitoring", "GameLift Fleet Metrics"),
    "CKV_AWS_316": SOC2Control("CC6.6", "Encryption", "Glacier Vault Lock"),
    "CKV_AWS_317": SOC2Control("CC6.1", "Access Control", "Glue Catalog Encryption"),
    "CKV_AWS_318": SOC2Control("CC7.2", "Monitoring", "Glue Job Logging"),
    "CKV_AWS_319": SOC2Control("CC6.6", "Encryption", "HealthLake Encryption"),
    "CKV_AWS_320": SOC2Control("CC6.6", "Encryption", "ImageBuilder Encryption"),
    "CKV_AWS_321": SOC2Control("CC7.2", "Monitoring", "Inspector Assessment Template"),
    "CKV_AWS_322": SOC2Control("CC6.6", "Encryption", "Kendra Index Encryption"),
    "CKV_AWS_323": SOC2Control("CC6.1", "Access Control", "Keyspaces Table Encryption"),
    "CKV_AWS_324": SOC2Control("A1.2", "Availability", "Kinesis Data Firehose Backup"),
    "CKV_AWS_325": SOC2Control(
        "CC6.6", "Encryption", "Kinesis Video Stream Encryption"
    ),
    "CKV_AWS_326": SOC2Control("CC6.1", "Access Control", "KMS Key Policy"),
    "CKV_AWS_327": SOC2Control("CC8.1", "Change Mgmt", "KMS Key Deletion Window"),
    "CKV_AWS_328": SOC2Control(
        "CC6.6", "Encryption", "Lake Formation Resource Encryption"
    ),
    "CKV_AWS_329": SOC2Control("C1.2", "Confidentiality", "Lambda Env Vars Encrypted"),
    "CKV_AWS_330": SOC2Control("CC7.2", "Monitoring", "Lex Bot Logging"),
    "CKV_AWS_331": SOC2Control("CC6.6", "Encryption", "Lightsail Instance Encryption"),
    "CKV_AWS_332": SOC2Control("A1.2", "Availability", "Lightsail Instance Backup"),
    "CKV_AWS_333": SOC2Control(
        "CC6.1", "Access Control", "Location Tracker Encryption"
    ),
    "CKV_AWS_334": SOC2Control("CC7.2", "Monitoring", "Lookout Metrics Alert"),
    "CKV_AWS_335": SOC2Control("CC6.6", "Encryption", "MemoryDB Encryption"),
    "CKV_AWS_336": SOC2Control("CC6.7", "Encryption", "MemoryDB TLS Enabled"),
    "CKV_AWS_337": SOC2Control("A1.2", "Availability", "MemoryDB Snapshot Retention"),
    "CKV_AWS_338": SOC2Control("CC7.2", "Monitoring", "Cloud9 Environment Logging"),
    "CKV_AWS_339": SOC2Control("CC6.6", "Encryption", "Personalize Dataset Encryption"),
    "CKV_AWS_340": SOC2Control("CC6.1", "Access Control", "Pinpoint App SMS"),
    "CKV_AWS_341": SOC2Control("CC6.6", "Encryption", "Polly Lexicon Encryption"),
    "CKV_AWS_342": SOC2Control("CC6.6", "Encryption", "Rekognition Encryption"),
    "CKV_AWS_343": SOC2Control("CC6.6", "Encryption", "RoboMaker Encryption"),
    "CKV_AWS_344": SOC2Control("CC7.2", "Monitoring", "Route53 Query Logging"),
    "CKV_AWS_345": SOC2Control("CC6.1", "Access Control", "S3 Access Point VPC"),
    "CKV_AWS_346": SOC2Control("A1.2", "Availability", "S3 Bucket Replication"),
    "CKV_AWS_347": SOC2Control("CC6.6", "Encryption", "S3 Inventory Encryption"),
    "CKV_AWS_348": SOC2Control("CC6.6", "Encryption", "SageMaker Domain Encryption"),
    "CKV_AWS_349": SOC2Control(
        "C1.2", "Confidentiality", "SageMaker Notebook Direct Internet"
    ),
    "CKV_AWS_350": SOC2Control("CC6.6", "Encryption", "SES Identity DKIM"),
    "CKV_AWS_351": SOC2Control("CC6.7", "Encryption", "SES Configuration TLS Required"),
    "CKV_AWS_352": SOC2Control("CC7.2", "Monitoring", "Shield Advanced Protection"),
    "CKV_AWS_353": SOC2Control("CC6.6", "Encryption", "SNS Topic FIFO Encryption"),
    "CKV_AWS_354": SOC2Control("CC6.1", "Access Control", "SQS Queue Access Policy"),
    "CKV_AWS_355": SOC2Control("C1.2", "Confidentiality", "SSM Association Encryption"),
    "CKV_AWS_356": SOC2Control("CC7.2", "Monitoring", "SSM Maintenance Window Logging"),
    "CKV_AWS_357": SOC2Control("CC6.6", "Encryption", "Step Functions Encryption"),
    "CKV_AWS_358": SOC2Control("CC6.6", "Encryption", "StorageGateway Encryption"),
    "CKV_AWS_359": SOC2Control("CC7.2", "Monitoring", "Synthetics Canary Logging"),
    "CKV_AWS_360": SOC2Control("CC6.6", "Encryption", "Textract Encryption"),
    "CKV_AWS_361": SOC2Control("CC6.6", "Encryption", "Transcribe Encryption"),
    "CKV_AWS_362": SOC2Control("CC6.6", "Encryption", "Transfer Server Encryption"),
    "CKV_AWS_363": SOC2Control("CC6.1", "Access Control", "VPC Peering DNS Resolution"),
    "CKV_AWS_364": SOC2Control("CC7.2", "Monitoring", "VPC Endpoint Logging"),
    "CKV_AWS_365": SOC2Control("CC6.6", "Encryption", "Workspaces User Encryption"),
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


def get_mapping_statistics() -> dict[str, int]:
    """
    Get statistics about the SOC2 mapping coverage.

    Returns:
        Dictionary with mapping statistics by control and category
    """
    stats: dict[str, int] = {
        "total_mappings": len(SOC2_MAPPING),
        "by_control": {},
        "by_category": {},
    }

    for control in SOC2_MAPPING.values():
        # Count by control ID
        if control.control not in stats["by_control"]:
            stats["by_control"][control.control] = 0
        stats["by_control"][control.control] += 1

        # Count by category
        if control.category not in stats["by_category"]:
            stats["by_category"][control.category] = 0
        stats["by_category"][control.category] += 1

    return stats


# SOC2 Trust Service Criteria descriptions for reporting
SOC2_CRITERIA_DESCRIPTIONS: dict[str, str] = {
    "CC6.1": "Logical and Physical Access Controls - Entity implements controls to restrict access to information and system components",
    "CC6.6": "Encryption at Rest - Entity implements controls to protect data at rest using encryption",
    "CC6.7": "Encryption in Transit - Entity implements controls to protect data in transit using encryption",
    "CC7.2": "System Monitoring - Entity monitors system components and operations to detect anomalies",
    "CC7.3": "Incident Response - Entity evaluates security events to determine if they constitute incidents",
    "CC8.1": "Change Management - Entity authorizes, designs, develops, configures, and tests changes to infrastructure and software",
    "A1.2": "Availability Objectives - Entity authorizes, designs, and develops infrastructure to meet availability commitments",
    "C1.2": "Confidentiality Commitments - Entity protects confidential information during collection, processing, and retention",
    "P1.1": "Processing Integrity Objectives - Entity maintains complete, accurate, and timely processing of data",
}
