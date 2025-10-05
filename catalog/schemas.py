from typing import Optional
from typing import List
from ninja import Schema, ModelSchema
from decimal import Decimal
from ninja.orm import create_schema

from catalog.models import Product, ProductImage, ProductRating, Category, Brand


# Category
class CategoryIn(ModelSchema):
    class Meta:
        model = Category
        fields = ['name', 'description']


class CategoryOut(ModelSchema):
    class Meta:
        model = Category
        fields = ['id','name', 'slug', 'description']


# Brand
class BrandIn(ModelSchema):
    class Meta:
        model = Brand
        fields = ['name']


class BrandOut(ModelSchema):
    class Meta:
        model = Brand
        fields = ['id','name', 'slug', 'image', 'created_at', 'updated_at']


# Product images
class ProductImageOut(Schema):
    image_url: str


# Product rating
class ProductRatingIn(ModelSchema):
    product_id: int
    class Meta:
        model = ProductRating
        fields = ['rating', 'comment']


class ProductRatingOut(ModelSchema):
    class Meta:
        model = ProductRating
        fields = ['rating', 'comment']


# Product
class ProductIn(ModelSchema):
    category: Optional[CategoryIn] = None
    brand: Optional[BrandIn] = None
    # images: List[ProductImageOut] = []
    # ratings: List[ProductRatingOut] = []
    class Meta:
        model = Product
        exclude = ['id', 'created_at', 'updated_at', 'slug']


class ProductOut(ModelSchema):
    category: Optional[CategoryOut] = None
    brand: Optional[BrandOut] = None
    images: List[ProductImageOut] = []
    ratings: List[ProductRatingOut] = []
    average_rating: Optional[float] = None

    class Meta:
        model = Product
        fields = "__all__"
