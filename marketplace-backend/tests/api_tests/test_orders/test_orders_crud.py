import pytest


@pytest.fixture(scope="module")
def admin_headers() -> dict[str, str]:
    return {"X-User-Id": "3", "X-User-Role": "admin"}


@pytest.mark.asyncio
async def test_get_all_orders(ac):
    response = await ac.get("/orders")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
@pytest.mark.parametrize("user_id,status_code", [(3, 200), (999, 404)])
async def test_get_order_by_user_id(ac, user_id: int, status_code: int):
    response = await ac.get(f"/orders/users/{user_id}")
    assert response.status_code == status_code


@pytest.mark.asyncio
async def test_get_order_by_id_requires_identity(ac):
    response = await ac.get("/orders/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_order_by_id_as_admin(ac, admin_headers: dict[str, str]):
    response = await ac.get("/orders/1", headers=admin_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["order_id"] == 1
    assert isinstance(payload["books"], list)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "order_data,status_code",
    [({"user_id": 3, "order_status": "pending"}, 201), ({"user_id": 1000}, 404)],
)
async def test_create_order(ac, order_data: dict, status_code: int):
    response = await ac.post("/orders/", json=order_data)
    assert response.status_code == status_code
    if status_code == 201:
        assert "id" in response.json()


@pytest.mark.asyncio
async def test_update_order(ac, admin_headers: dict[str, str]):
    response = await ac.patch(
        "/orders/1",
        headers=admin_headers,
        json={"order_status": "done"},
    )
    assert response.status_code == 200
    assert response.json()["order_status"] == "done"


@pytest.mark.asyncio
async def test_delete_order(ac, admin_headers: dict[str, str]):
    response = await ac.delete("/orders/2", headers=admin_headers)
    assert response.status_code == 204

    response = await ac.delete("/orders/2", headers=admin_headers)
    assert response.status_code == 404
