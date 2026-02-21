# Design Documentation — Jira-Like App

**Project**: Jira-Like Project Management Application  
**Stack**: MARN (MongoDB-style via PostgreSQL · AWS · React · NestJS)  
**Version**: 1.0 | **Date**: February 21, 2026

---

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 01 | [High-Level Design](./01-HIGH-LEVEL-DESIGN.md) | System context, major components, delivery phases, design principles |
| 02 | [System Architecture](./02-SYSTEM-ARCHITECTURE.md) | Component architecture, API contracts, real-time design, security, caching |
| 03 | [Production Cloud Architecture](./03-CLOUD-ARCHITECTURE.md) | AWS infrastructure, security groups, CI/CD pipeline, DR strategy, cost estimate |
| 04 | [Low-Level Design](./04-LOW-LEVEL-DESIGN.md) | Prisma schema, DB indexes, NestJS module internals, DTO definitions, Redis key design |
| 05 | [Phase 1 Mermaid Diagrams](./05-PHASE1-MERMAID-DIAGRAMS.md) | 12 Mermaid diagrams covering all key flows for MVP delivery |

---

## Architecture at a Glance

```
Users (Browser)
      │ HTTPS / WSS
      ▼
CloudFront + ALB (AWS)
      │
      ▼
NestJS API (ECS Fargate, Multi-AZ, Auto-scaling)
      │
  ┌───┼───────────┐
  │   │           │
  ▼   ▼           ▼
PostgreSQL  Redis    S3
(RDS)    (ElastiCache) (Attachments)
```

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
