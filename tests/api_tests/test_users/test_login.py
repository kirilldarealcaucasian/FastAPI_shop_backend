import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email,password,status_code",
    [
        ("jordan@gmail.com", "123456", 200),
        ("test@gmail.com", "1234567", 401),
        ("testgmail.com", "1234567", 422),
    ]
)
async def test_login(ac: AsyncClient, email: str, password: str, status_code: int):
    data = {
        "email": email,
        "password": password
    }
    response = await ac.post(url="v1/auth/login", json=data)

    assert response.status_code == status_code
