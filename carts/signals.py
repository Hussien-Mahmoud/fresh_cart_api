from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Cart


@receiver(pre_save, sender=Cart, dispatch_uid="empty_cart_on_checkout")
def empty_cart_on_checkout(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_cart = Cart.objects.get(pk=instance.pk)
            if (
                old_cart.status != Cart.STATUS_CHECKED_OUT
                and instance.status == Cart.STATUS_CHECKED_OUT
            ):
                instance.items.all().delete()
                instance.coupon = None
        except Cart.DoesNotExist:
            pass