from typing import Optional
from ninja import Schema, ModelSchema
from datetime import datetime
from .models import Address


class AddressIn(ModelSchema):
    class Meta:
        model = Address
        exclude = ['id', 'user', 'created_at', 'updated_at', 'is_default']


class AddressOut(ModelSchema):
    class Meta:
        model = Address
        exclude = ['user']


class SignupIn(Schema):
    username: str
    email: str
    password: str


class LoginIn(Schema):
    email: str
    password: str


class TokenOut(Schema):
    access: str
    refresh: str


class PasswordChangeIn(Schema):
    old_password: str
    new_password: str


class PasswordForgotIn(Schema):
    email: str
    reset_base_url: str  # client URL like https://app/reset


class PasswordResetIn(Schema):
    uidb64: str
    token: str
    new_password: str
