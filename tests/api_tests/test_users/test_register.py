import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "first_name,last_name,email,password,confirm_password,gender,status_code",
    [
        ("John", "Black", "john@gmail.com", "123456", "123456", "male", 200),
        ("John", "", "john@gmail.com", "123456", "123456", "male", 422),
        ("", "Black", "john@gmail.com", "123456", "123456", "male", 422),
        ("John", "Black", "", "123456", "123456", "male", 422),
        ("John""", "Black", "", "1234567", "123456", "male", 422),
    ]
)
async def test_register_user(
        ac: AsyncClient,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        confirm_password: str,
        gender: str,
        status_code: str
):
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password,
        "confirm_password": confirm_password,
        "gender": gender,
        "status_code": status_code
    }
    response = await ac.post(url="v1/auth/register", json=data)
    assert response.status_code == status_code
