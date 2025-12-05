from asgiref.sync import sync_to_async
from ninja import Router
from django.conf import settings
import stripe

from .models import Payment
from orders.models import Order

router = Router(tags=["payments"])


@router.post("/payments/stripe/webhook")
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
        return 400, {"detail": "Invalid payload"}
    except stripe.error.SignatureVerificationError:
        return 400, {"detail": "Invalid signature"}

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.get('metadata', {}).get('order_id')
        payment_intent = session.get('payment_intent')

        if order_id:
            order = await sync_to_async(Order.objects.filter(pk=order_id).first)()
            if order and order.status != Order.STATUS_PAID:
                order.status = Order.STATUS_PAID
                await sync_to_async(order.save)()
                payment, created = await sync_to_async(Payment.objects.get_or_create)(
                    order=order,
                    defaults={
                        'amount': order.total_amount,
                        'currency': 'usd',
                        'status': 'succeeded',
                        'payment_intent_id': payment_intent or '',
                        'raw_response': event,
                    }
                )
                if not created:
                    payment.status = 'succeeded'
                    payment.payment_intent_id = payment_intent or ''
                    payment.raw_response = event
                    await sync_to_async(payment.save)()

    return {"received": True}
