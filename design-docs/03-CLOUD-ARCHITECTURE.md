# Production Cloud Architecture
## Jira-Like Project Management Application — AWS

**Version**: 1.0  
**Date**: February 21, 2026  
**Author**: Architecture Team  
**Cloud Provider**: Amazon Web Services (AWS)  
**Target Regions**: us-east-1 (Primary), us-west-2 (DR)

---

## 1. Architecture Overview

The production environment is a **multi-AZ, auto-scaling cloud-native deployment** on AWS using managed services wherever possible to minimise operational overhead.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                           │
└──────────────────────────────────┬─────────────────────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │       Route 53 (DNS)         │
                    │   yourdomain.com             │
                    │   api.yourdomain.com         │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼─────────────────────┐
              │                    │                      │
   ┌──────────▼──────────┐         │            ┌────────▼────────────┐
   │  CloudFront CDN     │         │            │  AWS WAF             │
   │  (Static Assets)    │         │            │  (Web App Firewall)  │
   │  S3 origin          │         │            └────────┬────────────┘
   │  yourdomain.com     │         │                     │
   └─────────────────────┘         │            ┌────────▼────────────┐
                                   │            │  ALB                 │
                                   │            │  (App Load Balancer) │
                                   │            └────────┬────────────┘
                                   │                     │
┌──────────────────────────────────┼─────────────────────┼────────────────────────┐
│  VPC  10.0.0.0/16                │                     │                        │
│                                  │                     │                        │
│  ┌──────────────────────────┐    │    ┌────────────────▼──────────────────────┐ │
│  │  Public Subnets           │    │    │  Private Subnets (App Tier)           │ │
│  │  10.0.1.0/24 (AZ-a)      │    │    │  10.0.10.0/24 (AZ-a)                 │ │
│  │  10.0.2.0/24 (AZ-b)      │    │    │  10.0.11.0/24 (AZ-b)                 │ │
│  │                           │    │    │                                        │ │
│  │  ┌─────────────────────┐ │    │    │  ┌──────────────────────────────────┐ │ │
│  │  │  NAT Gateway (AZ-a) │ │    │    │  │  ECS Fargate Cluster             │ │ │
│  │  └─────────────────────┘ │    │    │  │                                  │ │ │
│  │  ┌─────────────────────┐ │    │    │  │  ┌────────────┐ ┌────────────┐  │ │ │
│  │  │  NAT Gateway (AZ-b) │ │    │    │  │  │  API Task  │ │  API Task  │  │ │ │
│  │  └─────────────────────┘ │    │    │  │  │  (AZ-a)    │ │  (AZ-b)    │  │ │ │
│  └──────────────────────────┘    │    │  │  │  NestJS    │ │  NestJS    │  │ │ │
│                                  │    │  │  │  1vCPU     │ │  1vCPU     │  │ │ │
│                                  │    │  │  │  2GB RAM   │ │  2GB RAM   │  │ │ │
│                                  │    │  │  └────────────┘ └────────────┘  │ │ │
│                                  │    │  │                                  │ │ │
│                                  │    │  │  Auto Scaling: 2 min, 10 max    │ │ │
│                                  │    │  │  Scale-out: CPU > 70% (5m avg)  │ │ │
│                                  │    │  │  Scale-in:  CPU < 30% (15m avg) │ │ │
│                                  │    │  └──────────────────────────────────┘ │ │
│                                  │    └────────────────────────────────────────┘ │
│                                  │                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │  Private Subnets (Data Tier)                                                │  │
│  │  10.0.20.0/24 (AZ-a)   10.0.21.0/24 (AZ-b)                                │  │
│  │                                                                             │  │
│  │  ┌──────────────────────────┐     ┌──────────────────────────────────────┐ │  │
│  │  │  RDS PostgreSQL 15        │     │  ElastiCache Redis 7                 │ │  │
│  │  │                           │     │                                      │ │  │
│  │  │  Primary (AZ-a)           │     │  Primary (AZ-a)                      │ │  │
│  │  │  db.r6g.large             │     │  cache.r6g.large                     │ │  │
│  │  │  ↕ synchronous replictn   │     │  ↕ async replication                 │ │  │
│  │  │  Read Replica (AZ-b)      │     │  Replica (AZ-b)                      │ │  │
│  │  │  db.r6g.large             │     │                                      │ │  │
│  │  │                           │     │  Cluster Mode: Enabled               │ │  │
│  │  │  Storage: 100GB gp3       │     │  Encryption: At-rest + in-transit    │ │  │
│  │  │  IOPS: 3000               │     │                                      │ │  │
│  │  │  Encrypted: KMS           │     │  cache.r6g.large: 13.07 GB RAM       │ │  │
│  │  │  Backup: 7-day retention  │     └──────────────────────────────────────┘ │  │
│  │  └──────────────────────────┘                                               │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘

External AWS Services (outside VPC):
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐
│   AWS S3    │  │   AWS SES   │  │  CloudWatch │  │   AWS SQS   │  │ AWS SecretsManager│
│(Attachments)│  │   (Email)   │  │(Logs+Metrics│  │  (DLQ)      │  │  (Credentials)    │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────────┘
```

---

## 2. AWS Services Inventory

### 2.1 Compute
| Service | Configuration | Purpose |
|---------|--------------|---------|
| **ECS Fargate** | 1 vCPU / 2GB RAM per task | Run NestJS API containers |
| **ECR** | Private registry | Store Docker images |
| **Auto Scaling** | Min 2, Max 10 tasks | Scale API tier |

### 2.2 Networking
| Service | Configuration | Purpose |
|---------|--------------|---------|
| **VPC** | 10.0.0.0/16, 3-tier subnet design | Network isolation |
| **ALB** | HTTPS listener (ACM cert), HTTP → HTTPS redirect | Load balance API traffic |
| **CloudFront** | S3 origin, HTTPS, React SPA assets | CDN for static frontend |
| **Route 53** | A-records, health checks | DNS + failover routing |
| **WAF** | OWASP Top 10 rules, rate limiting | Edge security |
| **NAT Gateway** | One per AZ | Outbound internet for private subnets |

### 2.3 Data
| Service | Configuration | Purpose |
|---------|--------------|---------|
| **RDS PostgreSQL 15** | db.r6g.large, Multi-AZ, encrypted | Primary database |
| **RDS Read Replica** | db.r6g.large, cross-AZ | Read-scaling for reports |
| **ElastiCache Redis 7** | cache.r6g.large, cluster mode, Multi-AZ | Caching + sessions |
| **S3** | Versioned, encrypted (SSE-S3) | File attachments, frontend assets |

### 2.4 Security
| Service | Configuration | Purpose |
|---------|--------------|---------|
| **ACM** | Wildcard cert `*.yourdomain.com` | TLS termination at ALB |
| **KMS** | Customer-managed key | RDS encryption |
| **Secrets Manager** | Auto-rotation 30 days | DB credentials, JWT secrets |
| **IAM** | Least-privilege task roles | ECS task permissions |
| **Security Groups** | Layered inbound rules | Network-level access control |
| **AWS WAF** | Managed rule groups | Web layer protection |

### 2.5 Observability
| Service | Configuration | Purpose |
|---------|--------------|---------|
| **CloudWatch Logs** | 90-day retention | Application logs |
| **CloudWatch Metrics** | Custom + built-in | Resource utilisation |
| **CloudWatch Alarms** | SNS alerts | Threshold breaches |
| **CloudWatch Dashboard** | API latency, error rate, DB connections | Operational visibility |
| **AWS X-Ray** | Sampling 5% | Distributed tracing |

### 2.6 Delivery
| Service | Configuration | Purpose |
|---------|--------------|---------|
| **GitHub Actions** | Push-to-deploy pipeline | CI/CD |
| **ECR** | Image scanning on push | Container vulnerability detection |
| **CodeDeploy** | Rolling update strategy ECS | Zero-downtime deployments |

### 2.7 Messaging
| Service | Configuration | Purpose |
|---------|--------------|---------|
| **SQS** | Standard queue, DLQ | Async notification processing |
| **SES** | Verified domain, DKIM | Transactional email |
| **SNS** | Alert topics | Ops alerting |

---

## 3. Security Group Rules

### 3.1 ALB Security Group
```
Inbound:  443 (HTTPS) from 0.0.0.0/0
          80 (HTTP)   from 0.0.0.0/0  ← redirects to 443
Outbound: All to ECS SG
```

### 3.2 ECS Task Security Group
```
Inbound:  3000 (NestJS) from ALB SG only
Outbound: 5432 (Postgres) to RDS SG
          6379 (Redis)    to ElastiCache SG
          443             to 0.0.0.0/0  (S3, SES, Secrets Manager via endpoints)
```

### 3.3 RDS Security Group
```
Inbound:  5432 from ECS SG only
Outbound: None
```

### 3.4 ElastiCache Security Group
```
Inbound:  6379 from ECS SG only
Outbound: None
```

---

## 4. CI/CD Pipeline

```
Developer Push to main
         │
         ▼
┌─────────────────┐
│  GitHub Actions  │
│                 │
│ 1. Lint + Test  │
│ 2. Docker Build │
│ 3. Push to ECR  │
│ 4. ECS Deploy   │
│    (Rolling)    │
└────────┬────────┘
         │
         ▼
  ECS Rolling Update
  (new task starts → health check passes → old task drains → terminates)
         │
         ▼
  CloudWatch alarm monitors
  error rate post-deploy
  (auto-rollback trigger)
```

### 4.1 Pipeline Stages
| Stage | Tool | Action |
|-------|------|--------|
| Code Quality | ESLint + Prettier | Fail on lint errors |
| Unit Tests | Jest | Fail on test failures, coverage < 70% |
| Integration Tests | Jest + testcontainers | Spin up Postgres + Redis |
| Build | Docker Buildx | Multi-stage build, minimal image |
| Scan | ECR Image Scan | Block on CRITICAL CVE |
| Deploy Staging | GitHub Actions + ECS | Push on `develop` branch |
| Deploy Production | GitHub Actions + ECS | Push on `main` branch (manual approval) |
| Smoke Test | Playwright | 5 key user flows post-deploy |

---

## 5. Environment Strategy

| Environment | Infrastructure | Branch | Auto-deploy |
|-------------|--------------|--------|-------------|
| **Development** | Docker Compose (local) | feature/* | No |
| **Staging** | ECS (single AZ, smaller instances) | develop | Yes |
| **Production** | ECS (Multi-AZ, full spec) | main | Manual approval |

### 5.1 Environment Variables (via Secrets Manager)
```
DATABASE_URL        → Injected at ECS task start from Secrets Manager
REDIS_URL           → Injected at ECS task start
JWT_SECRET          → Rotated every 30 days
JWT_REFRESH_SECRET  → Rotated every 30 days
AWS_REGION          → Built-in ECS metadata
S3_BUCKET           → Task Definition env var (non-secret)
SES_FROM_EMAIL      → Task Definition env var (non-secret)
```

---

## 6. Disaster Recovery

| Scenario | Recovery Mechanism | RTO | RPO |
|----------|--------------------|-----|-----|
| ECS Task failure | Auto-replacement by ECS | < 60s | 0 |
| AZ failure | Multi-AZ auto-failover (RDS + ECS) | < 5 min | 0 |
| RDS instance failure | Multi-AZ standby promotion | < 30s | 0 |
| Region failure | Manual Route 53 failover to us-west-2 | < 1 hr | 24 hr |
| Accidental data deletion | RDS point-in-time restore | < 30 min | 5 min |
| S3 data loss | S3 versioning restore | < 15 min | 0 |

---

## 7. Cost Estimation (Production — Monthly)

| Service | Configuration | Est. Monthly Cost (USD) |
|---------|--------------|-------------------------|
| ECS Fargate | 2 tasks × 1vCPU × 2GB | ~$60 |
| RDS db.r6g.large Multi-AZ | 100GB storage | ~$320 |
| ElastiCache cache.r6g.large | Multi-AZ | ~$180 |
| ALB | ~1M requests/mo | ~$20 |
| CloudFront | ~10GB transfer | ~$5 |
| S3 | 50GB storage + requests | ~$5 |
| NAT Gateway | 2 × ~10GB | ~$40 |
| Route 53 | Hosted zone + queries | ~$5 |
| CloudWatch | Logs + metrics | ~$20 |
| SES | 10,000 emails/mo | ~$1 |
| Secrets Manager | 5 secrets + rotations | ~$5 |
| **Total Estimate** | | **~$661/month** |

> Staging environment: ~$150/month (single AZ, smaller instances)

---

## 8. Scaling Targets

| Metric | Phase 1 Target | Phase 3 Target |
|--------|---------------|----------------|
| Concurrent Users | 500 | 5,000 |
| API Requests/sec | 100 | 1,000 |
| DB Connections | 50 | 200 |
| ECS Tasks | 2–4 | 5–10 |
| RDS Instance | db.r6g.large | db.r6g.xlarge |
| Redis | cache.r6g.large | cache.r6g.xlarge |
