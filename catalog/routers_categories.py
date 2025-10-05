from django.http import Http404
from django.shortcuts import aget_object_or_404

from typing import List
from asgiref.sync import sync_to_async
from ninja import Router, PatchDict
from ninja_jwt.authentication import AsyncJWTAuth

from .models import Category
from .schemas import CategoryIn, CategoryOut

router = Router(tags=["categories"])


@router.get("/categories", response=List[CategoryOut])
async def list_categories(request):
    categories = await sync_to_async(list)(Category.objects.all().order_by("name"))
    return categories


@router.get("/categories/{category_id}", response=CategoryOut)
async def get_category(request, category_id:int):
    category = await aget_object_or_404(Category, id=category_id)
    return category


@router.post("/categories", auth=AsyncJWTAuth(), response=CategoryOut)
async def create_category(request, payload: CategoryIn):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    category = Category(name=payload.name, description=payload.description)
    await category.asave()
    return category


@router.put("/categories/{category_id}", auth=AsyncJWTAuth(), response=CategoryOut)
async def update_category(request, category_id: int, payload: PatchDict[CategoryIn]):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    category = await sync_to_async(Category.objects.filter(id=category_id).first)()
    if not category:
        raise Http404

    for attr, value in payload.items():
        setattr(category, attr, value)

    await category.asave()
    return category


@router.delete("/categories/{category_id}", auth=AsyncJWTAuth())
async def delete_category(request, category_id: int):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}

    category = await sync_to_async(Category.objects.filter(id=category_id).first)()
    if not category:
        raise Http404

    await category.adelete()
    return {"success": True}
