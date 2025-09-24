from typing import List
from asgiref.sync import sync_to_async
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.http import Http404
from .models import Brand
from .schemas import BrandIn, BrandOut

router = Router(tags=["brands"])


@router.get("/brands", response=List[BrandOut])
async def list_brands(request):
    brands = await sync_to_async(list)(Brand.objects.all().order_by("name"))
    return [BrandOut(id=b.id, name=b.name, slug=b.slug) for b in brands]


@router.post("/brands", auth=JWTAuth(), response=BrandOut)
async def create_brand(request, payload: BrandIn):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}
    b = Brand(name=payload.name)
    await sync_to_async(b.save)()
    return BrandOut(id=b.id, name=b.name, slug=b.slug)


@router.put("/brands/{brand_id}", auth=JWTAuth(), response=BrandOut)
async def update_brand(request, brand_id: int, payload: BrandIn):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}
    b = await sync_to_async(Brand.objects.filter(pk=brand_id).first)()
    if not b:
        raise Http404
    b.name = payload.name
    await sync_to_async(b.save)()
    return BrandOut(id=b.id, name=b.name, slug=b.slug)


@router.delete("/brands/{brand_id}", auth=JWTAuth())
async def delete_brand(request, brand_id: int):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}
    b = await sync_to_async(Brand.objects.filter(pk=brand_id).first)()
    if not b:
        raise Http404
    await sync_to_async(b.delete)()
    return {"success": True}
