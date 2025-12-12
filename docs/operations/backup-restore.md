# Backup and Recovery

This guide covers backup procedures, disaster recovery planning, and data restoration for CasareRPA deployments.

---

## Overview

CasareRPA stores data in several locations:

| Data Type | Location | Backup Priority |
|-----------|----------|-----------------|
| Workflows | Database / JSON files | Critical |
| Credentials | Vault / Encrypted storage | Critical |
| Execution Logs | Database / Log files | Important |
| Configuration | Config files / Environment | Important |
| Metrics | Time-series database | Optional |
| Checkpoints | Local storage | Optional |

---

## Backup Strategy

### 3-2-1 Rule

- **3** copies of data
- **2** different storage types
- **1** offsite copy

### Backup Schedule

| Data Type | Frequency | Retention |
|-----------|-----------|-----------|
| Database | Daily | 30 days |
| Workflows | On change + daily | 90 days |
| Credentials | On change | 90 days |
| Configuration | On change | 30 days |
| Logs | Daily | 14 days |

---

## Database Backup

### PostgreSQL

#### Full Backup

```bash
# Full database backup
pg_dump -h localhost -U postgres -d casare \
  --format=custom \
  --file=casare_backup_$(date +%Y%m%d).dump

# Compressed backup
pg_dump -h localhost -U postgres -d casare | gzip > casare_$(date +%Y%m%d).sql.gz
```

#### Automated Daily Backup

```bash
#!/bin/bash
# /opt/scripts/backup_db.sh

BACKUP_DIR="/backups/postgres"
DB_HOST="localhost"
DB_USER="postgres"
DB_NAME="casare"
RETENTION_DAYS=30

# Create backup
BACKUP_FILE="$BACKUP_DIR/casare_$(date +%Y%m%d_%H%M%S).dump"
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --format=custom \
  --file=$BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Remove old backups
find $BACKUP_DIR -name "*.dump.gz" -mtime +$RETENTION_DAYS -delete

# Upload to S3 (optional)
aws s3 cp ${BACKUP_FILE}.gz s3://backups/casare/
```

Add to crontab:

```bash
# Daily at 2 AM
0 2 * * * /opt/scripts/backup_db.sh >> /var/log/backup.log 2>&1
```

#### Verify Backup

```bash
# List contents
pg_restore --list casare_backup.dump

# Test restore to temp database
createdb casare_test
pg_restore -d casare_test casare_backup.dump
dropdb casare_test
```

---

## Workflow Backup

### Export via CLI

```bash
# Export all workflows
casare-rpa orchestrator export-workflows \
  --output workflows_backup_$(date +%Y%m%d).json

# Export specific workflow
casare-rpa orchestrator export-workflow WF_123 \
  --output workflow_123.json

# Export with execution history
casare-rpa orchestrator export-workflows \
  --include-history \
  --output workflows_full_backup.json
```

### Automated Workflow Backup

```bash
#!/bin/bash
# /opt/scripts/backup_workflows.sh

BACKUP_DIR="/backups/workflows"
DATE=$(date +%Y%m%d)

# Export all workflows
casare-rpa orchestrator export-workflows \
  --output $BACKUP_DIR/workflows_$DATE.json

# Compress
gzip $BACKUP_DIR/workflows_$DATE.json

# Sync to remote
rsync -avz $BACKUP_DIR/ backup-server:/backups/casare/workflows/
```

### Git-Based Backup

Store workflows in version control:

```bash
# Initial setup
cd /path/to/workflows
git init
git remote add origin git@backup:casare-workflows.git

# Automated commit and push
#!/bin/bash
cd /path/to/workflows
casare-rpa orchestrator export-workflows --output workflows.json
git add .
git commit -m "Workflow backup $(date +%Y%m%d_%H%M%S)" || true
git push origin main
```

---

## Credential Backup

### Vault Backup

If using HashiCorp Vault:

```bash
# Vault snapshot
vault operator raft snapshot save vault_snapshot_$(date +%Y%m%d).snap

# Restore
vault operator raft snapshot restore vault_snapshot.snap
```

### Local Credential Backup

> **Warning:** Handle credential backups with extreme care.

```bash
# Export credentials (encrypted)
casare-rpa credentials export \
  --encryption-key $BACKUP_KEY \
  --output credentials_$(date +%Y%m%d).enc

# Store encryption key separately from backup
echo $BACKUP_KEY > /secure/keys/backup_key_$(date +%Y%m%d)
```

---

## Configuration Backup

### Backup Config Files

```bash
#!/bin/bash
BACKUP_DIR="/backups/config"
DATE=$(date +%Y%m%d)

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
  /etc/casare-rpa/ \
  ~/.casare-rpa/config/ \
  --exclude='*.log' \
  --exclude='*.tmp'

# Backup environment files
cp /etc/casare-rpa/.env $BACKUP_DIR/env_$DATE
```

### Version Configuration

```bash
# Track config changes in git
cd /etc/casare-rpa
git init
git add -A
git commit -m "Configuration $(date +%Y%m%d)"
```

---

## Log Backup

### Compress and Archive

```bash
#!/bin/bash
LOG_DIR="/var/log/casare-rpa"
ARCHIVE_DIR="/backups/logs"
DATE=$(date +%Y%m%d)

# Compress logs older than 1 day
find $LOG_DIR -name "*.log" -mtime +1 -exec gzip {} \;

# Move to archive
mv $LOG_DIR/*.gz $ARCHIVE_DIR/

# Retain for 14 days
find $ARCHIVE_DIR -name "*.gz" -mtime +14 -delete
```

### Ship to Log Aggregator

```yaml
# filebeat.yml
output.elasticsearch:
  hosts: ["logs.example.com:9200"]
  index: "casare-logs-%{+yyyy.MM.dd}"
```

---

## Checkpoint Backup

Checkpoints enable crash recovery for long-running workflows:

```bash
# Backup checkpoints
CHECKPOINT_DIR="~/.casare-rpa/checkpoints"
BACKUP_DIR="/backups/checkpoints"

# Sync checkpoints
rsync -avz $CHECKPOINT_DIR/ $BACKUP_DIR/

# Or with timestamp
tar -czf $BACKUP_DIR/checkpoints_$(date +%Y%m%d).tar.gz $CHECKPOINT_DIR/
```

---

## Restore Procedures

### Database Restore

```bash
# Full restore
pg_restore -h localhost -U postgres -d casare \
  --clean --if-exists \
  casare_backup.dump

# Restore to new database
createdb casare_restored
pg_restore -d casare_restored casare_backup.dump

# From compressed SQL
gunzip -c casare_backup.sql.gz | psql -h localhost -U postgres -d casare
```

### Workflow Restore

```bash
# Import workflows
casare-rpa orchestrator import-workflows \
  --input workflows_backup.json

# Import with conflict resolution
casare-rpa orchestrator import-workflows \
  --input workflows_backup.json \
  --on-conflict replace  # or skip, rename
```

### Credential Restore

```bash
# Restore credentials
casare-rpa credentials import \
  --input credentials_backup.enc \
  --encryption-key $BACKUP_KEY
```

### Configuration Restore

```bash
# Restore configuration
tar -xzf config_backup.tar.gz -C /

# Restore environment
cp env_backup /etc/casare-rpa/.env

# Restart services
systemctl restart casare-orchestrator
systemctl restart casare-robot
```

---

## Disaster Recovery

### Recovery Time Objective (RTO)

| Scenario | Target RTO |
|----------|------------|
| Single service failure | < 5 minutes |
| Database failure | < 30 minutes |
| Full system restore | < 4 hours |
| Datacenter failure | < 24 hours |

### Recovery Point Objective (RPO)

| Data Type | Target RPO |
|-----------|------------|
| Workflow definitions | < 1 hour |
| Execution state | < 5 minutes |
| Logs | < 1 day |

### DR Runbook

#### 1. Assessment

```bash
# Check service status
systemctl status casare-*

# Check database connectivity
casare-rpa orchestrator check-db

# Check recent backups
ls -la /backups/*/
```

#### 2. Decision Tree

```
Is database accessible?
├── Yes -> Check application services
│   ├── Orchestrator down -> Restart orchestrator
│   ├── Robots offline -> Restart robots
│   └── Both working -> Check network/load balancer
│
└── No -> Database recovery needed
    ├── Primary available -> Failover to replica
    └── Need full restore -> Restore from backup
```

#### 3. Database Recovery

```bash
# If replica available
# Promote replica to primary
pg_ctl promote -D /var/lib/postgresql/data

# If restore needed
createdb casare
pg_restore -d casare /backups/latest/casare.dump
```

#### 4. Application Recovery

```bash
# Restore configuration
tar -xzf /backups/config/latest.tar.gz -C /

# Import workflows if needed
casare-rpa orchestrator import-workflows --input /backups/workflows/latest.json

# Start services
systemctl start casare-orchestrator
systemctl start casare-robot

# Verify health
curl http://localhost:8000/health
```

#### 5. Verification

```bash
# Check orchestrator
curl http://localhost:8000/health

# Check robots connecting
curl http://localhost:8000/api/v1/robots

# Run test workflow
casare-rpa run test_workflow.json

# Verify recent data
casare-rpa orchestrator list-jobs --since "1 hour ago"
```

---

## Monitoring Backups

### Backup Job Monitoring

```yaml
# prometheus alert
- alert: BackupFailed
  expr: backup_job_success{job="casare-backup"} == 0
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "CasareRPA backup failed"

- alert: BackupTooOld
  expr: time() - backup_last_success_timestamp > 86400
  for: 0m
  labels:
    severity: critical
  annotations:
    summary: "No successful backup in 24 hours"
```

### Verify Backup Integrity

```bash
#!/bin/bash
# Run weekly

# Test database restore
pg_restore --list /backups/postgres/latest.dump > /dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Database backup corrupt" | mail -s "Backup Alert" admin@example.com
fi

# Test workflow backup
python -c "import json; json.load(open('/backups/workflows/latest.json'))"
if [ $? -ne 0 ]; then
    echo "ERROR: Workflow backup corrupt" | mail -s "Backup Alert" admin@example.com
fi
```

---

## Cloud Backup

### AWS S3

```bash
# Sync backups to S3
aws s3 sync /backups/ s3://casare-backups/ --storage-class STANDARD_IA

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket casare-backups \
  --versioning-configuration Status=Enabled

# Set lifecycle policy (move to Glacier after 30 days)
aws s3api put-bucket-lifecycle-configuration \
  --bucket casare-backups \
  --lifecycle-configuration file://lifecycle.json
```

### Azure Blob Storage

```bash
# Upload to Azure
az storage blob upload-batch \
  --destination casare-backups \
  --source /backups/
```

### Google Cloud Storage

```bash
# Upload to GCS
gsutil -m rsync -r /backups/ gs://casare-backups/
```

---

## Backup Checklist

### Daily

- [ ] Database backup completed
- [ ] Backup uploaded to remote storage
- [ ] Backup size within expected range
- [ ] No backup job errors

### Weekly

- [ ] Test restore to staging environment
- [ ] Verify backup file integrity
- [ ] Check backup storage capacity
- [ ] Review backup logs

### Monthly

- [ ] Full disaster recovery test
- [ ] Verify credentials backup
- [ ] Update DR documentation
- [ ] Review and update backup retention

### Quarterly

- [ ] Restore to isolated environment
- [ ] Verify all data types restored correctly
- [ ] Test full workflow execution
- [ ] Document any issues and fixes

---

## Related Documentation

- [Runbook](runbook.md) - Operating procedures
- [Troubleshooting](troubleshooting.md) - Common issues
- [Monitoring](../user-guide/deployment/monitoring.md) - Metrics and alerting
- [Security](../security/best-practices.md) - Security guidelines
