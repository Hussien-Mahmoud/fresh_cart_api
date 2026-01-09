from abc import ABC, abstractmethod
from typing import Protocol
import stripe

from django.conf import settings

from carts.models import Coupon


class CouponManageable(Protocol):
    @staticmethod
    def add_coupon(coupon: Coupon):
        ...

    @staticmethod
    def remove_coupon(coupon: Coupon):
        ...


class PaymentMethod(ABC):
    pass


class Stripe(PaymentMethod, CouponManageable):

    @staticmethod
    def add_coupon(coupon: Coupon):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        if coupon.is_valid_now:
            try:
                if coupon.discount_type == Coupon.PERCENT:
                    coupon = stripe.Coupon.create(
                        id=str(coupon.id),
                        name=coupon.code,
                        percent_off=coupon.amount,
                    )
                elif coupon.discount_type == Coupon.AMOUNT:
                    coupon = stripe.Coupon.create(
                        id=str(coupon.id),
                        name=coupon.code,
                        amount_off=int(coupon.amount * 100),
                        currency="EGP",
                    )
            except stripe._error.InvalidRequestError as e:
                print(f"Coupon {coupon.code} already exists: {e}")
                return None
            return coupon
        return None

    @staticmethod
    def remove_coupon(coupon: Coupon):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            deleted = stripe.Coupon.delete(str(coupon.id))
        except stripe._error.InvalidRequestError as e:
            print(f"Coupon {coupon.code} does not exist: {e}")
            return None
        return deleted