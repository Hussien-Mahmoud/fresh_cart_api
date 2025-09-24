from typing import Optional, List
from ninja import Schema
from decimal import Decimal


class CartItemIn(Schema):
    product_id: int
    quantity: int


class CartItemOut(Schema):
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class CartOut(Schema):
    id: int
    items: List[CartItemOut]
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    coupon: Optional[str] = None


class CouponIn(Schema):
    code: str


class CouponOut(Schema):
    id: int
    code: str
    discount_type: str
    amount: Decimal
    active: bool
