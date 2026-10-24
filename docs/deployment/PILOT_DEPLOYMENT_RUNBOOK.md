# Gayatri Cloud — Pilot Deployment Runbook

**Document Version:** 1.0.0  
**Effective Date:** 2026-10-24  
**Classification:** Operational Guide / Restricted  
**Target Infrastructure:** AWS (Mumbai `ap-south-1` / Single-EC2 Pilot with RDS PostgreSQL & S3)

---

## 1. Architectural Overview & Pilot Topology

Gayatri Cloud's pilot topology is designed for **single-instance EC2 pilot deployment** with managed persistent storage:

```
[ Internet ]
     │
     ▼ HTTPS:443 (TLS 1.3 / Let's Encrypt)
[ AWS Network Firewall / Security Group ]
     │ Ingress: 80, 443 only (No Port 22 SSH)
     ▼
[ EC2 Instance: t4g.xlarge (ARM64 / Graviton) / Amazon Linux 2023 ]
     │
     ├── Nginx Reverse Proxy (Port 80/443)
     │     ├── /api/  ──▶ FastAPI Backend (Port 8000, 4 Uvicorn Workers)
     │     └── /      ──▶ Next.js Web Portal (Port 3000, Node.js Standalone)
     │
     ├── IAM Instance Profile (gayatri-ec2-pilot-role)
     │     ├── S3 Read/Write ──▶ S3 Storage Bucket (Course Artifacts)
     │     ├── S3 Archive ───▶ S3 Telemetry Bucket (Audit & Training Archives)
     │     └── SSM Access ───▶ AWS Systems Manager (Interactive Shell & Secrets)
     │
     └── Internal VPC Security Group (Port 5432)
           │
           ▼
[ RDS PostgreSQL 16 Multi-AZ / Single-AZ Pilot (db.t4g.medium) ]
```

---

## 2. Infrastructure Provisioning Checklist (Owner Approval Required)

> [!IMPORTANT]
> In accordance with non-negotiable rules, do **NOT** provision paid AWS resources without explicit written authorization from the owner.

### 2.1 EC2 Instance Sizing
- **Instance Type:** `t4g.xlarge` (4 vCPUs, 16 GB RAM, ARM64 Graviton3) or `t3.xlarge` (x86_64).
- **Storage:** 100 GB gp3 root volume with KMS encryption (`aws/ebs`).
- **Operating System:** Amazon Linux 2023 or Ubuntu 24.04 LTS.

### 2.2 Security Group Rules
- **Inbound Rules:**
  - `HTTP (80)`: `0.0.0.0/0` (Redirects to HTTPS).
  - `HTTPS (443)`: `0.0.0.0/0` (TLS termination).
  - `SSH (22)`: **PROHIBITED**. No public port 22 open. Operator shell access is strictly brokered through AWS SSM Session Manager.
- **Outbound Rules:**
  - `HTTPS (443)`: External AI APIs (OpenAI, Anthropic, Gemini, Grok, OpenRouter) and S3 endpoints.
  - `PostgreSQL (5432)`: Target RDS security group only.

### 2.3 S3 Buckets & Access Control
- `gayatri-cloud-pilot-storage`: Course assets, syllabus PDFs, and user exports.
  - **S3 Block Public Access:** Enabled for all 4 settings (Total private isolation).
  - **Server-Side Encryption:** SSE-S3 or AWS KMS (`aws/s3`).
- `gayatri-cloud-pilot-archive`: Telemetry event outbox dumps and training candidates.
  - **Object Lock:** Compliance mode with 30-day immutability.

---

## 3. Host Initialization & Container Engine Setup

Connect to the instance using AWS SSM Session Manager:
```bash
aws ssm start-session --target i-0123456789abcdef0 --region ap-south-1
```

Install Docker and Docker Compose plugin:
```bash
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ssm-user

# Install Docker Compose Plugin
DOCKER_CONFIG=${DOCKER_CONFIG:-/usr/local/lib/docker}
sudo mkdir -p $DOCKER_CONFIG/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-aarch64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
sudo chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
```

---

## 4. Secret Configuration via AWS Secrets Manager

Retrieve secrets securely into `/opt/gayatri/.env.production` (never checked into version control):

```bash
sudo mkdir -p /opt/gayatri
cd /opt/gayatri

# Retrieve production secrets from AWS Secrets Manager
aws secretsmanager get-secret-value \
    --secret-id gayatri/pilot/production \
    --query SecretString \
    --output text > .env.production

sudo chmod 600 .env.production
```

---

## 5. Deployment and Migration Execution

### 5.1 Clone Repository and Prepare Build
```bash
git clone https://github.com/Gayatri-Education/Gayatri-Cloud.git /opt/gayatri/app
cd /opt/gayatri/app
git checkout main
```

### 5.2 Execute Database Migrations
Run Alembic schema migrations prior to container rotation:
```bash
docker run --rm \
    --env-file /opt/gayatri/.env.production \
    -v $(pwd)/backend:/app \
    python:3.12-slim \
    bash -c "pip install -r /app/requirements.txt && cd /app && alembic upgrade head"
```

### 5.3 Launch Production Stack
```bash
docker compose -f docker-compose.prod.yml --env-file /opt/gayatri/.env.production up -d --build
```

### 5.4 Verification Smoke Test
```bash
# Verify backend readiness probe
curl -f http://localhost:8000/health/ready

# Verify proxy health
curl -f http://localhost/healthz

# Verify Prometheus metrics exposition
curl -f http://localhost:8000/api/v1/observability/metrics/prometheus
```

---

## 6. Zero-Downtime Rollback Procedure

If a deployment defect is identified in production:

1. **Rollback Container Images:**
   ```bash
   cd /opt/gayatri/app
   git checkout <PREVIOUS_STABLE_COMMIT_SHA>
   docker compose -f docker-compose.prod.yml --env-file /opt/gayatri/.env.production up -d --build
   ```

2. **Rollback Database Migration (if applicable):**
   ```bash
   docker run --rm \
       --env-file /opt/gayatri/.env.production \
       -v $(pwd)/backend:/app \
       python:3.12-slim \
       bash -c "cd /app && alembic downgrade -1"
   ```

3. **Verify Restored Health:**
   ```bash
   curl -f http://localhost:8000/health/ready
   ```

---

## 7. Automated Backups & Disaster Recovery Drill

### 7.1 Daily Point-in-Time Backup Automation
Configure systemd timer `/etc/systemd/system/gayatri-backup.service`:
```ini
[Unit]
Description=Gayatri Cloud Automated Daily Backup

[Service]
Type=oneshot
ExecStart=/opt/gayatri/app/scripts/backup_snapshot.sh
```

### 7.2 Point-in-Time Disaster Recovery Runbook
In case of catastrophic database or storage loss:

1. Identify latest verified snapshot manifest in `s3://gayatri-cloud-pilot-archive/snapshots/`.
2. Verify SHA-256 manifest checksum matches the cryptographic signature recorded in logs.
3. Provision fresh PostgreSQL staging instance.
4. Restore SQL dump:
   ```bash
   pg_restore --clean --if-exists -h $TARGET_HOST -U $TARGET_USER -d $TARGET_DB snapshot_dump.sql
   ```
5. Execute deep health diagnostic probe:
   ```bash
   python backend/scripts/release_verification.py --verify-db
   ```
6. Divergence check: Ensure zero row-count divergence between snapshot manifest and restored tables.

---

## 8. Incident Response & Emergency Procedures

- **Provider Outage:** Use Admin Observability portal (`/admin/observability`) or trigger API circuit trip:
  ```bash
  curl -X POST http://localhost:8000/api/v1/observability/circuit-breakers/openai/trip \
       -H "Authorization: Bearer $SUPERADMIN_TOKEN" \
       -d '{"reason": "Provider 500 error spike"}'
  ```
- **Security Incident / Compromise:** Revoke JWT signing key in Secrets Manager and restart backend containers to invalidate all active refresh and access tokens immediately.
