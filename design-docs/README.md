# Design Documentation — Jira-Like App

**Project**: Jira-Like Project Management Application  
**Stack**: RAPP (React · AWS · PostgreSQL · Python/FastAPI)  
**Version**: 2.0 | **Date**: February 21, 2026

> **Stack**: Frontend → React 18 + TypeScript; Backend → FastAPI (Python 3.12); Database → PostgreSQL 15; Cloud → AWS.

---

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 01 | [High-Level Design](./01-HIGH-LEVEL-DESIGN.md) | System context, major components, delivery phases, design principles |
| 02 | [System Architecture](./02-SYSTEM-ARCHITECTURE.md) | Component architecture, API contracts, real-time design, security, caching |
| 03 | [Production Cloud Architecture](./03-CLOUD-ARCHITECTURE.md) | AWS infrastructure, security groups, CI/CD pipeline, DR strategy, cost estimate |
| 04 | [Low-Level Design](./04-LOW-LEVEL-DESIGN.md) | SQLAlchemy schema, DB indexes, FastAPI router internals, Pydantic schemas, Redis key design |
| 05 | [Phase 1 Mermaid Diagrams](./05-PHASE1-MERMAID-DIAGRAMS.md) | 12 Mermaid diagrams covering all key flows for MVP delivery |
| 06 | [API Contract — MVP1.0](./06-API-CONTRACT.md) | Complete REST API contract for MVP1.0 — auth, projects, tickets. Single source of truth for backend and frontend. |

---

## Architecture at a Glance

```
Users (Browser)
      │ HTTPS / WSS
      ▼
CloudFront + ALB (AWS)
      │
      ▼
FastAPI (Python 3.12 on ECS Fargate, Multi-AZ, Auto-scaling)
      │
  ┌───┼───────────┐
  │   │           │
  ▼   ▼           ▼
PostgreSQL  Redis    S3
(RDS)    (ElastiCache) (Attachments)
```

---

## Technology Stack Summary

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Vite |
| Frontend State | Redux Toolkit + React Query (TanStack) |
| Frontend UI | TailwindCSS + shadcn/ui |
| Backend | FastAPI (Python 3.12) |
| Backend ORM | SQLAlchemy 2.0 (async) + Alembic |
| Schema Validation | Pydantic v2 |
| Authentication | python-jose (JWT) + passlib/bcrypt |
| Real-time | FastAPI WebSockets + python-socketio |
| Primary Database | PostgreSQL 15 (AWS RDS) |
| Cache | Redis 7 (AWS ElastiCache) |
| File Storage | AWS S3 |
| Email | AWS SES |
| Container | Docker (python:3.12-slim) |
| Orchestration | AWS ECS Fargate |
| CI/CD | GitHub Actions |
| Backend Testing | pytest + httpx + pytest-asyncio |
| Frontend Testing | Vitest + React Testing Library + Playwright |

---

## Phase 1 Mermaid Diagrams Summary

| # | Diagram | Type |
|---|---------|------|
| 1 | System Context (C4) | C4Context |
| 2 | Container Diagram (C4) | C4Container |
| 3 | Authentication Flow | Sequence |
| 4 | Ticket Creation Flow | Sequence |
| 5 | Sprint Board Drag-and-Drop | Sequence |
| 6 | Sprint Lifecycle State Machine | State |
| 7 | Entity Relationship Diagram | ER |
| 8 | Frontend Application Flow | Flowchart |
| 9 | CI/CD Pipeline | Flowchart |
| 10 | RBAC Permission Flow | Flowchart |
| 11 | DB Migration & Seeding | Flowchart |
| 12 | Phase 1 Sprint Timeline | Gantt |
