from django.contrib import admin

from .models import WorkloadAssignment


@admin.register(WorkloadAssignment)
class WorkloadAssignmentAdmin(admin.ModelAdmin):

    list_display = (
        'teacher',
        'subject',
        'academic_year',
        'semester',
        'assigned_hours',
    )

    list_filter = (
        'academic_year',
        'semester',
    )

    search_fields = (
        'teacher__full_name',
        'subject__name',
    )