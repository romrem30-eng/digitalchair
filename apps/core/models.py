from django.db import models
from django.conf import settings


class Teacher(models.Model):

    POSITION_CHOICES = [
        ('assistant', 'Ассистент'),
        ('senior_teacher', 'Старший преподаватель'),
        ('docent', 'Доцент'),
        ('professor', 'Профессор'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )

    full_name = models.CharField(
        max_length=255
    )

    position = models.CharField(
        max_length=50,
        choices=POSITION_CHOICES
    )

    academic_degree = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    rate = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=1.0
    )

    max_hours = models.PositiveIntegerField(
        default=900
    )

    def __str__(self):

        return self.full_name


class Subject(models.Model):

    CONTROL_CHOICES = [
        ('exam', 'Экзамен'),
        ('test', 'Зачет'),
        ('coursework', 'Курсовая работа'),
    ]

    name = models.CharField(
        max_length=255
    )

    hours = models.PositiveIntegerField()

    semester = models.PositiveIntegerField()

    control_type = models.CharField(
        max_length=50,
        choices=CONTROL_CHOICES
    )

    def __str__(self):

        return self.name


class StudentGroup(models.Model):

    name = models.CharField(
        max_length=100
    )

    course = models.PositiveIntegerField()

    direction = models.CharField(
        max_length=255
    )

    def __str__(self):

        return self.name


class Student(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    full_name = models.CharField(
        max_length=255
    )

    group = models.ForeignKey(
        StudentGroup,
        on_delete=models.CASCADE,
        related_name='students'
    )

    record_book_number = models.CharField(
        max_length=100
    )

    def __str__(self):

        return self.full_name


class WorkloadPlan(models.Model):

    class Statuses(models.TextChoices):

        DRAFT = 'DRAFT', 'Черновик'

        SUBMITTED = 'SUBMITTED', 'Отправлено'

        APPROVED = 'APPROVED', 'Утверждено'

        RETURNED = 'RETURNED', 'Возвращено'

    кафедра = models.CharField(
        max_length=255
    )

    total_hours = models.IntegerField()

    academic_year = models.CharField(
        max_length=50
    )

    status = models.CharField(
        max_length=30,
        choices=Statuses.choices,
        default=Statuses.DRAFT
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    approved_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):

        return f'{self.кафедра} ({self.academic_year})'
