"""Tests for ticket endpoints:
  POST   /api/v1/projects/{project_id}/tickets
  GET    /api/v1/projects/{project_id}/tickets
  GET    /api/v1/tickets/{ticket_id}
  PUT    /api/v1/tickets/{ticket_id}
  DELETE /api/v1/tickets/{ticket_id}
"""
import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_TICKET_BASE = {
    "title": "Fix the login bug",
    "ticket_type": "BUG",
    "priority": "HIGH",
    "description": "Users cannot login with correct credentials.",
}


async def _create_ticket(
    client: AsyncClient, project_id: str, auth_headers: dict, overrides: dict | None = None
) -> dict:
    payload = {**_TICKET_BASE, **(overrides or {})}
    resp = await client.post(
        f"/api/v1/projects/{project_id}/tickets",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Create ticket
# ---------------------------------------------------------------------------
class TestCreateTicket:
    async def test_create_ticket_success(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        body = await _create_ticket(client, project["id"], auth_headers)
        assert body["title"] == _TICKET_BASE["title"]
        assert body["ticket_type"] == "BUG"
        assert body["priority"] == "HIGH"
        assert body["status"] == "TODO"  # default
        assert body["key"].startswith(project["key"] + "-")
        assert "id" in body

    async def test_create_ticket_auto_increments_key(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        t1 = await _create_ticket(client, project["id"], auth_headers, {"title": "T1"})
        t2 = await _create_ticket(client, project["id"], auth_headers, {"title": "T2"})
        nums = [int(t["key"].split("-")[1]) for t in [t1, t2]]
        assert nums[1] == nums[0] + 1

    async def test_create_ticket_with_story_type(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        body = await _create_ticket(
            client, project["id"], auth_headers,
            {"ticket_type": "STORY", "priority": "MEDIUM"}
        )
        assert body["ticket_type"] == "STORY"

    async def test_create_ticket_missing_title(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        resp = await client.post(
            f"/api/v1/projects/{project['id']}/tickets",
            json={"ticket_type": "BUG", "priority": "HIGH"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_create_ticket_invalid_type(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        resp = await client.post(
            f"/api/v1/projects/{project['id']}/tickets",
            json={**_TICKET_BASE, "ticket_type": "NOT_A_TYPE"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_create_ticket_project_not_found(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            f"/api/v1/projects/{fake_id}/tickets",
            json=_TICKET_BASE,
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_create_ticket_unauthenticated(
        self, client: AsyncClient, project: dict
    ) -> None:
        resp = await client.post(
            f"/api/v1/projects/{project['id']}/tickets", json=_TICKET_BASE
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# List tickets
# ---------------------------------------------------------------------------
class TestListTickets:
    async def test_list_tickets_success(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        await _create_ticket(client, project["id"], auth_headers, {"title": "List T1"})
        await _create_ticket(client, project["id"], auth_headers, {"title": "List T2"})

        resp = await client.get(
            f"/api/v1/projects/{project['id']}/tickets", headers=auth_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2
        assert len(body["items"]) >= 2

    async def test_list_tickets_pagination(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        for i in range(5):
            await _create_ticket(
                client, project["id"], auth_headers, {"title": f"Paginate {i}"}
            )
        resp = await client.get(
            f"/api/v1/projects/{project['id']}/tickets?skip=0&limit=3",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()["items"]) <= 3

    async def test_list_tickets_excludes_deleted(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        ticket = await _create_ticket(
            client, project["id"], auth_headers, {"title": "To delete"}
        )
        # Soft delete it
        await client.delete(
            f"/api/v1/tickets/{ticket['id']}", headers=auth_headers
        )
        resp = await client.get(
            f"/api/v1/projects/{project['id']}/tickets", headers=auth_headers
        )
        ids = [t["id"] for t in resp.json()["items"]]
        assert ticket["id"] not in ids

    async def test_list_tickets_non_member_forbidden(
        self, client: AsyncClient, project: dict
    ) -> None:
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Outsider",
                "email": "outsider_ticket@example.com",
                "password": "Password123",
            },
        )
        token = reg.json()["access_token"]
        resp = await client.get(
            f"/api/v1/projects/{project['id']}/tickets",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Get ticket detail
# ---------------------------------------------------------------------------
class TestGetTicket:
    async def test_get_ticket_success(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        ticket = await _create_ticket(client, project["id"], auth_headers)
        resp = await client.get(
            f"/api/v1/tickets/{ticket['id']}", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == ticket["id"]

    async def test_get_ticket_not_found(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/api/v1/tickets/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    async def test_get_deleted_ticket_returns_404(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        ticket = await _create_ticket(
            client, project["id"], auth_headers, {"title": "Will be deleted"}
        )
        await client.delete(f"/api/v1/tickets/{ticket['id']}", headers=auth_headers)
        resp = await client.get(
            f"/api/v1/tickets/{ticket['id']}", headers=auth_headers
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update ticket
# ---------------------------------------------------------------------------
class TestUpdateTicket:
    async def test_update_title(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        ticket = await _create_ticket(client, project["id"], auth_headers)
        resp = await client.put(
            f"/api/v1/tickets/{ticket['id']}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    async def test_update_status(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        ticket = await _create_ticket(client, project["id"], auth_headers)
        resp = await client.put(
            f"/api/v1/tickets/{ticket['id']}",
            json={"status": "IN_PROGRESS"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_PROGRESS"

    async def test_update_priority_and_story_points(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        ticket = await _create_ticket(client, project["id"], auth_headers)
        resp = await client.put(
            f"/api/v1/tickets/{ticket['id']}",
            json={"priority": "LOW", "story_points": 5},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["priority"] == "LOW"
        assert body["story_points"] == 5

    async def test_update_invalid_status(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        ticket = await _create_ticket(client, project["id"], auth_headers)
        resp = await client.put(
            f"/api/v1/tickets/{ticket['id']}",
            json={"status": "INVALID_STATUS"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_update_non_member_forbidden(
        self, client: AsyncClient, project: dict, auth_headers: dict
    ) -> None:
        ticket = await _create_ticket(client, project["id"], auth_headers)
        # Another user who is not a project member
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Not Member",
                "email": "notmember_upd@example.com",
                "password": "Password123",
            },
        )
        token = reg.json()["access_token"]
        resp = await client.put(
            f"/api/v1/tickets/{ticket['id']}",
            json={"title": "Hacked"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Delete ticket (soft delete)
# ---------------------------------------------------------------------------
class TestDeleteTicket:
    async def test_delete_ticket_as_owner(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        ticket = await _create_ticket(client, project["id"], auth_headers)
        resp = await client.delete(
            f"/api/v1/tickets/{ticket['id']}", headers=auth_headers
        )
        assert resp.status_code == 204

    async def test_delete_already_deleted_returns_404(
        self, client: AsyncClient, auth_headers: dict, project: dict
    ) -> None:
        ticket = await _create_ticket(client, project["id"], auth_headers)
        await client.delete(f"/api/v1/tickets/{ticket['id']}", headers=auth_headers)
        resp = await client.delete(
            f"/api/v1/tickets/{ticket['id']}", headers=auth_headers
        )
        assert resp.status_code == 404

    async def test_delete_non_member_forbidden(
        self, client: AsyncClient, project: dict, auth_headers: dict
    ) -> None:
        ticket = await _create_ticket(client, project["id"], auth_headers)
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Not Member",
                "email": "notmember_del@example.com",
                "password": "Password123",
            },
        )
        token = reg.json()["access_token"]
        resp = await client.delete(
            f"/api/v1/tickets/{ticket['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_delete_unauthenticated(
        self, client: AsyncClient, project: dict, auth_headers: dict
    ) -> None:
        ticket = await _create_ticket(client, project["id"], auth_headers)
        resp = await client.delete(f"/api/v1/tickets/{ticket['id']}")
        assert resp.status_code == 401
