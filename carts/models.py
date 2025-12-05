from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import F, Sum

from catalog.models import Product


class Coupon(models.Model):
    PERCENT = 'percent'
    AMOUNT = 'amount'
    DISCOUNT_TYPE_CHOICES = [
        (PERCENT, 'Percent'),
        (AMOUNT, 'Amount'),
    ]
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default=PERCENT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    @property
    def is_valid_now(self) -> bool:
        now = timezone.now()
        if not self.active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True

    def __str__(self) -> str:
        return self.code


class Cart(models.Model):
    STATUS_OPEN = 'open'
    STATUS_CHECKED_OUT = 'checked_out'
    STATUS_ABANDONED = 'abandoned'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_CHECKED_OUT, 'Checked out'),
        (STATUS_ABANDONED, 'Abandoned'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    # items = models.ManyToManyField(Product, through='CartItem')

    class Meta:
        # DB-level enforcement to prevent checked_out carts to have items is implemented via PostgreSQL triggers in a migration.
        # No Django CheckConstraint here because related-row checks are not supported by CHECK constraints.
        pass


    def subtotal(self):
        return sum(item.product.price * item.quantity for item in self.items.all())

    def discount_amount(self):
        coupon = self.coupon
        if not coupon or not coupon.is_valid_now:
            return 0
        subtotal = self.subtotal()
        if coupon.discount_type == Coupon.PERCENT:
            return subtotal * (coupon.amount / 100)
        return min(coupon.amount, subtotal)

    def total(self):
        return self.subtotal() - self.discount_amount()

    def __str__(self) -> str:
        return f"Cart #{self.pk} for {self.user}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="unique_cart_product"
            )
        ]

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product.name}"
