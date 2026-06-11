from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from apps.assignments.models import Task
from apps.core.models import StudentGroup
from apps.core.models import Subject
from apps.core.models import Teacher
from apps.core.models import WorkloadPlan
from apps.users.models import User
from apps.workload.models import WorkloadAssignment


REPORT_DEFINITIONS = {
    'workload-summary': {
        'title': 'Сводная нагрузка кафедры',
        'description': 'Общая ведомость распределенной учебной нагрузки по преподавателям и дисциплинам.',
        'url': '/reports/workload-summary/',
        'roles': {
            User.Roles.ADMIN,
            User.Roles.HEAD,
            User.Roles.STUDY_MASTER,
        }
    },
    'teacher-workload': {
        'title': 'Индивидуальная нагрузка преподавателя',
        'description': 'Отчет по дисциплинам и суммарной нагрузке выбранного преподавателя.',
        'url': '/reports/teacher-workload/',
        'roles': {
            User.Roles.ADMIN,
            User.Roles.HEAD,
            User.Roles.STUDY_MASTER,
            User.Roles.TEACHER,
        }
    },
    'workload-execution': {
        'title': 'Отчет о выполнении нагрузки',
        'description': 'Сравнение плановых и распределенных часов по планам нагрузки.',
        'url': '/reports/workload-execution/',
        'roles': {
            User.Roles.ADMIN,
            User.Roles.HEAD,
            User.Roles.STUDY_MASTER,
        }
    },
    'tasks': {
        'title': 'Отчет по поручениям',
        'description': 'Список поручений с исполнителями, сроками, приоритетами и статусами.',
        'url': '/reports/tasks/',
        'roles': {
            User.Roles.ADMIN,
            User.Roles.HEAD,
        }
    },
    'contingent': {
        'title': 'Справка по контингенту',
        'description': 'Сводные количественные показатели по преподавателям, дисциплинам и группам.',
        'url': '/reports/contingent/',
        'roles': {
            User.Roles.ADMIN,
            User.Roles.STUDY_MASTER,
        }
    }
}


def role_required(*roles):

    return user_passes_test(
        lambda user: user.is_authenticated and user.role in roles,
        login_url='/login/'
    )


report_center_required = role_required(
    User.Roles.ADMIN,
    User.Roles.HEAD,
    User.Roles.STUDY_MASTER,
    User.Roles.TEACHER,
)

workload_reports_required = role_required(
    User.Roles.ADMIN,
    User.Roles.HEAD,
    User.Roles.STUDY_MASTER,
)

teacher_workload_required = role_required(
    User.Roles.ADMIN,
    User.Roles.HEAD,
    User.Roles.STUDY_MASTER,
    User.Roles.TEACHER,
)

task_reports_required = role_required(
    User.Roles.ADMIN,
    User.Roles.HEAD,
)

contingent_report_required = role_required(
    User.Roles.ADMIN,
    User.Roles.STUDY_MASTER,
)


def get_dashboard_url(user):

    if user.role == User.Roles.ADMIN:

        return '/admin-dashboard/'

    if user.role == User.Roles.HEAD:

        return '/head-dashboard/'

    if user.role == User.Roles.STUDY_MASTER:

        return '/study-dashboard/'

    return '/teacher-dashboard/'


def get_report_links(user):

    report_links = []

    for report_key in (
        'workload-summary',
        'teacher-workload',
        'workload-execution',
        'tasks',
        'contingent',
    ):

        report = REPORT_DEFINITIONS[report_key]

        if user.role in report['roles']:

            report_links.append({
                'key': report_key,
                'title': report['title'],
                'description': report['description'],
                'url': report['url']
            })

    return report_links


def build_base_context(request, active_report=None):

    return {
        'dashboard_url': get_dashboard_url(request.user),
        'report_links': get_report_links(request.user),
        'active_report': active_report,
    }


def render_report_page(request, template_name, context=None, active_report=None):

    page_context = build_base_context(
        request,
        active_report=active_report
    )

    if context:

        page_context.update(context)

    return render(
        request,
        template_name,
        page_context
    )


@login_required(login_url='/login/')
@report_center_required
@never_cache
def report_center_view(request):

    return render_report_page(
        request,
        'reports/report_center.html',
        {
            'title': 'Отчеты',
            'description': 'Единый центр просмотра отчетов по данным DigitalChair.',
            'report_cards': get_report_links(request.user),
        }
    )


@login_required(login_url='/login/')
@workload_reports_required
@never_cache
def workload_summary_report_view(request):

    academic_year = request.GET.get('academic_year', '').strip()

    assignments = WorkloadAssignment.objects.select_related(
        'teacher',
        'subject'
    ).order_by(
        'teacher__full_name',
        'subject__semester',
        'subject__name'
    )

    if academic_year:

        assignments = assignments.filter(
            academic_year=academic_year
        )

    academic_years = list(
        WorkloadAssignment.objects.order_by(
            '-academic_year'
        ).values_list(
            'academic_year',
            flat=True
        ).distinct()
    )

    return render_report_page(
        request,
        'reports/workload_summary.html',
        {
            'title': REPORT_DEFINITIONS['workload-summary']['title'],
            'description': REPORT_DEFINITIONS['workload-summary']['description'],
            'assignments': assignments,
            'academic_year': academic_year,
            'academic_years': academic_years,
        },
        active_report='workload-summary'
    )


@login_required(login_url='/login/')
@teacher_workload_required
@never_cache
def teacher_workload_report_view(request):

    teachers = Teacher.objects.select_related('user').order_by('full_name')
    selected_teacher = None

    if request.user.role == User.Roles.TEACHER:

        selected_teacher = getattr(
            request.user,
            'teacher_profile',
            None
        )

    else:

        teacher_id = request.GET.get('teacher')

        if teacher_id:

            selected_teacher = teachers.filter(
                pk=teacher_id
            ).first()

        if selected_teacher is None:

            selected_teacher = teachers.first()

    assignments = WorkloadAssignment.objects.none()
    total_hours = 0

    if selected_teacher is not None:

        assignments = WorkloadAssignment.objects.filter(
            teacher=selected_teacher
        ).select_related(
            'subject',
            'plan'
        ).order_by(
            '-academic_year',
            'semester',
            'subject__name'
        )

        total_hours = assignments.aggregate(
            total=Sum('assigned_hours')
        )['total'] or 0

    return render_report_page(
        request,
        'reports/teacher_workload.html',
        {
            'title': REPORT_DEFINITIONS['teacher-workload']['title'],
            'description': REPORT_DEFINITIONS['teacher-workload']['description'],
            'teachers': teachers,
            'selected_teacher': selected_teacher,
            'assignments': assignments,
            'total_hours': total_hours,
            'is_personal_view': request.user.role == User.Roles.TEACHER,
        },
        active_report='teacher-workload'
    )


@login_required(login_url='/login/')
@workload_reports_required
@never_cache
def workload_execution_report_view(request):

    academic_year = request.GET.get('academic_year', '').strip()

    plans = WorkloadPlan.objects.order_by('-created_at')

    if academic_year:

        plans = plans.filter(
            academic_year=academic_year
        )

    plan_rows = []

    for plan in plans:

        distributed_hours = plan.assignments.aggregate(
            total=Sum('assigned_hours')
        )['total'] or 0

        remaining_hours = plan.total_hours - distributed_hours

        plan_rows.append({
            'plan': plan,
            'distributed_hours': distributed_hours,
            'remaining_hours': remaining_hours,
        })

    academic_years = list(
        WorkloadPlan.objects.order_by(
            '-academic_year'
        ).values_list(
            'academic_year',
            flat=True
        ).distinct()
    )

    return render_report_page(
        request,
        'reports/workload_execution.html',
        {
            'title': REPORT_DEFINITIONS['workload-execution']['title'],
            'description': REPORT_DEFINITIONS['workload-execution']['description'],
            'plan_rows': plan_rows,
            'academic_year': academic_year,
            'academic_years': academic_years,
        },
        active_report='workload-execution'
    )


@login_required(login_url='/login/')
@task_reports_required
@never_cache
def tasks_report_view(request):

    tasks = Task.objects.select_related(
        'teacher',
        'created_by'
    ).order_by(
        '-created_at'
    )

    return render_report_page(
        request,
        'reports/tasks_report.html',
        {
            'title': REPORT_DEFINITIONS['tasks']['title'],
            'description': REPORT_DEFINITIONS['tasks']['description'],
            'tasks': tasks,
        },
        active_report='tasks'
    )


@login_required(login_url='/login/')
@contingent_report_required
@never_cache
def contingent_report_view(request):

    return render_report_page(
        request,
        'reports/contingent.html',
        {
            'title': REPORT_DEFINITIONS['contingent']['title'],
            'description': REPORT_DEFINITIONS['contingent']['description'],
            'teachers_count': Teacher.objects.count(),
            'subjects_count': Subject.objects.count(),
            'groups_count': StudentGroup.objects.count(),
        },
        active_report='contingent'
    )
