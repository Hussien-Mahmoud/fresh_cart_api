from asgiref.sync import sync_to_async
from ninja import Router
from ninja_jwt.authentication import AsyncJWTAuth
from django.conf import settings
import stripe

from base.schemas import ErrorSchema
from carts.models import Coupon
from .models import Payment
from orders.models import Order
from .schemas import StripeCheckoutOut, WebhookOut

router = Router(tags=["payments"])

@router.post("/payments/stripe/order/{order_id}", auth=AsyncJWTAuth(), response={200: StripeCheckoutOut, 400: ErrorSchema, 404: ErrorSchema})
async def pay_order_stripe(request, order_id: int):

    # 1. Validates the order exists and belongs to the authenticated user and not paid yet
    order = await Order.objects.filter(pk=order_id, user=request.user).select_related("address").prefetch_related("items", "items__product").afirst()
    if not order:
        return 404, {"detail": "Order not found"}

    if order.status != Order.STATUS_PENDING:
        return 400, {"detail": "Order is not to be paid"}


    # 2. Retrieves all order items with their associated product information and images for stripe
    items = await sync_to_async(list)(order.items.all().select_related("product").prefetch_related("product__images"))
    line_items = [{
        'price_data': {
            'currency': settings.CURRENCY,
            'product_data': {
                'name': item.product_name,
                'images': [image.image.url for image in item.product.images.all()][:8] if item.product else []
            },
            'unit_amount_decimal': item.unit_price * 100,
        },
        'quantity': item.quantity,
    } for item in items]
    print(line_items)


    # 3. Applies coupon discount if found
    if order.coupon_code:
        try:
            coupon = await Coupon.objects.aget(code=order.coupon_code)
            coupon_id = coupon.id
        except Coupon.DoesNotExist:
            return 400, {"detail": "Coupon not found"}
    else:
        coupon_id = None


    # 4. Creates a Stripe Checkout session with customer information and metadata
    success_url = 'https://example.com/success?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = 'https://example.com/cancel'

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = await sync_to_async(stripe.checkout.Session.create)(
        mode='payment',
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=request.user.email,
        discounts=[{"coupon": coupon_id}] if coupon_id else None,
        metadata={'order_id': str(order.id), 'user_id': str(order.user_id)},
    )

    # 5. Stores the Stripe session ID on the order for tracking
    order.stripe_session_id = session['id']
    await order.asave()

    # 6. Creates or retrieves a Payment record in 'created' status as a placeholder
    # Create Payment placeholder
    payment, _created = await Payment.objects.aget_or_create(
        order=order,
        defaults={
            'amount': order.total,
            'currency': settings.CURRENCY,
            'status': 'created',
        }
    )

    # 7. Returns the checkout URL and session ID for client-side redirect
    return StripeCheckoutOut(checkout_url=session['url'], session_id=session['id'])


@router.post("/payments/stripe/webhook", response=WebhookOut)
async def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=endpoint_secret
        )
    except ValueError:
        return 400, {"message": "Invalid payload"}
    except stripe.error.SignatureVerificationError:
        return 400, {"message": "Invalid signature"}

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.get('metadata', {}).get('order_id')
        payment_intent = session.get('payment_intent')
        checkout_id = session.get('id')

        if order_id:
            order = await Order.objects.filter(pk=order_id).select_related("address").prefetch_related("items", "items__product").afirst()
            if not order:
                return 404, {"message": "Order not found"}

            if order.stripe_session_id != checkout_id:
                return 400, {"message": "Checkout session not updated"}

            if order.status == Order.STATUS_PENDING:
                order.status = Order.STATUS_PAID
                await order.asave()
                payment, created = await Payment.objects.aget_or_create(
                    order=order,
                    defaults={
                        'amount': order.total,
                        'currency': settings.CURRENCY,
                        'status': 'succeeded',
                        'payment_intent_id': payment_intent or '',
                        'raw_response': event,
                    }
                )
                if not created:
                    payment.status = 'succeeded'
                    payment.payment_intent_id = payment_intent or ''
                    payment.raw_response = event
                    await payment.asave()
            elif order.status == Order.STATUS_PAID:
                return 400, {"message": "Order is already paid"}
            else:
                return 400, {"message": "Order is not pending"}

    return 200, {"message": "Success"}
