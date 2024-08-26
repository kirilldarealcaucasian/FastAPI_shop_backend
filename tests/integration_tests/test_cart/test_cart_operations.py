from uuid import UUID

import pytest
from httpx import AsyncClient, ASGITransport
from pytest import fail
from application.cmd import app
from core.config import settings


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def get_admin_header() -> str:
    data = {"email": "jordan@gmail.com", "password": "123456"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(url="v1/auth/login", json=data)
        access_token = response.json()['access_token']
        admin_header = f"Bearer {access_token}"
        return admin_header


@pytest.mark.asyncio
@pytest.fixture(
    scope="session",
    params=[{"email": "alisha@gmail.com", "password": "123456"}]
)
async def get_jwt_token(request) -> str:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(url="v1/auth/login", json=request.param)
        access_token = response.json()['access_token']
        token = f"Bearer {access_token}"
        return token


@pytest.mark.asyncio(scope="session")
async def test_create_cart_without_auth(ac: AsyncClient):
    response = await ac.post(url=f"/v1/cart/")
    cookie = response.cookies.get(name=settings.SHOPPING_SESSION_COOKIE_NAME)
    if not cookie:
        fail(reason="No cookie in the response")
    assert response.status_code == 201


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "user_id,status_code",
    [
        (2, 201),
        (2, 409)
    ]
)
async def test_create_cart_with_auth(
        user_id: int,
        status_code: int,
        ac: AsyncClient,
        get_jwt_token: str
):
    data = {"user_id": user_id}
    response = await ac.post(
        url=f"/v1/cart/",
        data=data,
        headers={"Authorization": get_jwt_token}
    )
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "user_id,status_code",
    [
        (3, 200),
        (2, 404),  # user without cart
        (100, 404),  # user that doesn't exist
    ]
)
async def test_get_cart_by_user_id(
        ac: AsyncClient,
        user_id: int,
        status_code: int
):
    response = await ac.get(url=f"v1/cart/users/{user_id}")
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "session_id,status_code",
    [
        ("01e1ca73-5dea-46f2-a19b-56b5a7804efc", 200),
        ("01e1ca73-5dea-46f2-a19b-56b5a7804efb", 404),
        ("fdkjfdjfdjfjdhg", 422)
    ]
)
async def test_get_cart_by_session_id(
        ac: AsyncClient,
        session_id: str,
        status_code: int
):
    cookie = {f"{settings.SHOPPING_SESSION_COOKIE_NAME}": session_id}
    response = await ac.get(
        url=f"v1/cart/",
        cookies=cookie
    )
    assert response.status_code == status_code