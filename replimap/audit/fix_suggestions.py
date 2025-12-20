"""
Terraform Fix Suggestions for Common Checkov Findings.

Provides remediation code snippets for security misconfigurations.
"""

from __future__ import annotations

# Fix suggestions for common Checkov checks
FIX_SUGGESTIONS: dict[str, str] = {
    # S3 Bucket Security
    "CKV_AWS_19": '''# Enable S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}''',
    "CKV_AWS_18": '''# Enable S3 bucket versioning
resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}''',
    "CKV_AWS_21": '''# Enable S3 bucket logging
resource "aws_s3_bucket_logging" "this" {
  bucket        = aws_s3_bucket.this.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/"
}''',
    "CKV_AWS_20": '''# Enforce SSL-only access to S3 bucket
resource "aws_s3_bucket_policy" "ssl_only" {
  bucket = aws_s3_bucket.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnforceSSL"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.this.arn,
          "${aws_s3_bucket.this.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}''',
    "CKV_AWS_53": '''# Block public access to S3 bucket
resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}''',
    # EBS/EC2 Security
    "CKV_AWS_3": '''# Enable EBS volume encryption
resource "aws_ebs_volume" "this" {
  availability_zone = var.availability_zone
  size              = var.size

  encrypted  = true
  kms_key_id = var.kms_key_id  # Optional: Use CMK instead of AWS-managed key

  tags = {
    Name = var.name
  }
}''',
    "CKV_AWS_8": '''# Enable EC2 launch configuration encryption
resource "aws_launch_configuration" "this" {
  name_prefix   = var.name_prefix
  image_id      = var.ami_id
  instance_type = var.instance_type

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
  }

  ebs_block_device {
    device_name = "/dev/sdf"
    encrypted   = true
    volume_type = "gp3"
  }
}''',
    "CKV_AWS_79": '''# Enable IMDSv2 for EC2 instances
resource "aws_instance" "this" {
  ami           = var.ami_id
  instance_type = var.instance_type

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # Enforce IMDSv2
    http_put_response_hop_limit = 1
  }
}''',
    # Security Groups
    "CKV_AWS_23": '''# Restrict security group ingress - avoid 0.0.0.0/0
resource "aws_security_group" "this" {
  name        = var.name
  description = var.description
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from internal"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # Internal networks only
  }

  # Avoid rules like:
  # cidr_blocks = ["0.0.0.0/0"]  # DANGEROUS: Open to internet
}''',
    "CKV_AWS_24": '''# Restrict SSH access
ingress {
  description = "SSH from bastion only"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = [var.bastion_cidr]  # Bastion host CIDR only
  # Or use security_groups = [aws_security_group.bastion.id]
}''',
    "CKV_AWS_25": '''# Restrict RDP access
ingress {
  description = "RDP from VPN only"
  from_port   = 3389
  to_port     = 3389
  protocol    = "tcp"
  cidr_blocks = [var.vpn_cidr]  # VPN CIDR only
}''',
    # RDS Security
    "CKV_AWS_16": '''# Enable RDS encryption
resource "aws_db_instance" "this" {
  identifier     = var.identifier
  engine         = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class

  storage_encrypted = true
  kms_key_id        = var.kms_key_arn  # Optional: Use CMK

  # Other required attributes...
}''',
    "CKV_AWS_17": '''# RDS snapshots inherit encryption from the source DB
# Ensure the source RDS instance has encryption enabled
resource "aws_db_instance" "this" {
  storage_encrypted = true
  # Snapshots will automatically be encrypted
}''',
    "CKV_AWS_157": '''# Enable Multi-AZ for high availability
resource "aws_db_instance" "this" {
  identifier     = var.identifier
  engine         = var.engine
  instance_class = var.instance_class

  multi_az = true  # Enable Multi-AZ deployment

  # Other required attributes...
}''',
    "CKV_AWS_128": '''# Enable deletion protection
resource "aws_db_instance" "this" {
  identifier = var.identifier

  deletion_protection = true  # Prevent accidental deletion

  # Other required attributes...
}''',
    # ALB/ELB Security
    "CKV_AWS_2": '''# Use HTTPS listener with TLS
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# Redirect HTTP to HTTPS
resource "aws_lb_listener" "http_redirect" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}''',
    "CKV_AWS_103": '''# Use TLS 1.2+ security policy
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"

  # Use a policy that enforces TLS 1.2 minimum
  ssl_policy = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  # Or: "ELBSecurityPolicy-TLS-1-2-2017-01"

  certificate_arn = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}''',
    "CKV_AWS_104": '''# Enable ALB access logging
resource "aws_lb" "this" {
  name               = var.name
  internal           = var.internal
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.subnet_ids

  access_logs {
    bucket  = aws_s3_bucket.lb_logs.id
    prefix  = "alb-logs"
    enabled = true
  }
}''',
    # VPC/Network Security
    "CKV_AWS_48": '''# Enable VPC Flow Logs
resource "aws_flow_log" "this" {
  vpc_id          = aws_vpc.this.id
  traffic_type    = "ALL"
  iam_role_arn    = aws_iam_role.flow_logs.arn
  log_destination = aws_cloudwatch_log_group.flow_logs.arn

  tags = {
    Name = "${var.name}-flow-logs"
  }
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/aws/vpc/flow-logs/${var.name}"
  retention_in_days = 30
}''',
    # CloudTrail
    "CKV_AWS_67": '''# Enable CloudTrail
resource "aws_cloudtrail" "this" {
  name                          = var.name
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true

  event_selector {
    read_write_type           = "All"
    include_management_events = true
  }
}''',
    "CKV_AWS_35": '''# Enable CloudTrail log file validation
resource "aws_cloudtrail" "this" {
  name           = var.name
  s3_bucket_name = aws_s3_bucket.cloudtrail.id

  enable_log_file_validation = true  # Enable log integrity validation
}''',
    # SQS/SNS Security
    "CKV_AWS_27": '''# Enable SQS queue encryption
resource "aws_sqs_queue" "this" {
  name = var.name

  sqs_managed_sse_enabled = true
  # Or use KMS:
  # kms_master_key_id = var.kms_key_id
}''',
    "CKV_AWS_26": '''# Enable SNS topic encryption
resource "aws_sns_topic" "this" {
  name              = var.name
  kms_master_key_id = var.kms_key_id  # Required for encryption
}''',
    # ElastiCache Security
    "CKV_AWS_83": '''# Enable ElastiCache encryption in transit
resource "aws_elasticache_replication_group" "this" {
  replication_group_id = var.name
  description          = var.description

  transit_encryption_enabled = true  # Enable TLS
  auth_token                 = var.auth_token  # Optional but recommended

  # Other required attributes...
}''',
    "CKV_AWS_84": '''# Enable ElastiCache encryption at rest
resource "aws_elasticache_replication_group" "this" {
  replication_group_id = var.name
  description          = var.description

  at_rest_encryption_enabled = true
  kms_key_id                 = var.kms_key_id  # Optional: Use CMK

  # Other required attributes...
}''',
    # KMS
    "CKV_AWS_7": '''# Enable KMS key rotation
resource "aws_kms_key" "this" {
  description             = var.description
  deletion_window_in_days = 30

  enable_key_rotation = true  # Enable automatic annual rotation
}''',
}


def get_fix_suggestion(check_id: str) -> str | None:
    """
    Get fix suggestion for a Checkov check ID.

    Args:
        check_id: Checkov check ID (e.g., "CKV_AWS_19")

    Returns:
        Terraform code suggestion if available, None otherwise
    """
    return FIX_SUGGESTIONS.get(check_id)
