from typing import List
from asgiref.sync import sync_to_async
from ninja import Router, PatchDict
from ninja_jwt.authentication import AsyncJWTAuth
from ninja.pagination import paginate
from ninja.decorators import decorate_view

from django.http import Http404
from django.db import models
from django.core.cache import cache
from django.views.decorators.cache import cache_page

from .models import Product, Category, Brand, ProductImage
from .schemas import ProductIn, ProductOut

router = Router(tags=["products"])


@router.get("/products", response=List[ProductOut])
@paginate
# @decorate_view(cache_page(1 * 60))
async def list_products(request):
    # WARNING: cache is not fully working yet and only experimental
    cached_products = cache.get("products")
    if cached_products:
        return cached_products

    qs = Product.objects.filter(is_active=True) \
                        .select_related("category", "brand") \
                        .prefetch_related("images", "ratings") \
                        .annotate(average_rating=models.Avg("ratings__rating")) \
                        .order_by("-created_at")

    products = await sync_to_async(list)(qs)
    cache.set("products", products, 1 * 60)
    return products
    # return qs   # if no cache

@router.get("/products/{product_id}", response=ProductOut)
async def get_product(request, product_id: int):
    qs = Product.objects.filter(id=product_id).select_related("category", "brand").prefetch_related("images", "ratings").annotate(average_rating=models.Avg("ratings__rating"))
    p = await sync_to_async(qs.first)()
    if not p:
        raise Http404
    return p


# todo: add images upload (for cover and product images)
@router.post("/products", auth=AsyncJWTAuth(), response=ProductOut)
async def create_product(request, payload: PatchDict[ProductIn]):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    # Handle category
    category = None
    if payload.category:
        category = await sync_to_async(Category.objects.get)(pk=payload.category)

    # Handle brand
    brand = None
    if payload.brand:
        brand = await sync_to_async(Brand.objects.get)(pk=payload.brand)

    product = Product(
        name=payload.name,
        description=payload.description or "",
        price=payload.price,
        stock=payload.stock,
        is_active=payload.is_active,
        category=category,
        brand=brand,
    )
    await sync_to_async(product.save)()
    return await get_product(request, product.id)


# todo: add images upload (for cover and product images)
@router.put("/products/{product_id}", auth=AsyncJWTAuth(), response=ProductOut)
async def update_product(request, product_id: int, payload: ProductIn):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    product = await sync_to_async(Product.objects.filter(id=product_id).first)()
    if not product:
        raise Http404

    # Update product fields
    product.name = payload.name
    product.description = payload.description or ""
    product.price = payload.price
    product.stock = payload.stock
    product.is_active = payload.is_active

    # Handle category
    category = None
    if payload.category:
        category = await sync_to_async(Category.objects.get_or_create)(name=payload.category.name)
        category = category[0] if isinstance(category, tuple) else category
    product.category = category

    # Handle brand
    brand = None
    if payload.brand:
        brand = await sync_to_async(Brand.objects.get_or_create)(name=payload.brand.name)
        brand = brand[0] if isinstance(brand, tuple) else brand
    product.brand = brand


    # product.name = payload.name
    # product.description = payload.description or ""
    # product.price = payload.price
    # product.stock = payload.stock
    # product.category_id = payload.category_id
    # product.brand_id = payload.brand_id
    await sync_to_async(product.save)()
    return await get_product(request, product.id)


@router.delete("/products/{product_id}", auth=AsyncJWTAuth())
async def delete_product(request, product_id: int):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    product = await sync_to_async(Product.objects.filter(id=product_id).first)()
    if not product:
        raise Http404

    await sync_to_async(product.delete)()
    return {"success": True}
