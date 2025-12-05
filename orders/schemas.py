from typing import Optional, List
from ninja import Schema
from decimal import Decimal

from users.schemas import AddressOut


class OrderCreateIn(Schema):
    address_id: Optional[int] = None


class OrderItemOut(Schema):
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class OrderOut(Schema):
    id: int
    status: str
    total_amount: Decimal
    address: Optional[AddressOut] = None
    address_text: str
    coupon_code: Optional[str] = None
    discount_amount: Decimal
    items: List[OrderItemOut]
