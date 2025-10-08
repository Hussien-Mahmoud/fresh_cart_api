from asgiref.sync import sync_to_async
from .models import Cart, Coupon


async def get_or_create_open_cart(user):
    cart = await Cart.objects.filter(user=user).afirst()
    if cart:
        if cart.status != Cart.STATUS_OPEN:
            cart.status = Cart.STATUS_OPEN
            await cart.asave()
        return cart
    return await Cart.objects.acreate(user=user)


async def apply_coupon_to_cart(cart: Cart, code: str):
    coupon = await sync_to_async(Coupon.objects.filter(code__iexact=code).first)()
    if not coupon or not coupon.is_valid_now:
        return None
    cart.coupon = coupon
    await cart.asave()
    return coupon