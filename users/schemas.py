from typing import Optional
from ninja import Schema


class AddressIn(Schema):
    line1: str
    line2: Optional[str] = ""
    city: str
    state: Optional[str] = ""
    postal_code: str
    country: str
    is_default: Optional[bool] = False


class AddressOut(Schema):
    id: int
    line1: str
    line2: Optional[str]
    city: str
    state: Optional[str]
    postal_code: str
    country: str
    is_default: bool
