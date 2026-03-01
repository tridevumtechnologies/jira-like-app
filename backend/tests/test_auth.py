"""Tests for /api/v1/auth/* endpoints."""
import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------
class TestRegister:
    async def test_register_success(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Alice Smith",
                "email": "alice@example.com",
                "password": "SecurePass1",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        # HttpOnly cookie should be set
        assert "refresh_token" in resp.cookies

    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        payload = {
            "full_name": "Bob Jones",
            "email": "bob@example.com",
            "password": "SecurePass1",
        }
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]

    async def test_register_short_password(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"full_name": "Carol", "email": "carol@example.com", "password": "short"},
        )
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"full_name": "Dave", "email": "not-an-email", "password": "Password123"},
        )
        assert resp.status_code == 422

    async def test_register_with_optional_fields(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Eve White",
                "email": "eve@example.com",
                "password": "SecurePass1",
                "address": "123 Main St",
                "security_question": {
                    "question": "What is your pet's name?",
                    "answer": "Fluffy",
                },
            },
        )
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
class TestLogin:
    async def test_login_success(self, client: AsyncClient) -> None:
        email, password = "login_test@example.com", "Password123"
        await client.post(
            "/api/v1/auth/register",
            json={"full_name": "Login User", "email": email, "password": password},
        )
        resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert "refresh_token" in resp.cookies

    async def test_login_wrong_password(self, client: AsyncClient) -> None:
        email = "wrongpass@example.com"
        await client.post(
            "/api/v1/auth/register",
            json={"full_name": "User", "email": email, "password": "CorrectPass1"},
        )
        resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "WrongPass1"}
        )
        assert resp.status_code == 401

    async def test_login_unknown_email(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "Password123"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------
class TestRefresh:
    async def test_refresh_success(self, client: AsyncClient) -> None:
        # Register to get refresh cookie
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Refresh User",
                "email": "refresh@example.com",
                "password": "Password123",
            },
        )
        assert reg.status_code == 201

        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        # New refresh cookie issued
        assert "refresh_token" in resp.cookies

    async def test_refresh_without_cookie(self, client: AsyncClient) -> None:
        # Fresh client — no cookie
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    async def test_refresh_token_rotation(self, client: AsyncClient) -> None:
        """Calling refresh twice should rotate the token both times."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Rotate User",
                "email": "rotate@example.com",
                "password": "Password123",
            },
        )
        first = await client.post("/api/v1/auth/refresh")
        second = await client.post("/api/v1/auth/refresh")
        assert first.status_code == 200
        assert second.status_code == 200
        assert (
            first.json()["access_token"] != second.json()["access_token"]
        ), "access tokens should differ after rotation"


# ---------------------------------------------------------------------------
# Get current user (/me)
# ---------------------------------------------------------------------------
class TestGetMe:
    async def test_get_me_authenticated(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "testuser@example.com"
        assert "password" not in body
        assert "password_hash" not in body

    async def test_get_me_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer this.is.invalid"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
class TestLogout:
    async def test_logout_success(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert resp.status_code == 204
        # Cookie should be cleared
        assert resp.cookies.get("refresh_token") is None or resp.cookies.get("refresh_token") == ""

    async def test_logout_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 401
