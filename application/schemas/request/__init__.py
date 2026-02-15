from .author import (
    CreateAuthorRequest,
    UpdateAuthorRequest,
    UpdatePartiallyAuthorRequest,
)
from .book import (
    CreateBookRequest,
    UpdateBookRequest,
    UpdatePartiallyBookRequest,
)
from .cart import AddBookToCartRequest, DeleteBookFromCartRequest
from .category import CreateCategoryRequest, UpdateCategoryRequest
from .order import (
    AddBookToOrderRequest,
    CreateOrderRequest,
    OrderItemRequest,
    UpdateOrderRequest,
    UpdatePartiallyOrderRequest,
)
from .payment import CreatePaymentRequest
from .publisher import (
    CreatePublisherRequest,
    UpdatePublisherRequest,
    UpdatePartiallyPublisherRequest,
)
from .shopping_session import (
    CreateShoppingSessionRequest,
    UpdatePartiallyShoppingSessionRequest,
)
from .user import (
    LoginUserRequest,
    RegisterUserRequest,
    UpdatePartiallyUserRequest,
    UpdateUserRequest,
)

__all__ = (
    "AddBookToCartRequest",
    "AddBookToOrderRequest",
    "CreateAuthorRequest",
    "CreateBookRequest",
    "CreateCategoryRequest",
    "CreateOrderRequest",
    "CreatePaymentRequest",
    "CreatePublisherRequest",
    "CreateShoppingSessionRequest",
    "DeleteBookFromCartRequest",
    "LoginUserRequest",
    "OrderItemRequest",
    "RegisterUserRequest",
    "UpdateAuthorRequest",
    "UpdateBookRequest",
    "UpdateCategoryRequest",
    "UpdateOrderRequest",
    "UpdatePartiallyAuthorRequest",
    "UpdatePartiallyBookRequest",
    "UpdatePartiallyOrderRequest",
    "UpdatePartiallyPublisherRequest",
    "UpdatePartiallyShoppingSessionRequest",
    "UpdatePartiallyUserRequest",
    "UpdatePublisherRequest",
    "UpdateUserRequest",
)
