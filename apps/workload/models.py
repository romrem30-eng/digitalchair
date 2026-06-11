from django.db import models

from apps.core.models import (
    Teacher,
    Subject,
    WorkloadPlan
)


class WorkloadAssignment(models.Model):

    plan = models.ForeignKey(
        WorkloadPlan,
        on_delete=models.CASCADE,
        related_name='assignments',
        blank=True,
        null=True
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='workloads'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='workloads'
    )

    academic_year = models.CharField(
        max_length=20,
        default='2025-2026'
    )

    semester = models.PositiveIntegerField()

    assigned_hours = models.PositiveIntegerField()

    notes = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.teacher} - {self.subject}'
