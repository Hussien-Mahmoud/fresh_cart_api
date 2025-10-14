from typing import List
from asgiref.sync import sync_to_async

from django.http import Http404
from django.shortcuts import aget_object_or_404
from django.contrib.auth import get_user_model

from ninja import Router, PatchDict
from ninja_jwt.authentication import AsyncJWTAuth

from .models import Address
from .schemas import AddressIn, AddressOut

router = Router(tags=["Addresses"], auth=AsyncJWTAuth())


@router.get("/addresses", response=List[AddressOut])
async def get_user_addresses(request):
    """Get all addresses for the authenticated user"""
    user = request.user
    addresses = Address.objects.filter(user=user).all()
    return await sync_to_async(list)(addresses)


@router.post("/addresses", response=AddressOut)
async def create_address(request, payload: AddressIn):
    """Create a new address for the authenticated user"""
    user = request.user
    address = await Address.objects.acreate(user=user, **payload.dict())
    # Ensure only one default address
    if address.is_default:
        await Address.objects.filter(user=user).exclude(id=address.id).aupdate(is_default=False)
    return address


@router.put("/addresses/{address_id}", response=AddressOut)
async def update_address(request, address_id: int, payload: PatchDict[AddressIn]):
    """Update an existing address for the authenticated user"""
    user = request.user
    try:
        address = await Address.objects.aget(id=address_id, user=user)
    except Address.DoesNotExist:
        raise Http404("Address not found")

    for field, value in payload.items():
        setattr(address, field, value)
    await address.asave(force_update=True)
    return address


@router.delete("/addresses/{address_id}")
async def delete_address(request, address_id: int):
    """Delete an address for the authenticated user"""
    user = request.user
    try:
        address = await Address.objects.aget(id=address_id, user=user)
    except Address.DoesNotExist:
        raise Http404("Address not found")
    await address.adelete()
    return {"success": True}


@router.post("/addresses/{address_id}/set-default")
async def set_default_address(request, address_id: int):
    """Set an address as the default address for the authenticated user"""
    user = request.user
    try:
        address = await Address.objects.aget(id=address_id, user=user)
    except Address.DoesNotExist:
        raise Http404("Address not found")
    await Address.objects.filter(user=user).aupdate(is_default=False)
    address.is_default = True
    await address.asave(update_fields=["is_default"])
    return {"success": True}
