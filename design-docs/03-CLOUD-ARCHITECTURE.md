# Production Cloud Architecture
## Jira-Like Project Management Application

**Version**: 2.0 | **Date**: February 21, 2026 | **Status**: Approved

> Backend container: **Python 3.12 / FastAPI** on ECS Fargate.  
> CI/CD pipeline: **Poetry** (dependency management), **pytest** (tests), **Docker** (python:3.12-slim image).

---

## 1. AWS Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                              AWS CLOUD                                         │
│                                                                                │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                       us-east-1 (Primary Region)                        │  │
│  │                                                                          │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐   │  │
│  │  │                          VPC (10.0.0.0/16)                       │   │  │
│  │  │                                                                  │   │  │
│  │  │  ┌─────────────────────────────────────────────────────────┐    │   │  │
│  │  │  │                   Public Subnets                        │    │   │  │
│  │  │  │  ┌────────────────────────┐  ┌────────────────────────┐ │    │   │  │
│  │  │  │  │  10.0.1.0/24 (AZ-1a)  │  │  10.0.2.0/24 (AZ-1b)  │ │    │   │  │
│  │  │  │  │  - ALB nodes           │  │  - ALB nodes           │ │    │   │  │
│  │  │  │  │  - NAT Gateway         │  │  - NAT Gateway         │ │    │   │  │
│  │  │  │  └────────────────────────┘  └────────────────────────┘ │    │   │  │
│  │  │  └─────────────────────────────────────────────────────────┘    │   │  │
│  │  │                                                                  │   │  │
│  │  │  ┌─────────────────────────────────────────────────────────┐    │   │  │
│  │  │  │                   Private Subnets                       │    │   │  │
│  │  │  │  ┌────────────────────────┐  ┌────────────────────────┐ │    │   │  │
│  │  │  │  │ 10.0.10.0/24 (AZ-1a)  │  │ 10.0.11.0/24 (AZ-1b)  │ │    │   │  │
│  │  │  │  │                        │  │                        │ │    │   │  │
│  │  │  │  │  ECS Fargate Tasks     │  │  ECS Fargate Tasks     │ │    │   │  │
│  │  │  │  │ ┌──────────────────┐   │  │ ┌──────────────────┐  │ │    │   │  │
│  │  │  │  │ │  FastAPI API     │   │  │ │  FastAPI API     │  │ │    │   │  │
│  │  │  │  │ │  (Python 3.12)   │   │  │ │  (Python 3.12)   │  │ │    │   │  │
│  │  │  │  │ │  Uvicorn ASGI    │   │  │ │  Uvicorn ASGI    │  │ │    │   │  │
│  │  │  │  │ │  Port: 8000      │   │  │ │  Port: 8000      │  │ │    │   │  │
│  │  │  │  │ │  CPU: 512        │   │  │ │  CPU: 512        │  │ │    │   │  │
│  │  │  │  │ │  Memory: 1024MB  │   │  │ │  Memory: 1024MB  │  │ │    │   │  │
│  │  │  │  │ └──────────────────┘   │  │ └──────────────────┘  │ │    │   │  │
│  │  │  │  └────────────────────────┘  └────────────────────────┘ │    │   │  │
│  │  │  └─────────────────────────────────────────────────────────┘    │   │  │
│  │  │                                                                  │   │  │
│  │  │  ┌─────────────────────────────────────────────────────────┐    │   │  │
│  │  │  │                   Data Subnets                          │    │   │  │
│  │  │  │  ┌────────────────────────┐  ┌────────────────────────┐ │    │   │  │
│  │  │  │  │ 10.0.20.0/24 (AZ-1a)  │  │ 10.0.21.0/24 (AZ-1b)  │ │    │   │  │
│  │  │  │  │  RDS Primary           │  │  RDS Standby (Multi-AZ)│ │    │   │  │
│  │  │  │  │  PostgreSQL 15         │  │  ElastiCache Redis      │ │    │   │  │
│  │  │  │  └────────────────────────┘  └────────────────────────┘ │    │   │  │
│  │  │  └─────────────────────────────────────────────────────────┘    │   │  │
│  │  └──────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                          │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │  │                  Global / Edge Resources                          │  │  │
│  │  │  CloudFront (SPA + API Cache)  │  S3 (Frontend + Attachments)    │  │  │
│  │  │  Route 53 (DNS)                │  ACM (SSL/TLS wildcard cert)    │  │  │
│  │  │  WAF (Web Application Firewall)│  SES (Email)                    │  │  │
│  │  │  Secrets Manager               │  ECR (Container Registry)       │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │               us-west-2 (DR Region — Active-Passive)                    │  │
│  │  RDS Read Replica (cross-region)  │  S3 Cross-Region Replication        │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Service Configuration

### 2.1 ECS Fargate — FastAPI Application
| Parameter | Phase 1 | Phase 3+ |
|-----------|---------|---------|
| Task CPU | 512 (0.5 vCPU) | 1024 (1 vCPU) |
| Task Memory | 1024 MB | 2048 MB |
| Desired Count | 2 | 4 |
| Min Scaling | 2 | 2 |
| Max Scaling | 8 | 20 |
| Container Image | `python:3.12-slim` (ECR) | same |
| Command | `gunicorn -k uvicorn.workers.UvicornWorker -w 4 app.main:app` | same |
| Port | 8000 | 8000 |
| Health Check | `GET /health` | same |

**Environment Variables** (stored in AWS Secrets Manager, injected at task launch):
```
DATABASE_URL=postgresql+asyncpg://user:pass@rds-host:5432/dbname
REDIS_URL=redis://elasticache-host:6379
JWT_SECRET=<256-bit secret from Secrets Manager>
AWS_S3_BUCKET=jira-app-attachments
AWS_SES_FROM_EMAIL=noreply@yourdomain.com
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 2.2 ECS Fargate — Alembic Migration Task (One-shot)
Run as a separate ECS task on each deployment before rolling ECS service update:
```
Command: alembic upgrade head
```

### 2.3 AWS RDS — PostgreSQL 15
| Parameter | Phase 1 | Phase 3+ |
|-----------|---------|---------|
| Instance Class | `db.t4g.medium` | `db.r7g.large` |
| Storage | 100 GB gp3 | 500 GB gp3 |
| Multi-AZ | Yes | Yes |
| Read Replicas | 0 | 1 (same region) |
| Backup Retention | 30 days | 30 days |
| Parameter Group | Tuned for connection pooling | same |

### 2.4 AWS ElastiCache — Redis 7
| Parameter | Value |
|-----------|-------|
| Engine | Redis 7.x |
| Node Type | `cache.t4g.small` |
| Cluster Mode | Disabled (single shard) |
| Multi-AZ with Failover | Enabled |
| Auth Token | Enabled (stored in Secrets Manager) |

### 2.5 AWS CloudFront + S3 (Frontend SPA)
| Parameter | Value |
|-----------|-------|
| Origin | S3 bucket (OAC policy) |
| Price Class | PriceClass_100 (US, EU) |
| Cache Behavior | `/` → SPA (24h TTL); `/api/*` → no cache (forward to ALB) |
| WAF | OWASP Top 10 managed rule set |
| Custom Error | 403/404 → `/index.html` (SPA routing) |

---

## 3. Security Groups

| SG Name | Inbound Rules | Outbound |
|---------|--------------|----------|
| `sg-alb` | 443 from 0.0.0.0/0, 80 from 0.0.0.0/0 | All to `sg-api` |
| `sg-api` | 8000 from `sg-alb` only | All to `sg-rds`, `sg-redis`, HTTPS to S3/SES/ECR |
| `sg-rds` | 5432 from `sg-api` only | None |
| `sg-redis` | 6379 from `sg-api` only | None |

---

## 4. CI/CD Pipeline (GitHub Actions)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GitHub Actions — CI/CD Pipeline                      │
│                                                                             │
│  Trigger: Push to main branch                                               │
│                                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │  Stage 1   │  │  Stage 2   │  │  Stage 3   │  │  Stage 4   │          │
│  │   Lint &   │→ │   Test     │→ │   Build &  │→ │  Deploy    │          │
│  │  Format    │  │            │  │   Push     │  │            │          │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘          │
│                                                                             │
│  Stage 1 — Lint & Format (Backend + Frontend)                              │
│  Backend:                                                                   │
│    - poetry run ruff check app/                                             │
│    - poetry run ruff format --check app/                                    │
│    - poetry run mypy app/                                                   │
│  Frontend:                                                                  │
│    - npm run lint (ESLint + TypeScript compile check)                       │
│                                                                             │
│  Stage 2 — Test (Backend + Frontend)                                       │
│  Backend:                                                                   │
│    - poetry install --no-dev (ci cache)                                     │
│    - docker run postgres:15 (testcontainer via pytest-docker)               │
│    - poetry run pytest --cov=app --cov-report=xml -q                        │
│    - coverage gate: must be ≥ 70%                                           │
│  Frontend:                                                                  │
│    - npm ci                                                                 │
│    - npm run test:coverage (Vitest)                                         │
│                                                                             │
│  Stage 3 — Build & Push to ECR                                             │
│    - docker build -t jira-api:${{ github.sha }}                             │
│      (FROM python:3.12-slim, poetry install --only main)                    │
│    - docker push $ECR_REGISTRY/jira-api:$SHA                               │
│    - aws s3 sync frontend/dist/ s3://jira-frontend/ (SPA)                  │
│    - aws cloudfront create-invalidation --paths "/*"                        │
│                                                                             │
│  Stage 4 — Deploy to ECS                                                   │
│    - Run migration task: alembic upgrade head                               │
│    - aws ecs update-service --force-new-deployment                          │
│    - Wait for ECS rolling deployment to complete                            │
│    - Health check: GET https://api.yourdomain.com/health                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Dockerfile (Backend)
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --without-hashes -o requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
EXPOSE 8000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", \
     "--bind", "0.0.0.0:8000", "--timeout", "60", "app.main:app"]
```

---

## 5. Monitoring & Alerting

| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| API Error Rate (5xx) | > 1% of requests | PagerDuty P2 |
| API P95 Latency | > 500ms | PagerDuty P3 |
| API P99 Latency | > 2000ms | PagerDuty P2 |
| ECS CPU | > 80% for 5min | Auto-scale out |
| ECS Memory | > 85% | PagerDuty P2 |
| RDS CPU | > 70% for 5min | PagerDuty P2 |
| RDS Connections | > 80% of max | PagerDuty P1 |
| Redis Memory | > 80% | PagerDuty P2 |
| Failed Deployments | Any failure | PagerDuty P1 + Slack |
| pytest Coverage Drop | < 70% | Block PR merge |

### 5.1 ECS Custom Metrics (via structlog + CloudWatch Logs Metric Filter)
Python FastAPI app emits structured JSON logs; CloudWatch Metric Filters extract:
- `request_duration_ms` — P50, P95, P99 per endpoint
- `db_query_duration_ms` — slow query detection
- `cache_hit_rate` — board state / user profile caches

---

## 6. Disaster Recovery

| Scenario | RTO | RPO | Recovery Action |
|----------|-----|-----|-----------------|
| ECS task crash | < 1 min | 0 | ECS auto-restarts task; ALB health check fails old |
| AZ failure | < 5 min | 0 | ALB routes to healthy AZ; ECS tasks in other AZ |
| RDS failover | < 2 min | 0 | Multi-AZ automatic promotion |
| Region failure | < 1 hr | 24 hr | Promote RDS cross-region replica; update Route 53 |
| Data corruption | < 2 hr | 24 hr | Restore from most recent RDS automated snapshot |

---

## 7. Cost Estimate (Phase 1 — us-east-1)

| Service | Config | Est. Monthly |
|---------|--------|-------------|
| ECS Fargate (API) | 2 tasks × 0.5 vCPU × 1GB, 730h | ~$35 |
| RDS PostgreSQL | db.t4g.medium, Multi-AZ, 100GB gp3 | ~$110 |
| ElastiCache Redis | cache.t4g.small, Multi-AZ | ~$30 |
| ALB | 2 LCUs average | ~$20 |
| CloudFront + S3 | 5 GB transfer | ~$5 |
| ECR | 2 images stored | ~$1 |
| Route 53 | 1 hosted zone | ~$1 |
| Secrets Manager | 5 secrets | ~$2 |
| AWS SES | < 10,000 emails | ~$1 |
| CloudWatch | Metrics + Logs | ~$10 |
| **TOTAL** | | **~$215/month** |

---

## 8. IAM Roles

### 8.1 ECS Task Role (`jira-api-task-role`)
```json
{
  "permissions": [
    "s3:PutObject", "s3:GetObject", "s3:DeleteObject",
    "ses:SendEmail",
    "secretsmanager:GetSecretValue",
    "xray:PutTraceSegments",
    "cloudwatch:PutMetricData",
    "logs:CreateLogStream", "logs:PutLogEvents"
  ]
}
```

### 8.2 GitHub Actions Role (`jira-cicd-role`)
```json
{
  "permissions": [
    "ecr:GetAuthorizationToken", "ecr:BatchCheckLayerAvailability",
    "ecr:PutImage", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart", "ecr:CompleteLayerUpload",
    "ecs:RegisterTaskDefinition", "ecs:UpdateService", "ecs:DescribeServices",
    "ecs:RunTask", "ecs:StopTask",
    "s3:PutObject", "s3:ListBucket",
    "cloudfront:CreateInvalidation",
    "iam:PassRole"
  ]
}
```
