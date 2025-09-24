from typing import List
from asgiref.sync import sync_to_async
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.http import Http404
from .models import Category
from .schemas import CategoryIn, CategoryOut

router = Router(tags=["categories"])


@router.get("/categories", response=List[CategoryOut])
async def list_categories(request):
    cats = await sync_to_async(list)(Category.objects.all().order_by("name"))
    return [CategoryOut(id=c.id, name=c.name, slug=c.slug, description=c.description) for c in cats]


@router.post("/categories", auth=JWTAuth(), response=CategoryOut)
async def create_category(request, payload: CategoryIn):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}
    c = Category(name=payload.name, description=payload.description or "")
    await sync_to_async(c.save)()
    return CategoryOut(id=c.id, name=c.name, slug=c.slug, description=c.description)


@router.put("/categories/{category_id}", auth=JWTAuth(), response=CategoryOut)
async def update_category(request, category_id: int, payload: CategoryIn):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}
    c = await sync_to_async(Category.objects.filter(pk=category_id).first)()
    if not c:
        raise Http404
    c.name = payload.name
    c.description = payload.description or ""
    await sync_to_async(c.save)()
    return CategoryOut(id=c.id, name=c.name, slug=c.slug, description=c.description)


@router.delete("/categories/{category_id}", auth=JWTAuth())
async def delete_category(request, category_id: int):
    if not request.user.is_staff:
        return 403, {"detail": "Forbidden"}
    c = await sync_to_async(Category.objects.filter(pk=category_id).first)()
    if not c:
        raise Http404
    await sync_to_async(c.delete)()
    return {"success": True}
