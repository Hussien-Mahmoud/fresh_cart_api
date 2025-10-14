from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Address

User = get_user_model()
admin.site.register(User, UserAdmin)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "line1", "line2", "city", "governorate", "phone_number", "is_default")
    list_filter = ("city", "is_default")
