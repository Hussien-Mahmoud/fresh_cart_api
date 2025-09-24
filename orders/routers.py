from typing import List
from asgiref.sync import sync_to_async
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.http import Http404
from decimal import Decimal
import stripe
from django.conf import settings

from .models import Order, OrderItem
from .schemas import OrderCreateIn, OrderOut, OrderItemOut

from carts.models import Cart
from payments.models import Payment

from payments.schemas import StripeCheckoutOut

router = Router(auth=JWTAuth(), tags=["orders"])


async def serialize_order(order: Order) -> OrderOut:
    items = await sync_to_async(list)(order.items.all())
    return OrderOut(
        id=order.id,
        status=order.status,
        total_amount=order.total_amount,
        address_id=order.address_id,
        coupon_code=order.coupon.code if order.coupon_id else None,
        items=[
            OrderItemOut(
                product_id=it.product_id,
                product_name=it.product_name,
                quantity=it.quantity,
                unit_price=it.unit_price,
                line_total=it.unit_price * it.quantity,
            )
            for it in items
        ],
    )


@router.post("/orders", response=OrderOut)
async def create_order(request, payload: OrderCreateIn):
    cart = await sync_to_async(Cart.objects.select_related("coupon").filter(user=request.user, status=Cart.STATUS_OPEN).first)()
    if not cart:
        return 400, {"detail": "No open cart found"}

    # Calculate totals
    subtotal = cart.subtotal()
    discount = cart.discount_amount()
    total = cart.total()

    # Create order
    order = Order(
        user=request.user,
        address_id=payload.address_id,
        status=Order.STATUS_PENDING,
        total_amount=Decimal(total),
        coupon=cart.coupon,
    )
    await sync_to_async(order.save)()

    # Create order items
    items = await sync_to_async(list)(cart.items.select_related("product").all())
    for ci in items:
        oi = OrderItem(
            order=order,
            product=ci.product,
            product_name=ci.product.name,
            quantity=ci.quantity,
            unit_price=ci.unit_price,
        )
        await sync_to_async(oi.save)()

    # Mark cart as checked out
    cart.status = Cart.STATUS_CHECKED_OUT
    await sync_to_async(cart.save)()

    return await serialize_order(order)


@router.get("/orders", response=List[OrderOut])
async def list_orders(request):
    qs = Order.objects.filter(user=request.user).order_by("-created_at")
    orders = await sync_to_async(list)(qs)
    result: List[OrderOut] = []
    for order in orders:
        result.append(await serialize_order(order))
    return result


@router.get("/orders/{order_id}", response=OrderOut)
async def get_order(request, order_id: int):
    order = await sync_to_async(Order.objects.filter(pk=order_id, user=request.user).first)()
    if not order:
        raise Http404
    return await serialize_order(order)


@router.post("/orders/{order_id}/pay/stripe", response=StripeCheckoutOut)
async def pay_order_stripe(request, order_id: int):
    order = await sync_to_async(Order.objects.filter(pk=order_id, user=request.user).first)()
    if not order:
        raise Http404

    stripe.api_key = settings.STRIPE_SECRET_KEY

    line_items = []
    items = await sync_to_async(list)(order.items.all())
    for it in items:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': it.product_name,
                },
                'unit_amount': int(Decimal(it.unit_price) * 100),
            },
            'quantity': it.quantity,
        })

    success_url = 'https://example.com/success?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = 'https://example.com/cancel'

    session = await sync_to_async(stripe.checkout.Session.create)(
        mode='payment',
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={'order_id': str(order.id), 'user_id': str(request.user.id)},
    )

    order.stripe_session_id = session['id']
    await sync_to_async(order.save)()

    # Create Payment placeholder
    payment, _created = await sync_to_async(Payment.objects.get_or_create)(
        order=order,
        defaults={
            'amount': order.total_amount,
            'currency': 'usd',
            'status': 'created',
        }
    )

    return StripeCheckoutOut(checkout_url=session['url'], session_id=session['id'])
