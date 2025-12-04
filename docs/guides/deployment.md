# Deployment Guide

Deploy CasareRPA to production.

## Deployment Options

| Option | Use Case |
|--------|----------|
| Local | Development, testing |
| Standalone Robot | Single machine |
| Orchestrated | Multiple robots |
| Cloud | Scalable deployment |

## Standalone Deployment

### Install Robot

```bash
pip install casare-rpa
casare-robot install
```

### Configure

```yaml
# robot.yaml
name: production-robot
environment: production
orchestrator_url: https://orchestrator.example.com
```

### Run

```bash
casare-robot start
```

## Orchestrator Deployment

### Deploy Orchestrator

```bash
docker-compose up -d
```

### Register Robots

```bash
casare-robot register --orchestrator https://orchestrator.example.com
```

### Monitor

Access dashboard at `https://orchestrator.example.com/dashboard`

## Security Considerations

1. **Use HTTPS** for all connections
2. **Secure credentials** in vault
3. **Limit permissions** per robot
4. **Enable audit logging**
5. **Regular updates**

## Related

- [Orchestrator API](../api/infrastructure/orchestrator-api.md)
