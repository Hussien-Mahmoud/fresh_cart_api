from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from carts.models import Coupon
from .payments import CouponManageable


@receiver(post_save, sender=Coupon, dispatch_uid="sync_with_payment_methods_on_create")
def sync_with_payment_methods_on_create(sender, instance, created, **kwargs):
    if created:
        for Manageable in CouponManageable.__subclasses__():
            Manageable.add_coupon(instance)

@receiver(post_save, sender=Coupon, dispatch_uid="sync_with_payment_methods_on_update")
def sync_with_payment_methods_on_update(sender, instance, created, **kwargs):
    if not created:
        for Manageable in CouponManageable.__subclasses__():
            Manageable.remove_coupon(instance)
            Manageable.add_coupon(instance)


@receiver(post_delete, sender=Coupon, dispatch_uid="sync_with_payment_methods_on_delete")
def sync_with_payment_methods_on_delete(sender, instance, **kwargs):
    for Manageable in CouponManageable.__subclasses__():
        Manageable.remove_coupon(instance)
