from django.http import Http404
from django.shortcuts import aget_object_or_404

from typing import List, Optional
from asgiref.sync import sync_to_async
from ninja import Router, PatchDict, UploadedFile, Form, File
from ninja_jwt.authentication import AsyncJWTAuth

from .models import Brand
from .schemas import BrandIn, BrandOut

router = Router(tags=["brands"])


@router.get("/brands", response=List[BrandOut])
async def list_brands(request):
    brands = await sync_to_async(list)(Brand.objects.all().order_by("-updated_at"))
    return brands


@router.get("/brands/{brand_id}", response=BrandOut)
async def get_brand(request, brand_id: int):
    brand = await aget_object_or_404(Brand, id=brand_id)
    return brand


@router.post("/brands", auth=AsyncJWTAuth(), response=BrandOut)
async def create_brand(request, payload: BrandIn, image: File[UploadedFile] = None):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    brand = Brand(name=payload.name, image=image)
    await brand.asave()
    return brand


@router.put("/brands/{brand_id}", auth=AsyncJWTAuth(), response=BrandOut)
async def update_brand(request, brand_id: int, payload: PatchDict[BrandIn], image: File[UploadedFile] = None):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    brand = await sync_to_async(Brand.objects.filter(id=brand_id).first)()
    if not brand:
        raise Http404

    for attr, value in payload.items():
        setattr(brand, attr, value)

    if image:
        if brand.image:
            await sync_to_async(brand.image.delete)()
        brand.image = image

    await brand.asave()
    return brand


@router.delete("/brands/{brand_id}", auth=AsyncJWTAuth())
async def delete_brand(request, brand_id: int):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    brand = await sync_to_async(Brand.objects.filter(id=brand_id).first)()
    if not brand:
        raise Http404

    await brand.adelete()
    return {"success": True}
