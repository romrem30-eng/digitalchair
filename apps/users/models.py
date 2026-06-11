from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager

from django.db import models


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):

        if not email:

            raise ValueError('Email обязателен')

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            username=email,
            **extra_fields
        )

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', True)

        extra_fields.setdefault('is_superuser', True)

        extra_fields.setdefault('is_active', True)

        return self.create_user(
            email,
            password,
            **extra_fields
        )


class User(AbstractUser):

    class Roles(models.TextChoices):

        ADMIN = 'ADMIN', 'Администратор'

        HEAD = 'HEAD', 'Заведующий кафедрой'

        TEACHER = 'TEACHER', 'Преподаватель'

        STUDENT = 'STUDENT', 'Студент'

        STUDY_MASTER = 'STUDY_MASTER', 'Учебный мастер'

    username = models.CharField(
        max_length=150,
        unique=True
    )

    email = models.EmailField(
        unique=True
    )

    role = models.CharField(
        max_length=30,
        choices=Roles.choices,
        default=Roles.TEACHER
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    telegram_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    telegram_bind_code = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    telegram_bind_code_created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    is_2fa_enabled = models.BooleanField(
        default=False
    )

    totp_secret = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):

        return self.email
