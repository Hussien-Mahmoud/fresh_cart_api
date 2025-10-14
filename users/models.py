from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(email=self.normalize_email(email), **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
            **extra_fields,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    email = models.EmailField(
        _("Email address"),
        max_length=150,
        unique=True,
        error_messages={
            "unique": _("A user with that E-mail already exists."),
        },
    )
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=False,
        null=False,
    )
    first_name = ''
    last_name = ''

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']

    def get_full_name(self):
        """Return the user's username as their full name.

        Since this user model doesn't use first_name and last_name fields,
        the username is returned as the full name identifier.
        """
        return self.username

    def get_short_name(self):
        """Return the first part of username before any whitespace.

        For example, if username is 'John Doe', returns 'John'.
        If no whitespace exists, returns the entire username.
        """
        return self.username.split()[0]


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100)
    governorate = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=13)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Addresses'
        constraints = [
            # Ensure at most one address per user has is_default=True
            models.UniqueConstraint(
                fields=['user', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_address_per_user'
            ),
            # Validate Egyptian phone number format
            models.CheckConstraint(
                check=models.Q(
                    # Format 1: +201XXXXXXXXX (13 digits total)
                    models.Q(phone_number__regex=r'^\+201[0-9]{9}$') |
                    # Format 2: 01XXXXXXXXX (11 digits total)
                    models.Q(phone_number__regex=r'^01[0-9]{9}$')
                ),
                name='valid_egyptian_phone_number'
            ),
        ]
        ordering = ['-is_default', '-updated_at']

    def get_formatted_address(self):
        text = f'{self.line1}'.strip()
        text += f', {self.line2}'.strip() if self.line2 else ''
        text += f', {self.city}'.strip()
        text += f', {self.governorate}'.strip() if self.governorate else ''
        return text

    def __str__(self) -> str:
        return f"{self.line1}, {self.city}"
