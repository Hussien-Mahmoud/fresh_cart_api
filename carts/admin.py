from django.contrib import admin
from .models import Coupon, Cart, CartItem


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "amount", "active", "valid_from", "valid_to")
    list_filter = ("active", "discount_type")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status")
    list_filter = ("status",)
    inlines = [CartItemInline]
