from typing import List
from asgiref.sync import sync_to_async
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.http import Http404
from .models import Product, Category, Brand
from .schemas import ProductIn, ProductOut

router = Router(tags=["products"])


@router.get("/products", response=List[ProductOut])
async def list_products(request):
    qs = Product.objects.filter(is_active=True).select_related("category", "brand").order_by("name")
    products = await sync_to_async(list)(qs)
    return [ProductOut(
        id=p.id,
        name=p.name,
        slug=p.slug,
        description=p.description,
        price=p.price,
        stock=p.stock,
        is_active=p.is_active,
        category_id=p.category_id,
        brand_id=p.brand_id,
        image_url=p.image_url,
    ) for p in products]


@router.get("/products/{product_id}", response=ProductOut)
async def get_product(request, product_id: int):
    p = await sync_to_async(Product.objects.filter(pk=product_id).first)()
    if not p:
        raise Http404
    return ProductOut(
        id=p.id,
        name=p.name,
        slug=p.slug,
        description=p.description,
        price=p.price,
        stock=p.stock,
        is_active=p.is_active,
        category_id=p.category_id,
        brand_id=p.brand_id,
        image_url=p.image_url,
    )


@router.post("/products", auth=JWTAuth(), response=ProductOut)
async def create_product(request, payload: ProductIn):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}
    category = await sync_to_async(Category.objects.get)(pk=payload.category_id)
    brand = None
    if payload.brand_id:
        brand = await sync_to_async(Brand.objects.get)(pk=payload.brand_id)
    product = Product(
        name=payload.name,
        description=payload.description or "",
        price=payload.price,
        stock=payload.stock,
        category=category,
        brand=brand,
        image_url=payload.image_url or "",
    )
    await sync_to_async(product.save)()
    return await get_product(request, product.id)


@router.put("/products/{product_id}", auth=JWTAuth(), response=ProductOut)
async def update_product(request, product_id: int, payload: ProductIn):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}
    product = await sync_to_async(Product.objects.filter(pk=product_id).first)()
    if not product:
        raise Http404
    product.name = payload.name
    product.description = payload.description or ""
    product.price = payload.price
    product.stock = payload.stock
    product.category_id = payload.category_id
    product.brand_id = payload.brand_id
    product.image_url = payload.image_url or ""
    await sync_to_async(product.save)()
    return await get_product(request, product.id)


@router.delete("/products/{product_id}", auth=JWTAuth())
async def delete_product(request, product_id: int):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}
    product = await sync_to_async(Product.objects.filter(pk=product_id).first)()
    if not product:
        raise Http404
    await sync_to_async(product.delete)()
    return {"success": True}