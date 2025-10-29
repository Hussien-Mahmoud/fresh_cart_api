from ninja import FilterSchema, Field
from typing import Optional
from decimal import Decimal

from django.db.models import Q

class ProductFilterSchema(FilterSchema):
    category_id: Optional[int] = Field(None, alias="category")
    brand_id: Optional[int] = Field(None, alias="brand")
    min_price: Optional[Decimal] = Field(None, q='price__gte')
    max_price: Optional[Decimal] = Field(None, q='price__lte')
    in_stock: Optional[bool] = Field(None)
    def filter_in_stock(self, value: bool) -> Q:
        return Q(stock__gt=0) if value else Q(stock=0)