from typing import List, Optional
from asgiref.sync import sync_to_async
from ninja import Router
from ninja_jwt.authentication import AsyncJWTAuth
from django.http import Http404
from decimal import Decimal

from .models import Order, OrderItem
from .schemas import OrderCreateIn, OrderOut, OrderItemOut

from carts.models import Cart
from users.models import Address

from base.schemas import ErrorSchema

router = Router(auth=AsyncJWTAuth(), tags=["orders"])


async def serialize_order(order: Order) -> OrderOut:
    items = await sync_to_async(list)(order.items.all())
    return OrderOut(
        id=order.id,
        status=order.status,
        total_amount=order.total,
        address=order.address,
        address_text=order.address.get_formatted_address(),
        coupon_code=order.coupon_code,
        discount_amount=order.discount_amount,
        items=[
            OrderItemOut(
                product_id=it.product_id,
                product_name=it.product_name,
                quantity=it.quantity,
                unit_price=it.unit_price,
                line_total=it.line_total,
            )
            for it in items
        ],
    )


@router.get("/orders", response=List[OrderOut])
async def list_orders(request):
    qs = Order.objects.filter(user=request.user).select_related("address").prefetch_related("items", "items__product")
    orders = await sync_to_async(list)(qs)
    result: List[OrderOut] = []
    for order in orders:
        result.append(await serialize_order(order))
    return result


@router.post("/orders", response={200: OrderOut, 400: ErrorSchema})
async def create_order(request, payload: Optional[OrderCreateIn] = None):

    # get the cart corresponding to the user
    cart = await (Cart.objects
                  .select_related("coupon")
                  .prefetch_related('items', 'items__product')
                  .filter(user=request.user, status=Cart.STATUS_OPEN)
                  .afirst())
    if not cart:
        return 400, {"detail": "No open cart found"}

    # Calculate totals
    # subtotal = cart.subtotal()
    discount_amount = cart.discount_amount()
    total = cart.total()

    # checking coupon
    coupon_code = None
    if discount_amount > 0:
        coupon_code = cart.coupon.code

    if payload:
        if payload.address_id:
            address = await Address.objects.filter(id=payload.address_id, user=request.user).afirst()
            if not address:
                return 400, {"detail": f"User {request.user.username} has no address with this id"}
        else:
            address = await Address.objects.filter(is_default=True, user=request.user).afirst()
            if not address:
                return 400, {"detail": f"User {request.user.username} has no assigned addresses"}
    else:
        address = await Address.objects.filter(is_default=True, user=request.user).afirst()
        if not address:
            return 400, {"detail": f"User {request.user.username} has no assigned addresses"}


    # Create order
    order = Order(
        user=request.user,
        address=address,
        status=Order.STATUS_PENDING,
        coupon_code=coupon_code,
        discount_amount=discount_amount,
    )
    await order.asave()

    # Create order items
    items = await sync_to_async(list)(cart.items.select_related("product").all())
    order_items_objs = [
        OrderItem(
            order=order,
            product=cart_item.product,
            product_name=cart_item.product.name,
            unit_price=cart_item.product.price,
            quantity=cart_item.quantity,
        ) for cart_item in items
    ]

    await order.items.abulk_create(order_items_objs)

    # Mark cart as checked out
    cart.status = Cart.STATUS_CHECKED_OUT
    await cart.asave()

    # we need to prefetch the items
    order._prefetched_objects_cache = {"items": order_items_objs}
    return await serialize_order(order)


@router.get("/orders/{order_id}", response=OrderOut)
async def get_order(request, order_id: int):
    order = await Order.objects.filter(pk=order_id, user=request.user).select_related("address").prefetch_related("items", "items__product").afirst()
    if not order:
        raise Http404("Order not found")
    return await serialize_order(order)
