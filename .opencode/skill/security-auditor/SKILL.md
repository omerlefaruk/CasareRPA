---
name: security-auditor
description: Security auditing with OWASP Top 10 2025 compliance and vulnerability detection
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: security
---

## What I do

- Perform security audits on code
- Identify vulnerabilities and security risks
- Check for hardcoded secrets and injection flaws
- Verify OWASP Top 10 2025 compliance

## When to use me

Use this when you need to:
- Audit code for security vulnerabilities
- Check for hardcoded secrets
- Validate input handling
- Review authentication/authorization

## MCP-First Workflow

Always use MCP servers in this order:

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

### Authorization
- [ ] Role-based access control (RBAC) implemented
- [ ] API endpoints check permissions
- [ ] No privilege escalation paths

### Secrets Management
- [ ] No hardcoded API keys/passwords
- [ ] Secrets loaded from environment variables
- [ ] .env files in .gitignore
- [ ] No secrets in logs

### API Security
- [ ] Input validation on all endpoints
- [ ] Rate limiting implemented
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
