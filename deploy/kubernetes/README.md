# CasareRPA Kubernetes Deployment

Kustomize-based Kubernetes manifests for deploying CasareRPA orchestrator and robot fleet.

## Directory Structure

```
deploy/kubernetes/
├── base/                           # Base manifests (shared across environments)
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── common/
│   │   ├── secrets.yaml           # Secret templates (use external-secrets in prod)
│   │   └── networkpolicy.yaml     # Network segmentation policies
│   ├── orchestrator/
│   │   ├── deployment.yaml        # Orchestrator + metrics sidecar
│   │   ├── service.yaml           # ClusterIP + headless services
│   │   ├── hpa.yaml               # Horizontal Pod Autoscaler
│   │   ├── configmap.yaml         # Application configuration
│   │   └── ingress.yaml           # Ingress with TLS
│   └── robot/
│       ├── deployment.yaml        # Browser robot deployment
│       ├── service.yaml           # Robot service endpoints
│       ├── configmap.yaml         # Robot configuration
│       └── scaledobject.yaml      # KEDA ScaledObject for queue-based scaling
└── overlays/                       # Environment-specific overrides
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patches/
    ├── staging/
    │   ├── kustomization.yaml
    │   └── patches/
    └── prod/
        ├── kustomization.yaml
        └── patches/
```

## Prerequisites

1. **Kubernetes cluster** (1.25+)
2. **kubectl** configured with cluster access
3. **KEDA** installed for job-based scaling:
   ```bash
   kubectl apply --server-side -f https://github.com/kedacore/keda/releases/download/v2.13.0/keda-2.13.0.yaml
   ```
4. **cert-manager** for TLS certificates:
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml
   ```
5. **nginx-ingress** controller:
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.5/deploy/static/provider/cloud/deploy.yaml
   ```

## Deployment Commands

### Development Environment

```bash
# Preview what will be deployed
kubectl kustomize deploy/kubernetes/overlays/dev

# Apply to cluster
kubectl apply -k deploy/kubernetes/overlays/dev

# Verify deployment
kubectl -n casare-rpa-dev get all
```

### Staging Environment

```bash
# Preview
kubectl kustomize deploy/kubernetes/overlays/staging

# Apply
kubectl apply -k deploy/kubernetes/overlays/staging

# Verify
kubectl -n casare-rpa-staging get all
```

### Production Environment

```bash
# Preview (ALWAYS preview before applying to prod!)
kubectl kustomize deploy/kubernetes/overlays/prod | less

# Apply
kubectl apply -k deploy/kubernetes/overlays/prod

# Verify
kubectl -n casare-rpa get all,ingress,hpa,scaledobject
```

## Environment Comparison

| Feature | Dev | Staging | Prod |
|---------|-----|---------|------|
| Orchestrator Replicas | 1 | 2 | 3 |
| Robot Replicas (min) | 1 | 2 | 5 |
| Robot Replicas (max) | 5 | 20 | 100 |
| Orchestrator CPU (request/limit) | 100m/500m | 200m/750m | 500m/2000m |
| Orchestrator Memory (request/limit) | 256Mi/512Mi | 384Mi/768Mi | 1Gi/2Gi |
| Robot CPU (request/limit) | 250m/1000m | 400m/1500m | 750m/3000m |
| Robot Memory (request/limit) | 512Mi/2Gi | 768Mi/3Gi | 2Gi/6Gi |
| TLS | None | Self-signed | Let's Encrypt |
| Rate Limiting (RPS) | 1000 | 200 | 100 |
| Log Level | DEBUG | INFO | INFO |

## KEDA Configuration

KEDA scales robot pods based on:

1. **Queue depth**: Pending jobs in PostgreSQL `job_queue` table
2. **Business hours**: Higher baseline during 8 AM - 6 PM weekdays
3. **Off-hours**: Lower baseline after hours
4. **Weekends**: Minimal baseline

### Custom Scaling Query

The default query checks pending browser jobs:
```sql
SELECT COUNT(*) FROM job_queue WHERE status = 'pending' AND robot_type = 'browser'
```

Modify in `base/robot/scaledobject.yaml` or overlay patches to adjust.

## TLS Setup

### Development (No TLS)
No TLS configuration needed.

### Staging (Self-signed)
Create a self-signed ClusterIssuer:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned-issuer
spec:
  selfSigned: {}
```

### Production (Let's Encrypt)
Create a production ClusterIssuer:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
      - http01:
          ingress:
            class: nginx
```

## Secrets Management

### Development/Staging
Secrets are generated via Kustomize `secretGenerator` with placeholder values.

### Production
Use external-secrets operator to sync from your secrets manager:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: casare-secrets
  namespace: casare-rpa
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: casare-secrets
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: casare-rpa/production/database
        property: url
    - secretKey: JWT_SECRET_KEY
      remoteRef:
        key: casare-rpa/production/jwt
        property: secret
```

## Monitoring

### Prometheus Metrics
Both orchestrator and robot pods expose metrics on port 9090:
- Orchestrator: `/metrics` via statsd-exporter sidecar
- Robot: `/metrics` endpoint

### Service Monitor (if using Prometheus Operator)
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: casare-rpa
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/part-of: casare-rpa
  namespaceSelector:
    matchNames:
      - casare-rpa
  endpoints:
    - port: metrics
      interval: 30s
```

## Troubleshooting

### Check KEDA ScaledObject status
```bash
kubectl -n casare-rpa describe scaledobject casare-robot-scaler
```

### View robot scaling events
```bash
kubectl -n casare-rpa get events --sort-by='.lastTimestamp' | grep -i scale
```

### Check orchestrator logs
```bash
kubectl -n casare-rpa logs -l app.kubernetes.io/name=casare-orchestrator -c orchestrator -f
```

### Check robot logs
```bash
kubectl -n casare-rpa logs -l app.kubernetes.io/name=casare-browser-robot -f
```

### Verify network policies
```bash
kubectl -n casare-rpa get networkpolicies
kubectl -n casare-rpa describe networkpolicy allow-orchestrator-ingress
```

## Rollback

```bash
# Rollback orchestrator
kubectl -n casare-rpa rollout undo deployment/casare-orchestrator

# Rollback robot
kubectl -n casare-rpa rollout undo deployment/casare-browser-robot

# Check rollout history
kubectl -n casare-rpa rollout history deployment/casare-orchestrator
```
