# Gayatri Cloud — Owner Pre-Flight Release Checklist

**Target Release:** Gayatri Cloud Pilot v1.0.0  
**Date:** 2026-10-24  
**Classification:** Confidential / Owner Authorization  

---

## 1. Technical Release Gates Verification

| Verification Item | Requirement | Verification Evidence | Status |
|---|---|---|---|
| **Automated Tests** | 100% passing across backend and frontend | 125 backend pytest + 67 frontend vitest passed | `PASS` |
| **Linters & Formatters** | 0 warnings, strict formatting | `ruff check` (0 errors), `next lint` (0 warnings) | `PASS` |
| **Production Build** | Clean Next.js 14 standalone build | 31/31 routes compiled statically/dynamically | `PASS` |
| **Docker Specifications** | Unprivileged non-root users, health probes | `backend/Dockerfile` (UID 10001), `frontend/Dockerfile` (UID 1001) | `PASS` |
| **Tenant Boundaries** | 403 Forbidden on cross-tenant requests | Negative isolation tests verified in P04, P15, P20 | `PASS` |
| **Role Incompatibilities** | Student and Teacher dual-role prohibited | RQ-003 invariant verified across workflows | `PASS` |
| **Security Headers** | OWASP recommended defensive headers | CSP, HSTS, X-Frame-Options, X-Content-Type-Options | `PASS` |
| **SSRF Perimeter Defense** | Cloud metadata (169.254.169.254) blocked | `backend/app/domain/security/ssrf_guard.py` | `PASS` |
| **Statutory Accounting Hold** | Invoices & fee records preserved upon deletion | GDPR Art. 20 export & pseudonymization verified | `PASS` |
| **Localization & Offline** | 8 languages + offline reader with SHA-256 | `TranslationRegistry`, `OfflineStorage` verified | `PASS` |

---

## 2. Infrastructure Sizing & Estimated AWS Cloud Costs

| Resource | Pilot Specification | Monthly Est. (USD) | Owner Disposition |
|---|---|---:|---|
| **Compute (EC2)** | 1x `t4g.xlarge` (4 vCPU, 16 GB RAM, 100 GB gp3) | ~$98.00 | `RECOMMENDED_PENDING_APPROVAL` |
| **Database (RDS)** | PostgreSQL 16 `db.t4g.medium` (Single-AZ Pilot, 50 GB) | ~$52.00 | `RECOMMENDED_PENDING_APPROVAL` |
| **Object Storage (S3)** | S3 Standard (Storage + Telemetry Archives) | ~$10.00 | `RECOMMENDED_PENDING_APPROVAL` |
| **Network & Egress** | AWS NAT Gateway / Data Transfer (Pilot Scale) | ~$35.00 | `RECOMMENDED_PENDING_APPROVAL` |
| **Total Estimated Pilot Cost** | Single-Instance Architecture | **~$195.00 / mo** | Needs Owner Authorization |

---

## 3. Policy & Governance Sign-Off Items

1. **Training Data Governance (DEC-011):**
   - *Policy:* All student interactions remain private; training dataset generation is strictly deny-by-default and requires explicit institutional consent and anonymization.
   - *Disposition:* Confirmed and implemented.

2. **Database Provisioning (DEC-005):**
   - *Policy:* PostgreSQL RDS is recommended for transactional reliability with S3 for file archives.
   - *Disposition:* Awaiting owner live provisioning approval.

3. **Domain & DNS Pointing:**
   - *Policy:* Route53 / Cloudflare DNS pointing to EC2 Elastic IP.
   - *Disposition:* Pending owner domain assignment.

4. **Payment Gateway Credentials:**
   - *Policy:* Live Stripe / Razorpay API keys must be provisioned by owner into AWS Secrets Manager.
   - *Disposition:* Mock gateway adapter verified for local tests; live keys pending.

---

## 4. Final Sign-Off Status

- **Local Technical State:** `GREEN` (All 21 phases implemented, tested, verified).
- **Public Cloud Launch State:** `AWAITING_OWNER` (Awaiting live AWS resource provisioning authorization).
