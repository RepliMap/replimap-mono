# Security Policy

## Overview

RepliMap is designed with security as a core principle. This document outlines our security practices and how we protect your infrastructure data.

## Security Principles

### 1. Read-Only Access

RepliMap **only requires read permissions** to your AWS environment. We never:
- Create, modify, or delete AWS resources
- Require write permissions to any service
- Make changes to your infrastructure

### 2. Local Processing

All data processing happens **on your machine**:
- AWS API responses are processed locally
- Terraform code is generated locally
- No infrastructure data is sent to external servers

### 3. No Data Collection

RepliMap does **not collect** your infrastructure data:
- No telemetry of scanned resources
- No upload of generated Terraform code
- No tracking of your AWS resource configurations

### 4. Minimal Permissions

We request only the permissions necessary:
- See [IAM_POLICY.md](./IAM_POLICY.md) for the exact permissions
- All permissions are read-only (`Describe*`, `List*`, `Get*`)
- No wildcard write permissions

## Data Handling

### What Data Does RepliMap Access?

| Data Type | Accessed | Stored Locally | Sent Externally |
|-----------|----------|----------------|-----------------|
| VPC configurations | ✅ | Optional | ❌ |
| EC2 instance metadata | ✅ | Optional | ❌ |
| Security group rules | ✅ | Optional | ❌ |
| RDS configurations | ✅ | Optional | ❌ |
| S3 bucket metadata | ✅ | Optional | ❌ |
| S3 bucket contents | ❌ | ❌ | ❌ |
| Database contents | ❌ | ❌ | ❌ |
| Secrets/credentials | ❌ | ❌ | ❌ |

### Local Storage

RepliMap stores minimal data locally in `~/.replimap/`:

```
~/.replimap/
├── license.json        # License key (encrypted)
├── usage.json          # Usage statistics (local only)
└── config.yaml         # User preferences
```

## Sensitive Data Protection

### Automatic Sanitization

The sanitization transformer automatically removes sensitive data:

```python
# Fields that are automatically removed/replaced:
SENSITIVE_FIELDS = [
    "password", "secret", "key", "token",
    "credential", "private", "auth"
]
```

### Account ID Replacement

AWS account IDs are automatically replaced with variables:

```hcl
# Before
arn:aws:ec2:us-east-1:123456789012:vpc/vpc-abc123

# After
arn:aws:ec2:us-east-1:${var.aws_account_id}:vpc/vpc-abc123
```

## License Verification

### How License Keys Work

1. License keys are validated against our API on first use
2. Validated licenses are cached locally for 24 hours
3. Offline operation is supported for 7 days (grace period)
4. No infrastructure data is included in license checks

### What's Sent During Verification

```json
{
    "license_key": "RM-XXXX-XXXX-XXXX",
    "machine_id": "sha256_hash_of_system_info",
    "version": "1.0.0"
}
```

**Not sent**: AWS credentials, resource configurations, generated code

## Vulnerability Reporting

### Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Email**: security@replimap.io
2. **Subject**: `[SECURITY] Brief description`
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes

### Response Timeline

- **Acknowledgment**: Within 24 hours
- **Initial Assessment**: Within 72 hours
- **Fix Timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 1 week
  - Medium: 2 weeks
  - Low: Next release

### Disclosure Policy

- We follow responsible disclosure practices
- We will credit reporters (unless anonymity is requested)
- We will not take legal action against good-faith reporters

## Compliance

### SOC 2 Type II

RepliMap is designed with SOC 2 controls in mind:
- Access controls (read-only by design)
- Data protection (local processing)
- Audit logging (usage tracking)

### GDPR

For EU customers:
- No personal data is collected beyond license email
- Data processing occurs locally
- No cross-border data transfer of infrastructure data

## Best Practices

### For Users

1. **Use Dedicated Credentials**: Create a separate IAM user for RepliMap
2. **Restrict by Region**: Limit permissions to regions you scan
3. **Review Generated Code**: Always review Terraform before applying
4. **Rotate Credentials**: Regularly rotate AWS access keys
5. **Enable MFA**: Use MFA for AWS accounts

### For Developers

1. **Never Log Credentials**: AWS credentials are never logged
2. **Sanitize All Output**: Sensitive data is sanitized before display
3. **Validate Input**: All user input is validated
4. **Secure Dependencies**: Dependencies are regularly updated

## Third-Party Dependencies

| Dependency | Purpose | Security Notes |
|------------|---------|----------------|
| boto3 | AWS API | Official AWS SDK |
| networkx | Graph engine | No network access |
| typer | CLI | No network access |
| jinja2 | Templates | Sandboxed execution |
| rich | Console output | No network access |

## Audit Log

RepliMap maintains a local audit log of operations:

```bash
# View recent operations
replimap license usage
```

## Contact

- **Security Issues**: security@replimap.io
- **General Support**: support@replimap.io
- **GitHub Issues**: https://github.com/replimap/replimap/issues

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01 | Initial security policy |
