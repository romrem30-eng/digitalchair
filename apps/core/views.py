from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from apps.core.models import Teacher
from apps.core.models import WorkloadPlan

from django.shortcuts import render


@never_cache
@login_required(login_url='/login/')
def admin_dashboard(request):

    return render(
        request,
        'dashboards/admin_dashboard.html'
    )


@never_cache
@login_required(login_url='/login/')
def head_dashboard(request):

    return render(
        request,
        'dashboards/head_dashboard.html'
    )


@never_cache
@login_required(login_url='/login/')
def teacher_dashboard(request):

    return render(
        request,
        'dashboards/teacher_dashboard.html'
    )


@never_cache
@login_required(login_url='/login/')
def study_dashboard(request):

    return render(
        request,
        'dashboards/study_dashboard.html'
    )

@login_required(login_url='/login/')
@never_cache
def workload_view(request):

    teachers = Teacher.objects.all()

    teachers_data = []

    for teacher in teachers:

        current_hours = getattr(
            teacher,
            'max_hours',
            0
        ) // 2

        max_hours = getattr(
            teacher,
            'max_hours',
            1
        )

        progress = int(
            (current_hours / max_hours) * 100
        )

        if progress < 70:

            status = 'Нормальная'

            color = 'success'

        elif progress < 90:

            status = 'Высокая'

            color = 'warning'

        else:

            status = 'Перегруз'

            color = 'danger'

        teachers_data.append({

            'teacher': teacher,

            'current_hours': current_hours,

            'max_hours': max_hours,

            'progress': progress,

            'status': status,

            'color': color

        })

    return render(
        request,
        'workload/workload.html',
        {
            'teachers_data': teachers_data
        }
    )

@login_required(login_url='/login/')
@never_cache
def study_workload_view(request):

    plans = WorkloadPlan.objects.all().order_by(
        '-created_at'
    )

    return render(
        request,
        'study/study_workload.html',
        {
            'plans': plans
        }
    )