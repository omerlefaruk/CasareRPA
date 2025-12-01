# CasareRPA Hybrid Deployment Architecture

## Overview

CasareRPA supports hybrid cloud deployment where the control plane runs in the cloud while robot agents execute on-premises or in private networks. This architecture provides:

- **Security**: On-prem robots never expose inbound ports
- **Compliance**: Sensitive data stays within corporate network
- **Flexibility**: Mix cloud and on-prem robots as needed
- **Scalability**: Cloud control plane handles orchestration

## Architecture Diagram

```
                    CLOUD (AWS/Azure/GCP)
    ┌─────────────────────────────────────────────────────┐
    │                                                     │
    │   ┌──────────────┐     ┌──────────────────────┐    │
    │   │  PostgreSQL  │◄────│  Control Plane API   │    │
    │   │   (RDS)      │     │  (FastAPI + WS)      │    │
    │   └──────────────┘     └──────────┬───────────┘    │
    │                                   │                 │
    │   ┌──────────────┐                │                 │
    │   │    Redis     │◄───────────────┤                 │
    │   │  (ElastiCache)│               │                 │
    │   └──────────────┘                │                 │
    │                                   │                 │
    │   ┌─────────────────────────────┐ │                 │
    │   │    Cloud Browser Robots     │◄┘                 │
    │   │  (Kubernetes - Auto-scale)  │                   │
    │   └─────────────────────────────┘                   │
    │                                                     │
    └─────────────────────────────────────────────────────┘
                           │
                           │ TLS 1.3 + mTLS
                           │ (Outbound Only)
                           ▼
    ─────────────────── FIREWALL ──────────────────────────
                           │
    ┌─────────────────────────────────────────────────────┐
    │              ON-PREMISES / PRIVATE CLOUD            │
    │                                                     │
    │   ┌─────────────────┐     ┌─────────────────┐      │
    │   │  Windows Robot  │     │  Desktop Robot  │      │
    │   │  (Browser +     │     │  (UIAutomation) │      │
    │   │   Desktop)      │     │                 │      │
    │   └─────────────────┘     └─────────────────┘      │
    │                                                     │
    │   ┌─────────────────────────────────────────┐      │
    │   │         Corporate Applications          │      │
    │   │  (SAP, Oracle, Legacy Windows Apps)     │      │
    │   └─────────────────────────────────────────┘      │
    │                                                     │
    └─────────────────────────────────────────────────────┘
```

## Components

### Control Plane (Cloud)

| Component | Purpose | Technology |
|-----------|---------|------------|
| API Server | Job management, WebSocket gateway | FastAPI |
| Job Queue | Work distribution | PostgreSQL + Redis |
| Robot Registry | Track connected robots | PostgreSQL |
| Scheduler | Cron/trigger management | APScheduler |
| Metrics | Monitoring | Prometheus + Grafana |

### Robot Agent (On-Premises)

| Component | Purpose | Technology |
|-----------|---------|------------|
| Agent Tunnel | Secure connection to cloud | WebSocket + mTLS |
| Workflow Engine | Execute automation | CasareRPA Core |
| Browser Automation | Web tasks | Playwright |
| Desktop Automation | Windows apps | UIAutomation |

## Security Model

### mTLS Authentication

All robot-to-control-plane communication uses mutual TLS:

1. **CA Certificate**: Root certificate authority (cloud-hosted)
2. **Robot Certificate**: Unique cert per robot (signed by CA)
3. **Robot Private Key**: Never leaves on-prem

```python
from casare_rpa.infrastructure.tunnel import MTLSConfig, AgentTunnel, TunnelConfig

# Configure mTLS
mtls_config = MTLSConfig(
    ca_cert_path=Path("/certs/ca.crt"),
    client_cert_path=Path("/certs/robot.crt"),
    client_key_path=Path("/certs/robot.key"),
)

# Connect to control plane
tunnel = AgentTunnel(TunnelConfig(
    control_plane_url="wss://api.casarerpa.com/ws/robot",
    mtls_config=mtls_config,
    robot_name="Office-Robot-01",
))

await tunnel.connect()
```

### Certificate Generation

```python
from casare_rpa.infrastructure.tunnel import CertificateManager

# Generate CA (one-time, cloud-side)
cert_mgr = CertificateManager(base_dir=Path("/certs"))
ca_cert, ca_key = cert_mgr.generate_ca(
    common_name="CasareRPA CA",
    organization="Acme Corp",
    validity_days=3650  # 10 years
)

# Generate robot certificate (per robot)
robot_cert, robot_key = cert_mgr.generate_certificate(
    common_name="robot-office-01",
    ca_cert_path=ca_cert,
    ca_key_path=ca_key,
    validity_days=365
)
```

### Network Security

| Direction | Port | Protocol | Purpose |
|-----------|------|----------|---------|
| Outbound | 443 | WSS | Robot → Control Plane |
| None | - | - | No inbound ports required |

Firewall rules for on-prem robots:
- Allow HTTPS (443) outbound to control plane domain
- Block all inbound connections
- Optional: Allow NTP (123) for time sync

## Installation

### Windows Robot (On-Premises)

#### Automated Installation

```powershell
# Download and run installer
Invoke-WebRequest -Uri "https://releases.casarerpa.com/install-robot.ps1" -OutFile install-robot.ps1

# Install with control plane URL
.\install-robot.ps1 `
    -ControlPlaneUrl "wss://api.casarerpa.com/ws/robot" `
    -RobotName "Office-Robot-01" `
    -InstallDir "C:\CasareRPA"
```

#### Manual Installation

1. Install Python 3.12+
2. Create virtual environment:
   ```powershell
   python -m venv C:\CasareRPA\venv
   C:\CasareRPA\venv\Scripts\pip install casare-rpa
   ```
3. Copy certificates to `C:\CasareRPA\certs\`
4. Create configuration file
5. Run or install as service

### Certificate Distribution

Certificates must be securely distributed to on-prem robots:

| Method | Security | Automation |
|--------|----------|------------|
| Manual copy | High | Low |
| Secure file share | Medium | Medium |
| HashiCorp Vault | High | High |
| Azure Key Vault | High | High |

Example with Vault:
```bash
# Robot retrieves its certificate
vault kv get -field=cert secret/robots/office-01 > robot.crt
vault kv get -field=key secret/robots/office-01 > robot.key
```

## Robot Lifecycle

### Connection States

```
DISCONNECTED → CONNECTING → CONNECTED → AUTHENTICATING → REGISTERED
      ↑                                                      │
      │                    RECONNECTING                      │
      └──────────────────────────────────────────────────────┘
```

### Heartbeat Protocol

Robots send heartbeats every 30 seconds (configurable):

```json
{
    "type": "heartbeat",
    "robot_id": "robot-abc123",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

Control plane marks robot offline after 3 missed heartbeats.

### Job Assignment

1. Control plane assigns job to registered robot:
   ```json
   {
       "type": "job_assign",
       "job_id": "job-xyz789",
       "workflow_json": {...},
       "priority": 1
   }
   ```

2. Robot accepts or rejects:
   ```json
   {
       "type": "job_accept",
       "job_id": "job-xyz789",
       "robot_id": "robot-abc123"
   }
   ```

3. Robot reports progress:
   ```json
   {
       "type": "job_progress",
       "job_id": "job-xyz789",
       "progress": 50,
       "message": "Processing page 5 of 10"
   }
   ```

4. Robot reports completion:
   ```json
   {
       "type": "job_complete",
       "job_id": "job-xyz789",
       "result": {"records_processed": 100}
   }
   ```

## Scaling Strategy

### Cloud Robots (Browser Automation)

- Auto-scale based on job queue depth
- Use Kubernetes HPA or KEDA
- Target: 1 robot per 10 pending jobs

### On-Prem Robots (Desktop Automation)

- Fixed capacity (physical machines)
- Use tags for routing:
  - `location:office-ny` - New York office
  - `app:sap` - SAP-capable robot
  - `priority:high` - Reserved for critical jobs

## Monitoring

### Robot Metrics (Prometheus)

```
# Robot status
casare_robot_status{robot_id="robot-abc123", status="idle"} 1

# Jobs executed
casare_robot_jobs_total{robot_id="robot-abc123", status="completed"} 156
casare_robot_jobs_total{robot_id="robot-abc123", status="failed"} 3

# Connection uptime
casare_robot_connected_seconds{robot_id="robot-abc123"} 86400
```

### Grafana Dashboards

Import dashboard from `deploy/grafana/hybrid-dashboard.json`:
- Robot availability map
- Job throughput by robot
- Error rates
- Connection status timeline

## Troubleshooting

### Robot Won't Connect

1. **Check certificates**:
   ```powershell
   openssl x509 -in C:\CasareRPA\certs\robot.crt -noout -dates
   ```

2. **Verify network**:
   ```powershell
   Test-NetConnection -ComputerName api.casarerpa.com -Port 443
   ```

3. **Check logs**:
   ```powershell
   Get-Content C:\CasareRPA\logs\robot.log -Tail 100
   ```

### Job Failures

1. Check execution logs on robot
2. Verify workflow compatibility (browser vs desktop)
3. Check target application availability

### Certificate Expiration

Certificates expire after 1 year by default. Monitor with:
```python
cert_mgr.check_expiration(Path("robot.crt"))  # Returns (is_valid, days_remaining)
```

## Best Practices

1. **Certificate Rotation**: Rotate certificates 30 days before expiration
2. **Network Segmentation**: Place robots in dedicated VLAN
3. **Least Privilege**: Robot accounts should only access required applications
4. **Audit Logging**: Enable audit logs on control plane
5. **Backup Certificates**: Store CA private key in HSM or secure vault

## Migration from Full Cloud

To migrate robots from cloud to on-prem:

1. Generate certificates for on-prem robot
2. Install robot agent on Windows machine
3. Update workflow routing rules
4. Test connectivity and job execution
5. Decommission cloud robot replica

## Related Documentation

- [Cloud Deployment Guide](./CLOUD_DEPLOYMENT.md)
- [Security Hardening](./SECURITY.md)
- [API Reference](./API_REFERENCE.md)
