from enum import StrEnum


class BookEventAction(StrEnum):
    VIEW = "view"
    LONG_VIEW = "long_view"
    CART = "cart"
    PURCHASE = "purchase"

    @classmethod
    def from_action(cls, action: str) -> "BookEventAction | None":
        normalized = action.strip().lower().replace("-", "_")
        try:
            return cls(normalized)
        except ValueError:
            return None

    @property
    def weight(self) -> float:
        match self:
            case self.VIEW:
                return 1.0
            case self.LONG_VIEW:
                return 3.0
            case self.CART:
                return 1.5
            case self.PURCHASE:
                return 2.0


__all__ = ("BookEventAction",)
