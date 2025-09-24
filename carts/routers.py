from typing import List
from asgiref.sync import sync_to_async
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.http import Http404
from decimal import Decimal
from catalog.models import Product
from .models import CartItem
from .schemas import CartItemIn, CartOut, CartItemOut, CouponIn
from .utils import get_or_create_open_cart, apply_coupon_to_cart

router = Router(auth=JWTAuth(), tags=["cart"])


async def serialize_cart(cart) -> CartOut:
    items = await sync_to_async(list)(cart.items.select_related("product").all())
    item_schemas: List[CartItemOut] = []
    for it in items:
        line_total = it.unit_price * it.quantity
        item_schemas.append(CartItemOut(
            product_id=it.product_id,
            product_name=it.product.name,
            quantity=it.quantity,
            unit_price=it.unit_price,
            line_total=line_total,
        ))
    subtotal = cart.subtotal()
    discount = cart.discount_amount()
    total = cart.total()
    return CartOut(
        id=cart.id,
        items=item_schemas,
        subtotal=Decimal(subtotal),
        discount=Decimal(discount),
        total=Decimal(total),
        coupon=cart.coupon.code if cart.coupon_id else None,
    )


@router.get("/cart", response=CartOut)
async def get_cart(request):
    cart = await get_or_create_open_cart(request.user)
    return await serialize_cart(cart)


@router.post("/cart/add", response=CartOut)
async def add_to_cart(request, payload: CartItemIn):
    cart = await get_or_create_open_cart(request.user)
    product = await sync_to_async(Product.objects.filter(pk=payload.product_id, is_active=True).first)()
    if not product:
        raise Http404
    item = await sync_to_async(CartItem.objects.filter(cart=cart, product=product).first)()
    if item:
        item.quantity += payload.quantity
        await sync_to_async(item.save)()
    else:
        item = CartItem(cart=cart, product=product, quantity=payload.quantity, unit_price=product.price)
        await sync_to_async(item.save)()
    return await serialize_cart(cart)


@router.post("/cart/update", response=CartOut)
async def update_cart_item(request, payload: CartItemIn):
    cart = await get_or_create_open_cart(request.user)
    item = await sync_to_async(CartItem.objects.filter(cart=cart, product_id=payload.product_id).first)()
    if not item:
        raise Http404
    if payload.quantity <= 0:
        await sync_to_async(item.delete)()
    else:
        item.quantity = payload.quantity
        await sync_to_async(item.save)()
    return await serialize_cart(cart)


@router.post("/cart/remove", response=CartOut)
async def remove_from_cart(request, payload: CartItemIn):
    cart = await get_or_create_open_cart(request.user)
    item = await sync_to_async(CartItem.objects.filter(cart=cart, product_id=payload.product_id).first)()
    if item:
        await sync_to_async(item.delete)()
    return await serialize_cart(cart)


@router.post("/cart/apply-coupon", response=CartOut)
async def apply_coupon(request, payload: CouponIn):
    cart = await get_or_create_open_cart(request.user)
    await apply_coupon_to_cart(cart, payload.code)
    return await serialize_cart(cart)
