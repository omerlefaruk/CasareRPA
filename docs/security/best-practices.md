# Security Best Practices

This guide outlines security best practices for deploying and operating CasareRPA in production environments.

## Credential Security

### Never Hardcode Credentials

Credentials should never appear in workflow files, source code, or configuration files.

```python
# BAD: Hardcoded credentials
async def login(page: Page):
    await page.fill("#username", "admin")
    await page.fill("#password", "P@ssw0rd123")  # NEVER DO THIS!

# GOOD: Use credential store
async def login(page: Page, credential_id: str):
    store = get_credential_store()
    creds = store.get_credential(credential_id)
    await page.fill("#username", creds["username"])
    await page.fill("#password", creds["password"])
```

### Use Environment Variables for Secrets

Application secrets should be loaded from environment variables, not config files.

```python
# BAD: Secrets in config file
# config.yaml
# database:
#   password: "secret123"

# GOOD: Environment variables
import os

DATABASE_PASSWORD = os.environ.get("CASARE_DB_PASSWORD")
JWT_SECRET = os.environ.get("CASARE_JWT_SECRET")
ENCRYPTION_KEY = os.environ.get("CASARE_ENCRYPTION_KEY")

# Validate required secrets at startup
required_secrets = ["CASARE_DB_PASSWORD", "CASARE_JWT_SECRET", "CASARE_ENCRYPTION_KEY"]
missing = [s for s in required_secrets if not os.environ.get(s)]
if missing:
    raise RuntimeError(f"Missing required secrets: {missing}")
```

### Secure Environment Variable Loading

```python
from pydantic import BaseSettings, SecretStr

class SecuritySettings(BaseSettings):
    """Security settings loaded from environment."""
    jwt_secret: SecretStr
    encryption_key: SecretStr
    database_password: SecretStr
    vault_token: SecretStr = None

    class Config:
        env_prefix = "CASARE_"
        env_file = ".env"
        env_file_encoding = "utf-8"

# Usage
settings = SecuritySettings()
# Access secret value: settings.jwt_secret.get_secret_value()
```

### Credential Rotation Policy

Implement regular credential rotation:

| Credential Type | Rotation Frequency | Method |
|-----------------|-------------------|--------|
| API Keys | 90 days | Manual or automated |
| Database Passwords | 90 days | Vault auto-rotation |
| OAuth Tokens | Automatic | Refresh token flow |
| Robot API Keys | Annual | Manual with overlap period |
| Encryption Keys | Annual | Key rotation with re-encryption |

```python
from datetime import datetime, timedelta

async def check_credential_rotation():
    """Check for credentials needing rotation."""
    store = get_credential_store()
    alerts = []

    for cred in store.list_credentials():
        age_days = (datetime.now() - cred.updated_at).days

        if cred.credential_type == CredentialType.API_KEY and age_days > 90:
            alerts.append(f"API Key '{cred.name}' is {age_days} days old")
        elif cred.credential_type == CredentialType.USERNAME_PASSWORD and age_days > 90:
            alerts.append(f"Password '{cred.name}' is {age_days} days old")

    if alerts:
        await send_security_alert(alerts)
```

## Minimal Privilege Principle

### RBAC Configuration

Assign users the minimum permissions required for their role:

```python
from casare_rpa.infrastructure.security.rbac import RBACManager, Role

rbac = RBACManager()

# Developer: Can create workflows but not execute in production
rbac.assign_role(user_id, Role.DEVELOPER)

# Operator: Can execute workflows but not modify them
rbac.assign_role(user_id, Role.OPERATOR)

# Viewer: Read-only access for auditing
rbac.assign_role(user_id, Role.VIEWER)
```

### Credential Scope Restrictions

Create credentials with minimal scope:

```python
# BAD: Overly permissive
store.save_credential(
    name="Google Full Access",
    credential_type=CredentialType.GOOGLE_OAUTH,
    data={
        "scopes": [
            "https://www.googleapis.com/auth/gmail",  # Full Gmail access
            "https://www.googleapis.com/auth/drive"   # Full Drive access
        ]
    }
)

# GOOD: Minimal scope
store.save_credential(
    name="Google Gmail Read",
    credential_type=CredentialType.GOOGLE_OAUTH,
    data={
        "scopes": [
            "https://www.googleapis.com/auth/gmail.readonly"  # Read-only
        ]
    }
)
```

### Robot Agent Permissions

Limit robot capabilities based on their purpose:

```python
# Production robot: Only execute assigned workflows
robot_key = await key_manager.create_key(
    robot_id=robot.id,
    scopes=[
        "execution.run",
        "heartbeat.send",
        "logs.write"
    ]
)

# Test robot: Extended permissions for testing
test_robot_key = await key_manager.create_key(
    robot_id=test_robot.id,
    scopes=[
        "execution.run",
        "execution.debug",
        "heartbeat.send",
        "logs.write",
        "workflow.read"
    ]
)
```

## Secure Workflow Storage

### Workflow File Security

```python
# Set restrictive file permissions
import os
import stat

workflow_path = "/var/casare/workflows"

# Owner read/write only
os.chmod(workflow_path, stat.S_IRUSR | stat.S_IWUSR)

# For directories
os.chmod(workflow_path, stat.S_IRWXU)
```

### Workflow Encryption

For sensitive workflows, enable encryption:

```python
from casare_rpa.infrastructure.security import WorkflowEncryptor

encryptor = WorkflowEncryptor(encryption_key)

# Save encrypted workflow
encrypted_data = encryptor.encrypt(workflow_json)
with open(workflow_path, "wb") as f:
    f.write(encrypted_data)

# Load encrypted workflow
with open(workflow_path, "rb") as f:
    encrypted_data = f.read()
workflow_json = encryptor.decrypt(encrypted_data)
```

### Workflow Version Control

Track changes with audit trail:

```python
from casare_rpa.infrastructure.security.merkle_audit import log_audit_event

async def save_workflow(workflow: Workflow, user_id: UUID):
    # Save workflow
    await workflow_repository.save(workflow)

    # Log change
    await log_audit_event(
        action=AuditAction.WORKFLOW_UPDATE,
        actor_id=user_id,
        resource_type=ResourceType.WORKFLOW,
        resource_id=workflow.id,
        details={
            "version": workflow.version,
            "changed_nodes": workflow.get_changed_nodes()
        }
    )
```

## Network Security

### Firewall Configuration

Restrict Orchestrator API access:

```bash
# UFW example (Ubuntu)
# Allow only known IP ranges
ufw allow from 10.0.0.0/8 to any port 8000 proto tcp
ufw allow from 192.168.0.0/16 to any port 8000 proto tcp
ufw deny 8000

# For Robot agents, allow specific IPs
ufw allow from 10.0.1.100 to any port 8000 proto tcp  # Robot 1
ufw allow from 10.0.1.101 to any port 8000 proto tcp  # Robot 2
```

### TLS Configuration

Enforce TLS 1.3 for all connections:

```python
# Uvicorn SSL configuration
import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
ssl_context.load_cert_chain("cert.pem", "key.pem")

# Disable weak ciphers
ssl_context.set_ciphers(
    "ECDHE+AESGCM:DHE+AESGCM:ECDHE+CHACHA20:DHE+CHACHA20:!aNULL:!MD5:!DSS"
)
```

### VPN for Robot Communication

For robots outside the internal network:

```yaml
# Robot agent configuration
robot:
  orchestrator_url: "https://orchestrator.internal.example.com:8000"
  vpn:
    enabled: true
    type: wireguard
    config_file: "/etc/wireguard/casare.conf"
```

### Rate Limiting

Protect against brute-force attacks:

```python
from fastapi import FastAPI, Request
from fastapi.middleware.throttling import ThrottlingMiddleware

app = FastAPI()

# Global rate limit
app.add_middleware(
    ThrottlingMiddleware,
    rate_limit=100,  # requests
    time_window=60   # seconds
)

# Endpoint-specific limits
@app.post("/api/v1/auth/login")
@rate_limit(limit=5, window=300)  # 5 attempts per 5 minutes
async def login(request: Request):
    pass
```

## Robot Agent Security

### Secure Robot Deployment

```yaml
# Robot agent deployment checklist
security:
  # Run as non-root user
  user: casare-robot
  group: casare-robot

  # Restrict file system access
  readonly_paths:
    - /usr
    - /bin
    - /etc
  writable_paths:
    - /var/casare/work
    - /tmp/casare

  # Network restrictions
  allowed_hosts:
    - orchestrator.example.com
    - api.google.com  # For Google integrations

  # Resource limits
  memory_limit: 4G
  cpu_limit: 2
```

### Robot Isolation

For multi-tenant environments:

```python
# Each robot runs in isolated context
robot_config = RobotConfig(
    tenant_id=tenant.id,
    work_directory=f"/var/casare/tenants/{tenant.id}/work",
    log_directory=f"/var/casare/tenants/{tenant.id}/logs",
    temp_directory=f"/tmp/casare/{tenant.id}",
    network_namespace=f"casare-{tenant.id}"
)
```

### Robot API Key Management

```python
# Rotate robot keys annually
async def annual_robot_key_rotation():
    for robot in await robot_repository.list_all():
        key_age = datetime.now() - robot.api_key_created_at

        if key_age > timedelta(days=365):
            # Create new key
            new_key, new_key_id = await key_manager.create_key(
                robot_id=robot.id,
                tenant_id=robot.tenant_id
            )

            # Notify robot operator
            await notify_key_rotation(robot, new_key)

            # Schedule old key revocation (24h grace period)
            await scheduler.schedule(
                revoke_robot_key,
                args=[robot.old_key_id],
                run_at=datetime.now() + timedelta(hours=24)
            )
```

## Audit and Monitoring

### Enable Comprehensive Audit Logging

```python
from casare_rpa.infrastructure.security.merkle_audit import (
    MerkleAuditService,
    get_audit_service
)

# Initialize audit service with database persistence
audit_service = get_audit_service(db_pool=database_pool)

# All security events are automatically logged
# Configure log export for SIEM integration
```

### Security Event Monitoring

```python
from casare_rpa.infrastructure.security.merkle_audit import AuditAction

# Monitor for suspicious activities
SUSPICIOUS_PATTERNS = [
    (AuditAction.LOGIN_FAILED, 5, 300),  # 5 failures in 5 minutes
    (AuditAction.CREDENTIAL_ACCESS, 50, 3600),  # 50 accesses in 1 hour
    (AuditAction.API_KEY_CREATE, 10, 3600),  # 10 keys created in 1 hour
]

async def monitor_security_events():
    """Monitor for suspicious activity patterns."""
    audit = get_audit_service()

    for action, threshold, window_seconds in SUSPICIOUS_PATTERNS:
        recent_events = await audit.query_events(
            action=action,
            since=datetime.now() - timedelta(seconds=window_seconds)
        )

        # Group by actor
        actor_counts = Counter(e.actor_id for e in recent_events)

        for actor_id, count in actor_counts.items():
            if count >= threshold:
                await trigger_security_alert(
                    f"Suspicious activity: {count} {action.value} events "
                    f"from actor {actor_id} in {window_seconds}s"
                )
```

### Audit Log Integrity Verification

```python
# Regular integrity checks
async def verify_audit_integrity():
    """Verify audit log has not been tampered with."""
    audit = get_audit_service()

    result = await audit.verify_chain()

    if not result.is_valid:
        # CRITICAL: Audit log tampering detected
        await trigger_critical_alert(
            f"Audit log integrity failure: {result.error_message}"
        )
        # Preserve evidence
        await create_forensic_snapshot()
    else:
        logger.info(f"Audit integrity verified: {result.entries_verified} entries")
```

### SIEM Integration

```python
# Export audit logs to SIEM
async def export_to_siem():
    """Export audit logs to SIEM system."""
    audit = get_audit_service()

    export_data = await audit.export_audit_log(
        start_date=datetime.now() - timedelta(hours=1),
        include_proof=True
    )

    # Send to SIEM (Splunk, ELK, etc.)
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{SIEM_URL}/api/events",
            json=export_data,
            headers={"Authorization": f"Bearer {SIEM_TOKEN}"}
        )
```

## Incident Response

### Security Incident Playbook

```python
class SecurityIncident:
    """Handle security incidents."""

    async def handle_compromised_credential(self, credential_id: str):
        """Respond to compromised credential."""
        # 1. Immediately rotate the credential
        await credential_store.rotate_credential(credential_id)

        # 2. Identify affected workflows
        affected = await workflow_repository.find_using_credential(credential_id)

        # 3. Suspend affected workflows
        for workflow in affected:
            await workflow_repository.suspend(workflow.id)

        # 4. Alert security team
        await send_security_alert(
            severity="HIGH",
            message=f"Credential {credential_id} compromised",
            affected_workflows=[w.id for w in affected]
        )

        # 5. Log incident
        await log_audit_event(
            action=AuditAction.CREDENTIAL_UPDATE,
            actor_id=SYSTEM_ACTOR_ID,
            resource_type=ResourceType.CREDENTIAL,
            resource_id=credential_id,
            details={"reason": "compromised", "action": "emergency_rotation"}
        )

    async def handle_compromised_robot(self, robot_id: UUID):
        """Respond to compromised robot agent."""
        # 1. Revoke robot API key immediately
        robot = await robot_repository.get(robot_id)
        await key_manager.revoke_key(robot.api_key_id, reason="Compromised")

        # 2. Cancel all running jobs on this robot
        running_jobs = await job_repository.find_by_robot(robot_id, status="running")
        for job in running_jobs:
            await job_executor.cancel(job.id)

        # 3. Quarantine robot
        await robot_repository.update(robot_id, status="quarantined")

        # 4. Rotate all credentials the robot had access to
        accessed_creds = await audit.query_events(
            action=AuditAction.CREDENTIAL_ACCESS,
            actor_id=robot_id,
            since=datetime.now() - timedelta(days=7)
        )

        for event in accessed_creds:
            await credential_store.rotate_credential(event.resource_id)

        # 5. Alert and document
        await send_security_alert(
            severity="CRITICAL",
            message=f"Robot {robot_id} compromised and quarantined"
        )

    async def handle_brute_force_attack(self, source_ip: str):
        """Respond to brute force attack."""
        # 1. Block IP
        await firewall.block_ip(source_ip, duration_hours=24)

        # 2. Check for any successful logins from this IP
        successful_logins = await audit.query_events(
            action=AuditAction.LOGIN,
            ip_address=source_ip,
            since=datetime.now() - timedelta(hours=1)
        )

        # 3. If successful logins found, treat accounts as compromised
        for login in successful_logins:
            await self.handle_compromised_account(login.actor_id)

        # 4. Alert
        await send_security_alert(
            severity="MEDIUM",
            message=f"Brute force attack from {source_ip} blocked"
        )
```

### Emergency Procedures

```python
async def emergency_lockdown():
    """Emergency system lockdown procedure."""
    # 1. Disable all API keys
    await key_manager.disable_all_keys()

    # 2. Invalidate all sessions
    await session_manager.invalidate_all()

    # 3. Stop all running workflows
    await job_executor.cancel_all()

    # 4. Enable maintenance mode
    await config.set("maintenance_mode", True)

    # 5. Alert all administrators
    await send_emergency_alert("SYSTEM LOCKDOWN INITIATED")

    # 6. Log the event
    await log_audit_event(
        action=AuditAction.SYSTEM_CONFIG_CHANGE,
        actor_id=SYSTEM_ACTOR_ID,
        resource_type=ResourceType.SYSTEM,
        details={"action": "emergency_lockdown"}
    )
```

## Security Checklist

### Pre-Deployment

- [ ] All secrets loaded from environment variables
- [ ] Encryption keys generated with sufficient entropy
- [ ] TLS certificates installed and valid
- [ ] Firewall rules configured
- [ ] RBAC roles configured
- [ ] Audit logging enabled
- [ ] Backup encryption enabled

### Post-Deployment

- [ ] Security scan completed (no critical vulnerabilities)
- [ ] Penetration testing performed
- [ ] Audit log integrity verified
- [ ] Rate limiting tested
- [ ] Authentication flows tested
- [ ] Credential rotation scheduled

### Ongoing Operations

- [ ] Weekly: Review audit logs for anomalies
- [ ] Monthly: Verify audit log integrity
- [ ] Quarterly: Review and update RBAC permissions
- [ ] Quarterly: Rotate API keys and credentials
- [ ] Annually: Security assessment and penetration testing
- [ ] Annually: Review and update incident response procedures

## Related Documentation

- [Security Architecture](./architecture.md)
- [Authentication Methods](./authentication.md)
- [Credential Management](./credentials.md)
