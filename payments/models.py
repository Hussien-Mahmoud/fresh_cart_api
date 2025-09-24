from django.db import models
from orders.models import Order


class Payment(models.Model):
    PROVIDER_STRIPE = 'stripe'

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    provider = models.CharField(max_length=50, default=PROVIDER_STRIPE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='usd')
    status = models.CharField(max_length=50, default='created')
    payment_intent_id = models.CharField(max_length=255, blank=True)
    charge_id = models.CharField(max_length=255, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Payment for Order #{self.order_id} - {self.status}"
