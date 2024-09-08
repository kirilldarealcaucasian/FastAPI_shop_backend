import pytest
from httpx import AsyncClient, ASGITransport
from application.cmd import app
from application.schemas import UpdateUserS, UpdatePartiallyUserS


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def get_admin_header() -> str:
    data = {
        "email": "jordan@gmail.com",
        "password": "123456"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(url="v1/auth/login", json=data)
        access_token = response.json()['access_token']
        admin_header = f"Bearer {access_token}"
        return admin_header


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "user_id,status_code",
    [(2, 200), (100, 404)]
)
async def test_get_user_by_id(
        user_id: int,
        status_code: int,
        get_admin_header: str,
        ac: AsyncClient
):
    response = await ac.get(url=f"v1/users/{user_id}", headers={'Authorization': get_admin_header})
    assert response.status_code == status_code


@pytest.mark.asyncio
async def test_get_all_users():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(url="v1/users/")
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id,status_code",
    [(4, 204), (100, 404)]
)
async def test_delete_user(
        user_id: int,
        status_code: int,
        get_admin_header: str,
        ac: AsyncClient
):
    response = await ac.delete(
        url=f"v1/users/{user_id}",
        headers={"Authorization": get_admin_header}
    )
    assert response.status_code == status_code


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id,update_data,status_code",
    [
        (2, {"first_name": "Alisha", "last_name": "Belfordina", "email": "alisha@gmail.com", "role_name": "user"}, 200),
        (3, {"name": "Jordan1", "is_admin": "true"}, 422),
        (4, {"name": "test1", "is_admin": "true"}, 422)
    ]
)
async def test_update_user(
        user_id: int,
        update_data: UpdateUserS,
        status_code: int,
        get_admin_header: str,
        ac: AsyncClient
):
    response = await ac.put(
        url=f"v1/users/{user_id}",
        json=update_data,
        headers={"Authorization": get_admin_header}
    )
    assert response.status_code == status_code


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id,update_data,status_code",
    [
        (2, {"first_name": "Alice"}, 200),
        (100, {"first_name": "test1", "is_admin": "true"}, 404),
        (3, {"first": "test1"}, 422)
    ]
)
async def test_update_user_partially(
        user_id: int,
        update_data: UpdatePartiallyUserS,
        status_code: int,
        get_admin_header: str,
        ac: AsyncClient
):
    response = await ac.patch(
        url=f"v1/users/{user_id}", json=update_data,
        headers={"Authorization": get_admin_header}
    )
    assert response.status_code == status_code
