from typing import List
from asgiref.sync import sync_to_async
from ninja import Router
from ninja_jwt.authentication import AsyncJWTAuth
from django.http import Http404
from django.db import models
from .models import Product, Category, Brand, ProductImage
from .schemas import ProductIn, ProductOut

router = Router(tags=["products"])


@router.get("/products", response=List[ProductOut])
async def list_products(request):
    qs = await sync_to_async(Product.objects.filter(is_active=True)
                             .select_related("category", "brand")
                             .prefetch_related("images", "ratings")
                             .annotate(average_rating=models.Avg("ratings__rating"))
                             .order_by)("-created_at")
    if qs.exists():
        return []
    return qs


@router.get("/products/{slug}", response=ProductOut)
async def get_product(request, slug: str):
    p = await sync_to_async(Product.objects.filter(slug=slug)
                            .select_related("category", "brand")
                            .prefetch_related("images", "ratings")
                            .annotate(average_rating=models.Avg("ratings__rating"))
                            .first)()
    if not p:
        raise Http404
    return p


# todo: add images upload (for cover and product images)
@router.post("/products", auth=AsyncJWTAuth(), response=ProductOut)
async def create_product(request, payload: ProductIn):
    print(payload)
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}
    category=None
    if payload.category:
        category = await sync_to_async(Category.objects.get)(pk=payload.category)

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
@router.put("/products/{slug}", auth=AsyncJWTAuth(), response=ProductOut)
async def update_product(request, slug: str, payload: ProductIn):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    product = await sync_to_async(Product.objects.filter(slug=slug).first)()
    if not product:
        raise Http404

    # create or get category
    category = None
    if payload.category:
        category = await Category.objects.aget_or_create(name=payload.category.name, slug=payload.category.slug)
    product.category = category


    # product.name = payload.name
    # product.description = payload.description or ""
    # product.price = payload.price
    # product.stock = payload.stock
    # product.category_id = payload.category_id
    # product.brand_id = payload.brand_id
    await sync_to_async(product.save)()
    return await get_product(request, product.id)


@router.delete("/products/{slug}", auth=AsyncJWTAuth())
async def delete_product(request, slug: str):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    product = await sync_to_async(Product.objects.filter(slug=slug).first)()
    if not product:
        raise Http404

    await sync_to_async(product.delete)()
    return {"success": True}
