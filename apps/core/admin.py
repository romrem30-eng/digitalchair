from django.contrib import admin

from .models import (
    Teacher,
    Subject,
    StudentGroup,
    Student,
    WorkloadPlan
)

@admin.register(WorkloadPlan)
class WorkloadPlanAdmin(admin.ModelAdmin):

    list_display = (
        'кафедра',
        'academic_year',
        'total_hours',
        'status',
        'created_at'
    )
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):

    list_display = (
        'full_name',
        'position',
        'academic_degree',
        'rate',
        'max_hours',
    )

    search_fields = (
        'full_name',
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'hours',
        'semester',
        'control_type',
    )

    search_fields = (
        'name',
    )


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'course',
        'direction',
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        'full_name',
        'group',
        'record_book_number',
    )

    search_fields = (
        'full_name',
    )