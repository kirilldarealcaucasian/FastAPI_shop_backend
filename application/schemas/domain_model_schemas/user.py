from datetime import date, datetime

from pydantic import BaseModel


class UserS(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    email: str | None = None
    hashed_password: str | bytes | None = None
    registration_date: datetime | None = None
    role_name: str | None = None
    date_of_birth: date | None = None
