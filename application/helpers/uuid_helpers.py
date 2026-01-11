from uuid import UUID, uuid4


def is_valid_uuid(value: str) -> bool:
    try:
        UUID(value)
    except ValueError:
        return False
    return True

def generate_uuid() -> UUID:
    return uuid4()
