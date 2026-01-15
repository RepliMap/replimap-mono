# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.5.x   | :white_check_mark: |
| < 0.5   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Email **security@replimap.com** with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Any suggested fixes (optional)

### What to Expect

| Stage | Timeline |
|-------|----------|
| Acknowledgment | Within 48 hours |
| Initial Assessment | Within 1 week |
| Resolution (Critical) | 24-72 hours |
| Resolution (High) | 1-2 weeks |
| Resolution (Medium) | 2-4 weeks |
| Resolution (Low) | Next release cycle |

## Security Measures

### Supply Chain Security

| Measure | Implementation |
|---------|---------------|
| **Dependency Scanning** | Dependabot (weekly) |
| **Static Analysis** | CodeQL on every PR |
| **Secret Scanning** | GitHub Advanced Security |
| **Package Publishing** | OIDC Trusted Publishing (no long-lived tokens) |

### Infrastructure Security

- All traffic encrypted (TLS 1.3)
- AWS credentials never stored on our servers
- SOC2 Type II compliant infrastructure
- Regular penetration testing

### Development Practices

- Signed commits required for releases
- Branch protection on `main`
- Required reviews from CODEOWNERS
- Automated security checks in CI

## Security Contacts

| Contact | Purpose |
|---------|---------|
| security@replimap.com | Vulnerability reports |

## Security Hall of Fame

We appreciate responsible disclosure. Researchers who report valid vulnerabilities will be acknowledged here (with permission).

<!-- Add acknowledged researchers here -->
