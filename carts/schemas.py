from typing import Optional, List
from ninja import ModelSchema, Schema
from decimal import Decimal

from carts.models import Coupon
from catalog.schemas import ProductOut


class CouponIn(Schema):
    code: str


class CouponOut(ModelSchema):
    is_valid_now: bool

    class Meta:
        model = Coupon
        fields = "__all__"
        exclude = ['valid_from']


class CartItemIn(Schema):
    product_id: int
    quantity: Optional[int] = 1


class CartItemOut(Schema):
    product: ProductOut
    quantity: int
    line_total: Decimal


class CartOut(Schema):
    id: int
    items: List[CartItemOut]
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    coupon: Optional[CouponOut] = None
