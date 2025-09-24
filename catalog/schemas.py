from typing import Optional
from ninja import Schema
from decimal import Decimal


class CategoryIn(Schema):
    name: str
    description: Optional[str] = ""


class CategoryOut(Schema):
    id: int
    name: str
    slug: str
    description: Optional[str] = ""


class BrandIn(Schema):
    name: str


class BrandOut(Schema):
    id: int
    name: str
    slug: str


class ProductIn(Schema):
    name: str
    description: Optional[str] = ""
    price: Decimal
    stock: int
    category_id: int
    brand_id: Optional[int] = None
    image_url: Optional[str] = ""


class ProductOut(Schema):
    id: int
    name: str
    slug: str
    description: Optional[str] = ""
    price: Decimal
    stock: int
    is_active: bool
    category_id: int
    brand_id: Optional[int]
    image_url: Optional[str] = ""
