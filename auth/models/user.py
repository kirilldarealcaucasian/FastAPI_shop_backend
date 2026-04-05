from dataclasses import dataclass
from datetime import date

from auth.schemas import RoleName


@dataclass(slots=True)
class User:
    id: int
    first_name: str
    last_name: str
    gender: str
    email: str
    hashed_password: str
    role_name: RoleName = "user"
    date_of_birth: date | None = None
