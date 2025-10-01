# todo: not filtered
from typing import List
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.contrib.auth import get_user_model

from .models import Address
from .schemas import AddressIn, AddressOut

router = Router(tags=["Addresses"], auth=JWTAuth())


@router.post("/addresses", response=AddressOut)
def create_address(request, payload: AddressIn):
    user = request.user
    address = Address.objects.create(user=user, **payload.dict())
    # Ensure only one default address
    if address.is_default:
        Address.objects.filter(user=user).exclude(id=address.id).update(is_default=False)
    return AddressOut(**{**payload.dict(), "id": address.id})


@router.put("/addresses/{address_id}", response=AddressOut)
def update_address(request, address_id: int, payload: AddressIn):
    user = request.user
    address = get_object_or_404(Address, id=address_id, user=user)
    for field, value in payload.dict().items():
        setattr(address, field, value)
    address.save()
    if address.is_default:
        Address.objects.filter(user=user).exclude(id=address.id).update(is_default=False)
    return AddressOut(
        id=address.id,
        line1=address.line1,
        line2=address.line2,
        city=address.city,
        state=address.state,
        postal_code=address.postal_code,
        country=address.country,
        is_default=address.is_default,
    )


@router.delete("/addresses/{address_id}")
def delete_address(request, address_id: int):
    user = request.user
    address = get_object_or_404(Address, id=address_id, user=user)
    address.delete()
    return {"success": True}


@router.post("/addresses/{address_id}/set-default")
def set_default_address(request, address_id: int):
    user = request.user
    address = get_object_or_404(Address, id=address_id, user=user)
    Address.objects.filter(user=user).update(is_default=False)
    address.is_default = True
    address.save(update_fields=["is_default"])
    return {"success": True}
