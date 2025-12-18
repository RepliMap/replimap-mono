# RepliMap IAM Policy

RepliMap requires **read-only** access to scan your AWS resources. This document provides the minimum required IAM permissions.

## Recommended Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "RepliMapReadOnly",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeInstances",
                "ec2:DescribeTags",
                "ec2:DescribeAvailabilityZones",
                "ec2:DescribeRouteTables",
                "ec2:DescribeInternetGateways",
                "ec2:DescribeNatGateways",
                "rds:DescribeDBInstances",
                "rds:DescribeDBSubnetGroups",
                "rds:DescribeDBSecurityGroups",
                "rds:ListTagsForResource",
                "s3:ListAllMyBuckets",
                "s3:GetBucketLocation",
                "s3:GetBucketTagging",
                "s3:GetBucketVersioning",
                "s3:GetBucketEncryption",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

## Setup Instructions

### Option 1: Create a Dedicated IAM User

1. Go to IAM Console → Users → Add User
2. Name: `replimap-scanner`
3. Access type: Programmatic access
4. Attach the policy above
5. Save the access keys

```bash
# Configure AWS CLI
aws configure --profile replimap
# Enter the access key ID and secret
```

### Option 2: Create an IAM Role (Recommended for EC2/ECS)

1. Go to IAM Console → Roles → Create Role
2. Select "AWS service" → EC2/ECS
3. Attach the policy above
4. Name: `replimap-scanner-role`

### Option 3: Use Existing Profile with Restricted Permissions

If you have an existing AWS profile, you can create a more restricted policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "RepliMapVPCRead",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "ec2:Region": "us-east-1"
                }
            }
        }
    ]
}
```

## Verification

Test your permissions with:

```bash
# Verify identity
aws sts get-caller-identity --profile replimap

# Test VPC access
aws ec2 describe-vpcs --profile replimap --region us-east-1

# Test with RepliMap
replimap scan --profile replimap --region us-east-1
```

## Security Best Practices

1. **Use Read-Only Permissions**: Never grant write permissions to RepliMap
2. **Restrict by Region**: Limit access to specific regions if possible
3. **Use IAM Roles**: Prefer roles over access keys when running on AWS
4. **Rotate Credentials**: Regularly rotate access keys
5. **Enable CloudTrail**: Monitor API calls made by RepliMap

## What RepliMap Does NOT Do

- ❌ Create, modify, or delete any AWS resources
- ❌ Access S3 bucket contents (only metadata)
- ❌ Read database contents
- ❌ Access secrets or credentials
- ❌ Make cross-account API calls
- ❌ Upload any data to external services

## Permissions by Resource Type

| Resource | Actions Required | Purpose |
|----------|-----------------|---------|
| VPC | `ec2:DescribeVpcs` | Scan VPC configurations |
| Subnet | `ec2:DescribeSubnets` | Scan subnet configurations |
| Security Group | `ec2:DescribeSecurityGroups` | Scan security rules |
| EC2 Instance | `ec2:DescribeInstances` | Scan instance configurations |
| RDS Instance | `rds:DescribeDBInstances` | Scan database configurations |
| S3 Bucket | `s3:ListAllMyBuckets`, `s3:GetBucket*` | Scan bucket configurations |
| STS | `sts:GetCallerIdentity` | Verify authentication |

## Troubleshooting

### "Access Denied" Error

```
AccessDeniedException: User: arn:aws:iam::123456789012:user/replimap
is not authorized to perform: ec2:DescribeVpcs
```

**Solution**: Ensure the IAM policy is correctly attached to your user/role.

### "InvalidClientTokenId" Error

```
InvalidClientTokenId: The security token included in the request is invalid.
```

**Solution**: Check your AWS credentials are correctly configured:

```bash
aws configure list --profile replimap
```

### Region-Specific Issues

If you only have access to specific regions:

```bash
# Specify the region explicitly
replimap scan --profile replimap --region eu-west-1
```

## Questions?

- Open an issue on [GitHub](https://github.com/replimap/replimap/issues)
- Email: support@replimap.io
