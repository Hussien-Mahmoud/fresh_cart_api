from asgiref.sync import sync_to_async
from typing import List
from decimal import Decimal

from django.http import Http404
from django.db.models import Avg, F

from ninja import Router
from ninja_jwt.authentication import AsyncJWTAuth

from catalog.models import Product
from .models import CartItem, Cart
from .utils import get_or_create_open_cart, apply_coupon_to_cart
from .schemas import CartItemIn, CartOut, CartItemOut, CouponIn, CouponOut
from catalog.schemas import ProductOut

router = Router(auth=AsyncJWTAuth(), tags=["cart"])


async def serialize_cart(cart) -> CartOut:
    # getting items scheme
    items = await sync_to_async(list)(
        CartItem.objects.filter(cart=cart).prefetch_related("product", "product__images", "product__ratings")
        .select_related(
            'product__category', 'product__brand'
        )
        .annotate(avarage_rating=Avg("product__ratings__rating"))
        .annotate(line_total=F("product__price") * F("quantity"))
    )

    # item_schemas: List[CartItemOut] = []
    # for item in items:
    #     line_total = item.product.price * item.quantity
    #     item_schemas.append(CartItemOut(
    #         product=ProductOut(item.product),
    #         quantity=int(item.quantity),
    #         line_total=Decimal(line_total),
    #     ))
    subtotal = await sync_to_async(cart.subtotal)()
    discount = await sync_to_async(cart.discount_amount)()
    total = await sync_to_async(cart.total)()
    cart_schema = CartOut(
        id=cart.id,
        items=items,
        subtotal=Decimal(subtotal),
        discount=Decimal(discount),
        total=Decimal(total),
        coupon=cart.coupon,
    )
    return cart_schema


@router.get("/cart", response=CartOut)
async def get_cart(request):
    cart = await get_or_create_open_cart(request.user)
    return await serialize_cart(cart)


@router.post("/cart", response=CartOut)
async def add_to_cart(request, payload: CartItemIn):
    cart = await get_or_create_open_cart(request.user)
    product = await sync_to_async(Product.objects.filter(pk=payload.product_id, is_active=True).first)()
    if not product:
        raise Http404
    item = await sync_to_async(CartItem.objects.filter(cart=cart, product=product).first)()
    if item:
        item.quantity += payload.quantity
        await item.asave()
    else:
        item = CartItem(cart=cart, product=product, quantity=payload.quantity)
        await item.asave()
    return await serialize_cart(cart)


@router.put("/cart", response=CartOut)
async def update_cart_item(request, payload: CartItemIn):
    cart = await get_or_create_open_cart(request.user)
    product = await sync_to_async(Product.objects.filter(pk=payload.product_id, is_active=True).first)()
    if not product:
        raise Http404
    item = await sync_to_async(CartItem.objects.filter(cart=cart, product=product).first)()
    if not item:
        raise Http404

    if payload.quantity <= 0:
        await item.adelete()
    else:
        item.quantity = payload.quantity
        await item.asave()
    return await serialize_cart(cart)


@router.delete("/cart", response=CartOut)
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
