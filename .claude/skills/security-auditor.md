# Security Auditor Skill

Security auditing with OWASP Top 10 2025 compliance and secret detection.

## MCP-First Workflow

1. **codebase** - Search for vulnerability patterns
   ```python
   search_codebase("security vulnerabilities Python injection", top_k=10)
   ```

2. **filesystem** - view_file the code under audit
   ```python
   read_file("src/casare_rpa/infrastructure/auth/")
   ```

3. **git** - Check for recent changes
   ```python
   git_diff("HEAD~10..HEAD", path="src/casare_rpa/infrastructure/")
   ```

4. **exa** - Research latest threats
   ```python
   web_search("OWASP Top 10 2025 Python vulnerabilities", num_results=5)
   ```

## Security Checklist

### Authentication
- [ ] JWT tokens have proper expiration
- [ ] Passwords are hashed (bcrypt/argon2)
- [ ] OAuth tokens stored securely
- [ ] Session management is secure
- [ ] No authentication bypass when disabled

### Authorization
- [ ] Role-based access control (RBAC) implemented
- [ ] API endpoints check permissions
- [ ] No privilege escalation paths
- [ ] Admin functions protected

### Secrets Management
- [ ] No hardcoded API keys/passwords
- [ ] Secrets loaded from environment variables
- [ ] .env files in .gitignore
- [ ] No secrets in logs
- [ ] Sensitive data masked in errors

### API Security
- [ ] Input validation on all endpoints
- [ ] Rate limiting implemented
- [ ] CORS properly configured
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)

## Common Vulnerabilities

### Hardcoded Secrets
```python
# BAD
api_key = "sk-1234567890"

# GOOD
api_key = os.environ.get("API_KEY")
```

### SQL Injection
```python
# BAD
query = f"SELECT * FROM users WHERE id = {user_id}"

# GOOD
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

### Path Traversal
```python
# BAD
file_path = f"/uploads/{user_input}"

# GOOD
safe_path = os.path.basename(user_input)
file_path = os.path.join("/uploads", safe_path)
```

## Audit Report Format

```markdown
## Security Audit: [File/Module]

### 🔴 Critical
**Issue:** Hardcoded API key
**Location:** `src/module.py:42`
**Risk:** Credential exposure
**Fix:** Move to environment variable

### 🟠 High
**Issue:** Missing input validation
**Location:** `api/routes.py:78`
**Risk:** Injection attack
**Fix:** Add input sanitization
```

## Example Usage

```python
Skill(skill="security-auditor", prompt="""
Audit the workflow JSON parsing for security:

MCP Workflow:
1. codebase: Search for "JSON injection Python security patterns"
2. filesystem: Read src/casare_rpa/infrastructure/parsing/
3. git: Check recent parsing changes
4. exa: Research JSON parsing vulnerabilities 2025

Provide:
- Critical/high/medium findings
- File:line references
- Remediation suggestions
""")
```
