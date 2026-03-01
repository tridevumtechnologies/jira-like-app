# Test Run Report — Jira-Like Backend
**Date:** 2026-03-01  
**Environment:** Virtual Environment (no Docker, no PostgreSQL, no Redis required)  
**Database:** SQLite in-memory (aiosqlite)  
**Redis:** fakeredis (in-process mock)  
**Python:** 3.13.1  
**pytest:** 9.0.2

---

## Summary

| Metric | Value |
|---|---|
| Total Tests | **52** |
| Passed | **52** ✅ |
| Failed | **0** |
| Errors | **0** |
| Duration | ~12 s |
| Overall Coverage | **80%** |

---

## Results by Module

### Auth (`tests/test_auth.py`) — 16 tests, all pass

| Test | Status |
|---|---|
| `TestRegister::test_register_success` | ✅ PASS |
| `TestRegister::test_register_duplicate_email` | ✅ PASS |
| `TestRegister::test_register_short_password` | ✅ PASS |
| `TestRegister::test_register_invalid_email` | ✅ PASS |
| `TestRegister::test_register_with_optional_fields` | ✅ PASS |
| `TestLogin::test_login_success` | ✅ PASS |
| `TestLogin::test_login_wrong_password` | ✅ PASS |
| `TestLogin::test_login_unknown_email` | ✅ PASS |
| `TestRefresh::test_refresh_success` | ✅ PASS |
| `TestRefresh::test_refresh_without_cookie` | ✅ PASS |
| `TestRefresh::test_refresh_token_rotation` | ✅ PASS |
| `TestGetMe::test_get_me_authenticated` | ✅ PASS |
| `TestGetMe::test_get_me_unauthenticated` | ✅ PASS |
| `TestGetMe::test_get_me_invalid_token` | ✅ PASS |
| `TestLogout::test_logout_success` | ✅ PASS |
| `TestLogout::test_logout_unauthenticated` | ✅ PASS |

### Projects (`tests/test_projects.py`) — 13 tests, all pass

| Test | Status |
|---|---|
| `TestCreateProject::test_create_project_success` | ✅ PASS |
| `TestCreateProject::test_create_project_minimal` | ✅ PASS |
| `TestCreateProject::test_create_project_duplicate_key` | ✅ PASS |
| `TestCreateProject::test_create_project_unauthenticated` | ✅ PASS |
| `TestCreateProject::test_create_project_missing_name` | ✅ PASS |
| `TestCreateProject::test_create_project_missing_key` | ✅ PASS |
| `TestListProjects::test_list_projects_returns_own_project` | ✅ PASS |
| `TestListProjects::test_list_projects_empty_for_new_user` | ✅ PASS |
| `TestListProjects::test_list_projects_unauthenticated` | ✅ PASS |
| `TestGetProject::test_get_project_success` | ✅ PASS |
| `TestGetProject::test_get_project_not_found` | ✅ PASS |
| `TestGetProject::test_get_project_access_denied_for_non_member` | ✅ PASS |
| `TestGetProject::test_get_project_unauthenticated` | ✅ PASS |

### Tickets (`tests/test_tickets.py`) — 23 tests, all pass

| Test | Status |
|---|---|
| `TestCreateTicket::test_create_ticket_success` | ✅ PASS |
| `TestCreateTicket::test_create_ticket_auto_increments_key` | ✅ PASS |
| `TestCreateTicket::test_create_ticket_with_story_type` | ✅ PASS |
| `TestCreateTicket::test_create_ticket_missing_title` | ✅ PASS |
| `TestCreateTicket::test_create_ticket_invalid_type` | ✅ PASS |
| `TestCreateTicket::test_create_ticket_project_not_found` | ✅ PASS |
| `TestCreateTicket::test_create_ticket_unauthenticated` | ✅ PASS |
| `TestListTickets::test_list_tickets_success` | ✅ PASS |
| `TestListTickets::test_list_tickets_pagination` | ✅ PASS |
| `TestListTickets::test_list_tickets_excludes_deleted` | ✅ PASS |
| `TestListTickets::test_list_tickets_non_member_forbidden` | ✅ PASS |
| `TestGetTicket::test_get_ticket_success` | ✅ PASS |
| `TestGetTicket::test_get_ticket_not_found` | ✅ PASS |
| `TestGetTicket::test_get_deleted_ticket_returns_404` | ✅ PASS |
| `TestUpdateTicket::test_update_title` | ✅ PASS |
| `TestUpdateTicket::test_update_status` | ✅ PASS |
| `TestUpdateTicket::test_update_priority_and_story_points` | ✅ PASS |
| `TestUpdateTicket::test_update_invalid_status` | ✅ PASS |
| `TestUpdateTicket::test_update_non_member_forbidden` | ✅ PASS |
| `TestDeleteTicket::test_delete_ticket_as_owner` | ✅ PASS |
| `TestDeleteTicket::test_delete_already_deleted_returns_404` | ✅ PASS |
| `TestDeleteTicket::test_delete_non_member_forbidden` | ✅ PASS |
| `TestDeleteTicket::test_delete_unauthenticated` | ✅ PASS |

---

## Coverage by File

| File | Stmts | Miss | Cover | Uncovered Lines |
|---|---|---|---|---|
| `app/__init__.py` | 0 | 0 | **100%** | — |
| `app/api/v1/endpoints/auth.py` | 36 | 4 | **89%** | 38-39, 49-50 |
| `app/api/v1/endpoints/projects.py` | 23 | 4 | **83%** | 22-23, 32, 48 |
| `app/api/v1/endpoints/tickets.py` | 30 | 4 | **87%** | 33, 48, 63, 74 |
| `app/api/v1/endpoints/users.py` | 8 | 0 | **100%** | — |
| `app/api/v1/router.py` | 11 | 0 | **100%** | — |
| `app/core/config.py` | 16 | 0 | **100%** | — |
| `app/core/dependencies.py` | 27 | 5 | **81%** | — |
| `app/core/security.py` | 23 | 0 | **100%** | — |
| `app/db/redis.py` | 13 | 1 | **92%** | (real Redis path, unused in tests) |
| `app/db/session.py` | 12 | 2 | **83%** | — |
| `app/main.py` | 22 | 9 | **59%** | lifespan (not triggered via ASGI client) |
| `app/models/project.py` | 34 | 0 | **100%** | — |
| `app/models/ticket.py` | 43 | 0 | **100%** | — |
| `app/models/user.py` | 23 | 0 | **100%** | — |
| `app/schemas/auth.py` | 36 | 2 | **94%** | — |
| `app/schemas/common.py` | 11 | 0 | **100%** | — |
| `app/schemas/project.py` | 37 | 3 | **92%** | — |
| `app/schemas/ticket.py` | 49 | 2 | **96%** | — |
| `app/schemas/user.py` | 10 | 0 | **100%** | — |
| `app/services/auth_service.py` | 68 | 23 | **66%** | refresh / logout paths |
| `app/services/project_service.py` | 37 | 23 | **38%** | membership management (update/delete not tested yet) |
| `app/services/ticket_service.py` | 64 | 44 | **31%** | update / delete service paths |
| **TOTAL** | **639** | **126** | **80%** | |

---

## Fixes Applied During This Run

| Area | Issue | Fix |
|---|---|---|
| `bcrypt` | `bcrypt 5.0.0` incompatible with `passlib 1.7.4` | Downgraded to `bcrypt==3.2.2` |
| `SQLite UUID binding` | `Uuid(as_uuid=True)` bind-processor called `.hex` on a JWT string | Converted JWT `sub` claim to `uuid.UUID` in `dependencies.py` |
| `HTTPBearer status code` | FastAPI 0.134 changed missing-auth response from `403` → `401` | Updated 7 test assertions to expect `401` |
| `conftest.py` | Required live PostgreSQL + Redis | Replaced with SQLite in-memory + fakeredis |
| `session.py` | Hard-coded `pool_pre_ping=True` fails on SQLite | Added SQLite detection; omits `pool_pre_ping`, adds `check_same_thread=False` |

---

## Mock Dev Server

Run the backend locally without any database or Redis installation:

```powershell
# From backend/
.\run_mock.ps1
```

Or manually:
```powershell
$env:DATABASE_URL="sqlite+aiosqlite:///./dev_mock.db"
$env:DEV_FAKE_REDIS="1"
$env:SECRET_KEY="f06601905b779fbc42bf8ba11cb7610cd77e582656a501052bf2710bdd999bdd"
$env:ALGORITHM="HS256"; $env:ACCESS_TOKEN_EXPIRE_MINUTES="15"
$env:REFRESH_TOKEN_EXPIRE_DAYS="7"
$env:BACKEND_CORS_ORIGINS='["http://localhost:5173"]'
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

- API docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  
- SQLite DB file: `backend/dev_mock.db` (auto-created on first start)
- Redis: in-process fakeredis (zero configuration)

---

## Report Files

| File | Description |
|---|---|
| `test-reports/junit.xml` | JUnit XML (CI-compatible) |
| `test-reports/coverage.xml` | Cobertura XML coverage |
| `test-reports/coverage-html/index.html` | Interactive HTML coverage report |
