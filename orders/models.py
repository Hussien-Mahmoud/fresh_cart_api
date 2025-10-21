from django.conf import settings
from django.db import models
from django.db.models import F, Sum

from users.models import Address
from carts.models import Coupon
from catalog.models import Product


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELED = 'canceled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELED, 'Canceled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    address_text = models.TextField(null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    coupon_code = models.CharField(max_length=50, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    stripe_session_id = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(address__isnull=False) | models.Q(address_text__isnull=False),
                name='address_reference_or_address_text_required'
            )
        ]
        ordering = ['-created_at']

    def items_total(self):
        return OrderItem.objects.filter(order=self).aggregate(total=Sum(F('unit_price') * F('quantity'), default=0))['total']

    def total(self):
        return self.items_total() - self.discount_amount

    def __str__(self) -> str:
        return f"Order #{self.pk} - {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product_name}"
