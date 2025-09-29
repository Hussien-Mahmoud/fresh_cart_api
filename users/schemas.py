from typing import Optional
from ninja import Schema


class AddressIn(Schema):
    line1: str
    line2: Optional[str] = ""
    city: str
    state: Optional[str] = ""
    postal_code: str
    country: str
    is_default: Optional[bool] = False


class AddressOut(Schema):
    id: int
    line1: str
    line2: Optional[str]
    city: str
    state: Optional[str]
    postal_code: str
    country: str
    is_default: bool


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
