import pytest
from httpx import AsyncClient
from application.cmd import app
from application.schemas import UpdatePartiallyOrderS


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def get_admin_header() -> str:
    data = {
        "email": "jordan@gmail.com",
        "password": "123456"
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(url="auth/login", json=data)
        admin_header = f"Bearer {response.json()['token']}"
        return admin_header


@pytest.mark.asyncio(scope="session")
async def test_get_all_orders():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(url="orders")
    assert response.status_code == 200


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "user_id,status_code",
    [(3, 200), (100, 404)]
)
async def test_get_order_by_user_id(
        user_id: int,
        status_code: int,
):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(url=f"orders/users/{user_id}")
        assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "order_id,status_code",
    [(1, 200), (3, 404)]
)
async def test_get_order_by_id(
        order_id: int,
        status_code: int,
        get_admin_header: str
):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(url=f"orders/{order_id}", headers={"Authorization": get_admin_header})
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "order_data,status_code",
    [({"user_id": 3, "order_status": "pending"}, 201), ({"user_id": 100, "order_status": "pending"}, 404)]
)
async def test_create_order(
        order_data: dict,
        status_code: int,
):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(url="orders/", json=order_data)
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "order_id,status_code",
    [(3, 204), (100, 404)]
)
async def test_delete_order(
        order_id: dict,
        status_code: int,
        get_admin_header: str
):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(url=f"orders/{order_id}", headers={"Authorization": get_admin_header})
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "order_id,book_id,quantity,status_code",
    [
     (1, "ecd38a11-3bbd-4bba-b596-3e2d554796a7", 1, 200),
     (1, "ecd38a11-3bbd-4bba-b596-3e2d554796a7", 2, 200),
     (1, "ecd38a11-3bbd-4bba-b596-3e2d554796a7", 100, 400),
     (2, "ecd38a11-3bbd-4bba-b596-3e2d55479", 10, 422),
    ]
)
async def test_add_book_to_order(
        order_id: int,
        book_id: str,
        quantity: int,
        status_code: int,
        get_admin_header: str
):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            url=f"/orders/{order_id}/books/{book_id}",
            json={"quantity": quantity},
            headers={"Authorization": get_admin_header}
        )
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "order_id,book_id,status_code",
    [
        (1, "0b003aac-25dc-4fd6-8f89-e2ba796c6386", 204),
        (3, "0b003aac-25dc-4fd6-8f89-e2ba796c6386", 404),
    ]
)
async def test_delete_book_from_order(
        order_id: int,
        book_id: str,
        status_code: int,
        get_admin_header: str
):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(
            url=f"/orders/{order_id}/books/{book_id}",
            headers={"Authorization": get_admin_header}
        )
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "order_id,update_data,status_code",
    [
        (1, {"order_status": "processing", "total_sum": "555.5"}, 200),
        (100, {"order_status": "processing", "total_sum": "555.5"}, 404)
    ]
)
async def test_update_order(
        order_id: int,
        update_data: UpdatePartiallyOrderS,
        status_code: int,
        get_admin_header: str
):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.patch(
            url=f"orders/{order_id}",
            headers={"Authorization": get_admin_header},
            json=update_data
        )
    assert response.status_code == status_code


