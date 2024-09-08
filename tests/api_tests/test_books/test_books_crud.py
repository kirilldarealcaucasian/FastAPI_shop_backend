import pytest
from httpx import AsyncClient, ASGITransport
from application.cmd import app
from application.schemas import UpdateBookS


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def get_admin_header() -> str:
    data = {"email": "jordan@gmail.com", "password": "123456"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(url="v1/auth/login", json=data)
        access_token = response.json()['access_token']
        admin_header = f"Bearer {access_token}"
        return admin_header


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "book_id,status_code",
    [
        ("0b003aac-25dc-4fd6-8f89-e2ba796c6386", 200),
        ("0b003aac-25dc-4fd6-8f89-e2ba796c6385", 404),
    ],
)
async def test_get_book_by_id(
        book_id: int | str, status_code: int, get_admin_header: str
):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            url=f"v1/books/{book_id}", headers={"Authorization": get_admin_header}
        )
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
async def test_get_all_books(ac):
    response = await ac.get(url="v1/books")
    assert response.status_code == 200


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "limit,page,status_code",
    [
        (1, 0, 200),
        (-1, 0, 422),
        (0, -1, 422),
        (100000, 1, 200),
        (1, 1000000, 200)
    ]
)
async def test_get_all_books_pagination(limit: int, page: int, status_code: int, ac):
    response = await ac.get(url=f"v1/books?limit={limit}&page={page}")
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "filters,status_code",
    [
        ({"id__eq": "0b003aac-25dc-4fd6-8f89-e2ba796c6386", }, 200),
        ({"isbn__eq": "777776", }, 200),
        ({"name__eq": "Book 2", }, 200),
        ({"name__ilike": "Book"}, 200),
        ({"number_in_stock__eq": 10}, 200),
        ({"price_per_unit__gt": 1}, 200),
        ({"price_per_unit__lt": 1}, 200),
        ({"price_with_discount__gt": 50}, 200),
        ({"price_with_discount__lt": 50}, 200),
        ({"number_in_stock__gte": 3}, 200),
        ({"id__eq": "0b003aac-25dc-4fd6-8f89-e2ba796c6386", "name__ilike": "Book"}, 200),
        ({"number_in_stock__gte": 5, "number_in_stock__lte": 3}, 200),
        ({"order_by": "id"}, 200),
        ({"order_by": "number_in_stock,isbn"}, 200),
        ({"order_by": "-number_in_stock,isbn"}, 200),
        ({"order_by": "gfgfgfnumber_in_stock,isbn"}, 400),
        ({"order_by": "-number_in_stock,hghgisbn"}, 400),
    ]
)
async def test_get_all_books_filters(filters: dict, status_code: int, ac):
    filter_list = []
    for filter, value in filters.items():
        filter_list.append(f"{filter}={value}")
    filters = "&".join(filter_list)
    print("filters: ", filters)

    response = await ac.get(url=f"v1/books?{filters}")
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "isbn,name,description,price_per_unit,number_in_stock,rating,discount,status_code",
    [
        ("5555", "New Book", "", 10, 100, 5, 10, 201),
        ("5555", "New Book", "", 10, 100, 5, 10, 409),
        ("3333", "New Book 3", "description", 0, 100, 5, 10, 422),
        ("3333", "New Book 3", "description", 2, -1, 5, 10, 422),
        ("3333", "", "description", 10, 1, 5, 10, 422),
        ("", "New Book 4", "description", 10, 1, 5, 10, 422),
        ("ffff", "New Book 5", "description", -100, 1, 5, 10, 422),
        ("ffff", "New Book 5", "description", 10, -50, 5, 10, 422),
    ],
)
async def test_create_book(
        isbn: str,
        name: str,
        description: str,
        price_per_unit: int,
        number_in_stock: int,
        rating: float,
        discount: int,
        status_code: int,
        ac: AsyncClient
):
    data = {
        "isbn": isbn,
        "name": name,
        "description": description,
        "price_per_unit": price_per_unit,
        "number_in_stock": number_in_stock,
        "rating": rating,
        "discount": discount,
    }
    response = await ac.post(url="v1/books/", json=data)
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "book_id,status_code",
    [
        ("657dab80-50ff-45d9-a242-ac0357d97417", 204),
        ("657dab80-50ff-45d9-a242-ac0357d97417", 404),
    ],
)
async def test_delete_book(book_id, status_code, ac):
    response = await ac.delete(url=f"v1/books/{book_id}")
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "book_id,update_data,status_code",
    [
        (
                "ecd38a11-3bbd-4bba-b596-3e2d554796a7",
                {
                    "name": "Book for update122221",
                    "description": "book for update updated",
                    "price_per_unit": 66.5,
                    "number_in_stock": 5,
                    "isbn": "1010101",
                    "rating": 2.8,
                    "discount": 10
                },
                200,
        ),
        (
                "ecd38a11-3bbd-4bba-b596-3e2d554796a7",
                {
                    "isbn": "1010101",
                    "name": "Book updated",
                    "price_per_unit": 85.4,
                    "number_in_stock": 84,
                    "rating": 3,
                    "discount": -10
                },
                422,
        ),
        (
                "ebd38a11-3bbd-4bba-b596-3e2d554796a7",
                {
                    "name": "Book for update122221",
                    "description": "book for update",
                    "price_per_unit": 66.5,
                    "number_in_stock": 5,
                    "isbn": "1010101",
                    "rating": 6,
                    "discount": 10
                },
                404,
        ),
    ],
)
async def test_update_book(book_id: int | str, update_data: UpdateBookS, status_code, ac):
    response = await ac.put(url=f"v1/books/{book_id}", json=update_data)
    assert response.status_code == status_code


@pytest.mark.asyncio(scope="session")
@pytest.mark.parametrize(
    "book_id,update_data,status_code",
    [
        (
                "ecd38a11-3bbd-4bba-b596-3e2d554796a7",
                {
                    "name": "string",
                    "description": "string",
                    "price_per_unit": 5,
                    "number_in_stock": 10,
                    "rating": 5,
                    "discount": 5
                },
                200
        ),
        (
                "ecd38a11-3bbd-4bba-b596-3e2d554796a7",
                {
                    "name": "string",
                    "description": "string",
                    "price_per_unit": 5,
                    "number_in_stock": 0,
                    "rating": 0,
                    "discount": -5
                },
                422
        ),
(
                "ecd38a11-3bbd-4bba-b596-3e2d554796a7",
                {
                    "name": "string",
                    "description": "string",
                    "price_per_unit": 5,
                    "number_in_stock": 0,
                    "rating": -4,
                    "discount": 4
                },
                422
        ),
    ]
)
async def test_update_book_partially(
        book_id: str,
        update_data: dict,
        status_code: int
):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.patch(url=f"v1/books/{book_id}", json=update_data)
    assert response.status_code == status_code
