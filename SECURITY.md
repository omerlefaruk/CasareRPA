# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |
| < 1.0   | :x:                |

## Reporting a Vulnerability

The CasareRPA team takes security seriously. We appreciate your efforts to responsibly disclose your findings.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security vulnerabilities by emailing:

**dev@casarerpa.com**

Include the following information:
- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the issue
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within **48 hours**.
- **Updates**: We will send you regular updates about our progress every **72 hours**.
- **Verification**: We will work with you to understand and verify the issue.
- **Fix Timeline**: We aim to release a fix within **30 days** for critical vulnerabilities.
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous).

### Security Update Process

1. **Triage**: We assess the severity and impact of the vulnerability
2. **Development**: We develop and test a fix
3. **Disclosure**: We prepare a security advisory
4. **Release**: We release the patched version
5. **Announcement**: We publish the security advisory

## Security Best Practices for Users

### Credential Management

CasareRPA supports HashiCorp Vault for secure credential storage:

```python
# NEVER store credentials in workflow files or code
# ❌ BAD
password = "my_password123"

# ✅ GOOD - Use Vault
from casare_rpa.utils.vault import get_secret
password = await get_secret("database/prod/password")
```

### Environment Variables

Use `.env` files for configuration (already in `.gitignore`):

```bash
# .env (NEVER commit to git)
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=your_vault_token
```

### Workflow Security

When creating workflows:

1. **Validate Input**: Always validate user input and external data
2. **Sanitize Selectors**: Avoid user-controlled CSS selectors (XSS risk)
3. **Limit Permissions**: Run workflows with minimum required privileges
4. **Audit Workflows**: Review workflows before deploying to production
5. **Use Secrets Manager**: Store all credentials in Vault, not in workflow JSON

### Known Security Considerations

#### 1. Workflow Execution

Workflows execute Python code. Only run workflows from trusted sources:

```python
# Python Script Node can execute arbitrary code
# ONLY use workflows you trust or have reviewed
```

**Mitigation**: Future versions will add workflow signing and sandboxing.

#### 2. Desktop Automation

UIAutomation can interact with any Windows application:

```python
# Desktop nodes can control applications
# Be cautious with automation of sensitive apps
```

**Mitigation**: Run CasareRPA in isolated environments when automating sensitive apps.

#### 3. Browser Automation

Playwright can access web pages and credentials:

```python
# Be careful with credential autofill
# Avoid automating on untrusted websites
```

**Mitigation**: Use incognito contexts for sensitive automation.

## Security Features

### Current

- ✅ Vault integration for secret management
- ✅ Environment variable support (`.env`)
- ✅ Secrets excluded from git (`.gitignore`)
- ✅ Async/await for secure timeout handling
- ✅ Type hints for input validation

### Planned (Future Versions)

- 🔄 Workflow signing and verification
- 🔄 Sandboxed Python script execution
- 🔄 Permission system for nodes
- 🔄 Audit logging for sensitive operations
- 🔄 RBAC (Role-Based Access Control) for Orchestrator

## Vulnerability Disclosure Policy

We follow **Coordinated Vulnerability Disclosure**:

1. **Private Reporting**: Security researchers report vulnerabilities privately
2. **Coordinated Fix**: We work together to understand and fix the issue
3. **Public Disclosure**: After a fix is released, we publish a security advisory
4. **Recognition**: We credit researchers in the advisory (with their permission)

### Timeline

- **Day 0**: Vulnerability reported
- **Day 1-2**: Acknowledgment sent
- **Day 3-14**: Investigation and fix development
- **Day 15-30**: Testing and release preparation
- **Day 30**: Security advisory published (or earlier if actively exploited)

## Security Advisories

Security advisories are published at:
- GitHub Security Advisories: https://github.com/omerlefaruk/CasareRPA/security/advisories
- Project website: (Coming soon)

## Contact

For security concerns:
- **Email**: dev@casarerpa.com
- **PGP Key**: (Coming soon)

For general questions:
- **GitHub Issues**: https://github.com/omerlefaruk/CasareRPA/issues
- **GitHub Discussions**: https://github.com/omerlefaruk/CasareRPA/discussions

---

Thank you for helping keep CasareRPA and its users safe! 🔒
