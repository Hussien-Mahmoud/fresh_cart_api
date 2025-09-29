from typing import Optional
from django.contrib.auth import get_user_model, aauthenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
from ninja import Router
from ninja_jwt.tokens import RefreshToken
from ninja_jwt.authentication import AsyncJWTAuth

from .schemas import SignupIn, LoginIn, TokenOut, PasswordChangeIn, PasswordForgotIn, PasswordResetIn

User = get_user_model()
router = Router(tags=["Auth"])  # public and protected endpoints on same router


@router.post("/auth/signup", response=TokenOut)
async def signup(request, payload: SignupIn):
    if User.objects.filter(email=payload.email).aexists():
        return 400, {"detail": "Email already exists"}
    user = User.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )
    refresh = RefreshToken.for_user(user)
    return TokenOut(access=str(refresh.access_token), refresh=str(refresh))


@router.post("/auth/login", response=TokenOut)
async def login(request, payload: LoginIn):
    user = await aauthenticate(request, email=payload.email, password=payload.password)
    if not user:
        return 401, {"detail": "Invalid credentials"}
    refresh = RefreshToken.for_user(user)
    return TokenOut(access=str(refresh.access_token), refresh=str(refresh))


@router.post("/auth/password/change", auth=AsyncJWTAuth())
async def change_password(request, payload: PasswordChangeIn):
    user: User = request.user
    if not await user.acheck_password(payload.old_password):
        return 400, {"detail": "Old password is incorrect"}
    user.set_password(payload.new_password)
    await user.asave(update_fields=["password"])
    return {"success": True}


# todo: code not filtered
@router.post("/auth/password/forgot")
def forgot_password(request, payload: PasswordForgotIn):
    try:
        user = User.objects.get(email=payload.email)
    except User.DoesNotExist:
        # Do not reveal whether email exists
        return {"success": True}

    token_gen = PasswordResetTokenGenerator()
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = token_gen.make_token(user)

    reset_link = payload.reset_base_url.rstrip("/") + f"/{uidb64}/{token}"
    subject = "Password reset instructions"
    message = f"Hi {user.get_full_name() or user.username},\n\nUse the following link to reset your password:\n{reset_link}\n\nIf you did not request this, please ignore this email."
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com')
    try:
        send_mail(subject, message, from_email, [user.email], fail_silently=True)
    except Exception:
        # even if email fails, we don't reveal
        pass
    return {"success": True}


# todo: code not filtered
@router.post("/auth/password/reset")
def reset_password(request, payload: PasswordResetIn):
    token_gen = PasswordResetTokenGenerator()
    try:
        uid = force_str(urlsafe_base64_decode(payload.uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        return router.create_response(request, {"detail": "Invalid token"}, status=400)

    if not token_gen.check_token(user, payload.token):
        return router.create_response(request, {"detail": "Invalid or expired token"}, status=400)

    user.set_password(payload.new_password)
    user.save(update_fields=["password"])
    return {"success": True}
