from typing import Optional, List
from ninja import Schema
from decimal import Decimal


class OrderCreateIn(Schema):
    address_id: int


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
    address_id: int
    coupon_code: Optional[str] = None
    items: List[OrderItemOut]
