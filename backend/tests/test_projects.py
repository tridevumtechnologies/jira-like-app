"""Tests for /api/v1/projects/* endpoints."""
import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Create project
# ---------------------------------------------------------------------------
class TestCreateProject:
    async def test_create_project_success(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.post(
            "/api/v1/projects",
            json={"name": "My Project", "key": "MYPROJ", "description": "A test project"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "My Project"
        assert body["key"] == "MYPROJ"
        assert "id" in body
        assert "owner_id" in body

    async def test_create_project_minimal(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """description is optional."""
        resp = await client.post(
            "/api/v1/projects",
            json={"name": "Minimal", "key": "MIN"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["description"] is None

    async def test_create_project_duplicate_key(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        payload = {"name": "First", "key": "DUPKEY"}
        await client.post("/api/v1/projects", json=payload, headers=auth_headers)
        resp = await client.post("/api/v1/projects", json=payload, headers=auth_headers)
        assert resp.status_code == 409

    async def test_create_project_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/projects",
            json={"name": "No Auth", "key": "NOAUTH"},
        )
        assert resp.status_code == 403

    async def test_create_project_missing_name(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.post(
            "/api/v1/projects",
            json={"key": "NONAME"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_create_project_missing_key(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.post(
            "/api/v1/projects",
            json={"name": "No Key"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List projects
# ---------------------------------------------------------------------------
class TestListProjects:
    async def test_list_projects_returns_own_project(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        resp = await client.get("/api/v1/projects", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        ids = [p["id"] for p in body["items"]]
        assert project["id"] in ids

    async def test_list_projects_empty_for_new_user(
        self, client: AsyncClient
    ) -> None:
        # Register a brand-new user
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "New User",
                "email": "newuser_list@example.com",
                "password": "Password123",
            },
        )
        token = reg.json()["access_token"]
        resp = await client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        assert resp.json()["items"] == []

    async def test_list_projects_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/projects")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Get project detail
# ---------------------------------------------------------------------------
class TestGetProject:
    async def test_get_project_success(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == project["id"]

    async def test_get_project_not_found(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/api/v1/projects/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    async def test_get_project_access_denied_for_non_member(
        self, client: AsyncClient, project: dict
    ) -> None:
        # Different user — not a member
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Outsider",
                "email": "outsider@example.com",
                "password": "Password123",
            },
        )
        token = reg.json()["access_token"]
        resp = await client.get(
            f"/api/v1/projects/{project['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_get_project_unauthenticated(
        self, client: AsyncClient, project: dict
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project['id']}")
        assert resp.status_code == 403
