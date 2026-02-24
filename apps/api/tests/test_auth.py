# apps/api/tests/test_auth.py
from fastapi.testclient import TestClient


def test_register_login_me_logout(client: TestClient):
    # Register
    r = client.post("/auth/register", json={"email": "eric@example.com", "password": "longpassword123"})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["user"]["email"] == "eric@example.com"

    # Cookie should now be set; /auth/me should work
    me = client.get("/auth/me")
    assert me.status_code == 200, me.text
    me_data = me.json()
    assert me_data["user"]["email"] == "eric@example.com"
    assert me_data["workspace"] is not None

    # Logout
    out = client.post("/auth/logout")
    assert out.status_code == 200, out.text

    # /me should now fail
    me2 = client.get("/auth/me")
    assert me2.status_code == 401

    # Login again
    login = client.post("/auth/login", json={"email": "eric@example.com", "password": "longpassword123"})
    assert login.status_code == 200, login.text
    me3 = client.get("/auth/me")
    assert me3.status_code == 200