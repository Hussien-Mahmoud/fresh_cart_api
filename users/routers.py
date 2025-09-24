from typing import List
from asgiref.sync import sync_to_async
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.http import Http404
from .models import Address
from .schemas import AddressIn, AddressOut

router = Router(auth=JWTAuth(), tags=["addresses"])


@router.get("/addresses", response=List[AddressOut])
async def list_addresses(request):
    qs = Address.objects.filter(user=request.user).order_by("-is_default", "-created_at")
    addresses = await sync_to_async(list)(qs)
    return [AddressOut(
        id=a.id,
        line1=a.line1,
        line2=a.line2,
        city=a.city,
        state=a.state,
        postal_code=a.postal_code,
        country=a.country,
        is_default=a.is_default,
    ) for a in addresses]


@router.post("/addresses", response=AddressOut)
async def create_address(request, payload: AddressIn):
    a = Address(
        user=request.user,
        line1=payload.line1,
        line2=payload.line2 or "",
        city=payload.city,
        state=payload.state or "",
        postal_code=payload.postal_code,
        country=payload.country,
        is_default=bool(payload.is_default),
    )
    await sync_to_async(a.save)()
    return AddressOut(
        id=a.id,
        line1=a.line1,
        line2=a.line2,
        city=a.city,
        state=a.state,
        postal_code=a.postal_code,
        country=a.country,
        is_default=a.is_default,
    )


@router.put("/addresses/{address_id}", response=AddressOut)
async def update_address(request, address_id: int, payload: AddressIn):
    a = await sync_to_async(Address.objects.filter(pk=address_id, user=request.user).first)()
    if not a:
        raise Http404
    a.line1 = payload.line1
    a.line2 = payload.line2 or ""
    a.city = payload.city
    a.state = payload.state or ""
    a.postal_code = payload.postal_code
    a.country = payload.country
    a.is_default = bool(payload.is_default)
    await sync_to_async(a.save)()
    return AddressOut(
        id=a.id,
        line1=a.line1,
        line2=a.line2,
        city=a.city,
        state=a.state,
        postal_code=a.postal_code,
        country=a.country,
        is_default=a.is_default,
    )


@router.delete("/addresses/{address_id}")
async def delete_address(request, address_id: int):
    a = await sync_to_async(Address.objects.filter(pk=address_id, user=request.user).first)()
    if not a:
        raise Http404
    await sync_to_async(a.delete)()
    return {"success": True}
