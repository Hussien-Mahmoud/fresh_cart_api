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


# todo: not filtered
class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='')
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self) -> str:
        return f"{self.line1}, {self.city}"
