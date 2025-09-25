# Security Policy

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in VAITP-Auditor, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please send an email to: **security@vaitp-auditor.com** (or create a private issue if this email is not available)

Include the following information:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** and severity
- **Suggested fix** (if you have one)
- **Your contact information** for follow-up

### What to Expect

1. **Acknowledgment**: We'll acknowledge receipt within 48 hours
2. **Investigation**: We'll investigate and assess the vulnerability
3. **Updates**: We'll provide regular updates on our progress
4. **Resolution**: We'll work on a fix and coordinate disclosure
5. **Credit**: We'll credit you in the security advisory (if desired)

### Security Best Practices

When using VAITP-Auditor:

- **Keep updated**: Always use the latest version
- **Secure data**: Protect sensitive code and data files
- **Network security**: Be cautious when processing untrusted data
- **Access control**: Limit access to configuration and session files

### Known Security Considerations

- **File access**: The application reads and processes code files
- **Data storage**: Session data is stored locally in pickle format
- **Network**: No network communication by default
- **Execution**: No code execution - only analysis and display

### Vulnerability Disclosure Timeline

- **Day 0**: Vulnerability reported
- **Day 1-2**: Acknowledgment and initial assessment
- **Day 3-14**: Investigation and fix development
- **Day 15-30**: Testing and validation
- **Day 30+**: Public disclosure and release

We aim to resolve critical vulnerabilities within 30 days of responsible disclosure.

## Security Features

VAITP-Auditor includes several security features:

- **No code execution**: Only displays and analyzes code
- **Local processing**: No data sent to external servers
- **File validation**: Input validation for data files
- **Session encryption**: Session data can be encrypted (optional)

## Contact

For security-related questions or concerns:

- **Email**: security@vaitp-auditor.com
- **GPG Key**: [Public key if available]
- **Response time**: Within 48 hours for security issues

Thank you for helping keep VAITP-Auditor secure!
