from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from apps.core.forms import StudentGroupForm
from apps.core.forms import SubjectForm
from apps.core.forms import TeacherForm
from apps.core.forms import WorkloadAssignmentForm
from apps.core.forms import WorkloadPlanForm
from apps.core.models import StudentGroup
from apps.core.models import Subject
from apps.core.models import Teacher
from apps.core.models import WorkloadPlan
from apps.workload.models import WorkloadAssignment


def is_study_master(user):

    return user.is_authenticated and user.role == 'STUDY_MASTER'


def is_head(user):

    return user.is_authenticated and user.role == 'HEAD'


def is_teacher(user):

    return user.is_authenticated and user.role == 'TEACHER'


study_master_required = user_passes_test(
    is_study_master,
    login_url='/login/'
)

head_required = user_passes_test(
    is_head,
    login_url='/login/'
)

teacher_required = user_passes_test(
    is_teacher,
    login_url='/login/'
)


def get_plan_hours(plan):

    distributed_hours = plan.assignments.aggregate(
        total=Sum('assigned_hours')
    )['total'] or 0

    remaining_hours = plan.total_hours - distributed_hours

    return distributed_hours, remaining_hours


def get_teacher_current_hours(teacher, academic_year):

    return WorkloadAssignment.objects.filter(
        teacher=teacher,
        academic_year=academic_year
    ).aggregate(
        total=Sum('assigned_hours')
    )['total'] or 0


def build_teacher_load_data(teachers, academic_year):

    teachers_data = []

    for teacher in teachers:

        current_hours = get_teacher_current_hours(
            teacher,
            academic_year
        )

        max_hours = getattr(
            teacher,
            'max_hours',
            0
        )

        progress = int(
            (current_hours / max_hours) * 100
        ) if max_hours else 0

        if current_hours > max_hours:

            status = 'Превышение'

            color = 'danger'

        elif progress >= 90:

            status = 'Высокая'

            color = 'warning'

        else:

            status = 'Нормальная'

            color = 'success'

        teachers_data.append({
            'teacher': teacher,
            'current_hours': current_hours,
            'max_hours': max_hours,
            'progress': progress,
            'status': status,
            'color': color
        })

    return teachers_data


def build_distribution_context(plan, form):

    assignments = WorkloadAssignment.objects.filter(
        plan=plan
    ).select_related(
        'teacher',
        'subject'
    ).order_by(
        'subject__semester',
        'subject__name'
    )

    assignment_by_subject = {
        assignment.subject_id: assignment
        for assignment in assignments
    }

    subject_rows = []

    for subject in Subject.objects.all().order_by('semester', 'name'):

        subject_rows.append({
            'subject': subject,
            'assignment': assignment_by_subject.get(subject.id)
        })

    distributed_hours, remaining_hours = get_plan_hours(plan)

    teachers = Teacher.objects.select_related('user').order_by('full_name')

    return {
        'plan': plan,
        'form': form,
        'subject_rows': subject_rows,
        'teachers_data': build_teacher_load_data(
            teachers,
            plan.academic_year
        ),
        'assignments': assignments,
        'distributed_hours': distributed_hours,
        'remaining_hours': remaining_hours,
        'total_hours': plan.total_hours,
        'is_approved': plan.status == WorkloadPlan.Statuses.APPROVED
    }


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
@head_required
@never_cache
def workload_view(request):

    plan_rows = []

    for plan in WorkloadPlan.objects.all().order_by('-created_at'):

        distributed_hours, remaining_hours = get_plan_hours(plan)

        plan_rows.append({
            'plan': plan,
            'distributed_hours': distributed_hours,
            'remaining_hours': remaining_hours
        })

    return render(
        request,
        'workload/workload.html',
        {
            'plan_rows': plan_rows
        }
    )


@login_required(login_url='/login/')
@head_required
@never_cache
def workload_distribution_view(request, pk):

    plan = get_object_or_404(
        WorkloadPlan,
        pk=pk
    )

    if request.method == 'POST' and 'approve_distribution' in request.POST:

        distributed_hours, remaining_hours = get_plan_hours(plan)

        if remaining_hours < 0:

            messages.error(
                request,
                'Нельзя утвердить распределение: превышены общие часы плана.'
            )

        else:

            plan.status = WorkloadPlan.Statuses.APPROVED

            plan.approved_at = timezone.now()

            plan.save(
                update_fields=[
                    'status',
                    'approved_at'
                ]
            )

            messages.success(
                request,
                'Распределение утверждено.'
            )

        return redirect(
            f'/workload/plans/{plan.id}/'
        )

    if request.method == 'POST':

        if plan.status == WorkloadPlan.Statuses.APPROVED:

            messages.warning(
                request,
                'Утвержденный план нельзя изменять.'
            )

            return redirect(
                f'/workload/plans/{plan.id}/'
            )

        form = WorkloadAssignmentForm(
            request.POST,
            plan=plan
        )

        if form.is_valid():

            subject = form.cleaned_data['subject']

            teacher = form.cleaned_data['teacher']

            assigned_hours = subject.hours

            current_teacher_hours = get_teacher_current_hours(
                teacher,
                plan.academic_year
            )

            distributed_hours, remaining_hours = get_plan_hours(plan)

            if current_teacher_hours + assigned_hours > teacher.max_hours:

                form.add_error(
                    'teacher',
                    'Нагрузка преподавателя превысит допустимый лимит.'
                )

            if assigned_hours > remaining_hours:

                form.add_error(
                    'subject',
                    'Назначение превышает оставшиеся часы плана.'
                )

            if not form.errors:

                WorkloadAssignment.objects.create(
                    plan=plan,
                    teacher=teacher,
                    subject=subject,
                    academic_year=plan.academic_year,
                    semester=subject.semester,
                    assigned_hours=assigned_hours
                )

                messages.success(
                    request,
                    'Дисциплина закреплена за преподавателем.'
                )

                return redirect(
                    f'/workload/plans/{plan.id}/'
                )

    else:

        form = WorkloadAssignmentForm(plan=plan)

    return render(
        request,
        'workload/distribution.html',
        build_distribution_context(
            plan,
            form
        )
    )


@login_required(login_url='/login/')
@head_required
@never_cache
def workload_assignment_delete_view(request, plan_pk, assignment_pk):

    plan = get_object_or_404(
        WorkloadPlan,
        pk=plan_pk
    )

    assignment = get_object_or_404(
        WorkloadAssignment,
        pk=assignment_pk,
        plan=plan
    )

    if plan.status == WorkloadPlan.Statuses.APPROVED:

        messages.warning(
            request,
            'Утвержденный план нельзя изменять.'
        )

        return redirect(
            f'/workload/plans/{plan.id}/'
        )

    if request.method == 'POST':

        assignment.delete()

        messages.success(
            request,
            'Назначение удалено.'
        )

    return redirect(
        f'/workload/plans/{plan.id}/'
    )


@login_required(login_url='/login/')
@teacher_required
@never_cache
def teacher_my_workload_view(request):

    teacher = getattr(
        request.user,
        'teacher_profile',
        None
    )

    assignments = WorkloadAssignment.objects.none()

    total_hours = 0

    if teacher is not None:

        assignments = WorkloadAssignment.objects.filter(
            teacher=teacher
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

    return render(
        request,
        'workload/my_workload.html',
        {
            'teacher': teacher,
            'assignments': assignments,
            'total_hours': total_hours
        }
    )


@login_required(login_url='/login/')
@study_master_required
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


@login_required(login_url='/login/')
@study_master_required
@never_cache
def workload_plan_detail_view(request, pk):

    plan = get_object_or_404(
        WorkloadPlan,
        pk=pk
    )

    return render(
        request,
        'study/workload_plan_detail.html',
        {
            'plan': plan
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def workload_plan_create_view(request):

    if request.method == 'POST':

        form = WorkloadPlanForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect('/study-workload/')

    else:

        form = WorkloadPlanForm()

    return render(
        request,
        'study/workload_plan_form.html',
        {
            'form': form,
            'title': 'Создать план нагрузки',
            'submit_label': 'Создать'
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def workload_plan_update_view(request, pk):

    plan = get_object_or_404(
        WorkloadPlan,
        pk=pk
    )

    if request.method == 'POST':

        form = WorkloadPlanForm(
            request.POST,
            instance=plan
        )

        if form.is_valid():

            form.save()

            return redirect('/study-workload/')

    else:

        form = WorkloadPlanForm(instance=plan)

    return render(
        request,
        'study/workload_plan_form.html',
        {
            'form': form,
            'plan': plan,
            'title': 'Редактировать план нагрузки',
            'submit_label': 'Сохранить'
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def workload_plan_delete_view(request, pk):

    plan = get_object_or_404(
        WorkloadPlan,
        pk=pk
    )

    if request.method == 'POST':

        plan.delete()

        return redirect('/study-workload/')

    return render(
        request,
        'study/workload_plan_confirm_delete.html',
        {
            'plan': plan
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def study_directories_view(request):

    return render(
        request,
        'study/directories/index.html'
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def teacher_list_view(request):

    teachers = Teacher.objects.select_related('user').order_by('full_name')

    rows = []

    for teacher in teachers:

        rows.append({
            'object': teacher,
            'values': (
                teacher.full_name,
                teacher.user.email,
                teacher.get_position_display(),
                teacher.academic_degree or '-',
                teacher.rate,
                teacher.max_hours,
            )
        })

    return render(
        request,
        'study/directories/list.html',
        {
            'title': 'Преподаватели',
            'description': 'Справочник преподавателей кафедры.',
            'create_url': '/study-directories/teachers/create/',
            'headers': (
                'ФИО',
                'Пользователь',
                'Должность',
                'Ученая степень',
                'Ставка',
                'Макс. часов',
            ),
            'rows': rows,
            'empty_text': 'Преподаватели пока не добавлены.',
            'edit_url_name': '/study-directories/teachers/',
            'delete_url_name': '/study-directories/teachers/',
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def teacher_create_view(request):

    return directory_form_view(
        request=request,
        form_class=TeacherForm,
        template_context={
            'title': 'Добавить преподавателя',
            'description': 'Заполните данные преподавателя.',
            'submit_label': 'Создать',
            'cancel_url': '/study-directories/teachers/'
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def teacher_update_view(request, pk):

    teacher = get_object_or_404(
        Teacher,
        pk=pk
    )

    return directory_form_view(
        request=request,
        form_class=TeacherForm,
        instance=teacher,
        template_context={
            'title': 'Редактировать преподавателя',
            'description': 'Измените данные преподавателя.',
            'submit_label': 'Сохранить',
            'cancel_url': '/study-directories/teachers/'
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def teacher_delete_view(request, pk):

    teacher = get_object_or_404(
        Teacher,
        pk=pk
    )

    return directory_delete_view(
        request=request,
        instance=teacher,
        title='Удалить преподавателя',
        cancel_url='/study-directories/teachers/'
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def subject_list_view(request):

    subjects = Subject.objects.all().order_by('name')

    rows = []

    for subject in subjects:

        rows.append({
            'object': subject,
            'values': (
                subject.name,
                subject.hours,
                subject.semester,
                subject.get_control_type_display(),
            )
        })

    return render(
        request,
        'study/directories/list.html',
        {
            'title': 'Дисциплины',
            'description': 'Справочник учебных дисциплин.',
            'create_url': '/study-directories/subjects/create/',
            'headers': (
                'Название',
                'Часы',
                'Семестр',
                'Тип контроля',
            ),
            'rows': rows,
            'empty_text': 'Дисциплины пока не добавлены.',
            'edit_url_name': '/study-directories/subjects/',
            'delete_url_name': '/study-directories/subjects/',
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def subject_create_view(request):

    return directory_form_view(
        request=request,
        form_class=SubjectForm,
        template_context={
            'title': 'Добавить дисциплину',
            'description': 'Заполните данные дисциплины.',
            'submit_label': 'Создать',
            'cancel_url': '/study-directories/subjects/'
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def subject_update_view(request, pk):

    subject = get_object_or_404(
        Subject,
        pk=pk
    )

    return directory_form_view(
        request=request,
        form_class=SubjectForm,
        instance=subject,
        template_context={
            'title': 'Редактировать дисциплину',
            'description': 'Измените данные дисциплины.',
            'submit_label': 'Сохранить',
            'cancel_url': '/study-directories/subjects/'
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def subject_delete_view(request, pk):

    subject = get_object_or_404(
        Subject,
        pk=pk
    )

    return directory_delete_view(
        request=request,
        instance=subject,
        title='Удалить дисциплину',
        cancel_url='/study-directories/subjects/'
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def group_list_view(request):

    groups = StudentGroup.objects.all().order_by('name')

    rows = []

    for group in groups:

        rows.append({
            'object': group,
            'values': (
                group.name,
                group.course,
                group.direction,
            )
        })

    return render(
        request,
        'study/directories/list.html',
        {
            'title': 'Группы',
            'description': 'Справочник студенческих групп.',
            'create_url': '/study-directories/groups/create/',
            'headers': (
                'Название',
                'Курс',
                'Направление',
            ),
            'rows': rows,
            'empty_text': 'Группы пока не добавлены.',
            'edit_url_name': '/study-directories/groups/',
            'delete_url_name': '/study-directories/groups/',
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def group_create_view(request):

    return directory_form_view(
        request=request,
        form_class=StudentGroupForm,
        template_context={
            'title': 'Добавить группу',
            'description': 'Заполните данные студенческой группы.',
            'submit_label': 'Создать',
            'cancel_url': '/study-directories/groups/'
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def group_update_view(request, pk):

    group = get_object_or_404(
        StudentGroup,
        pk=pk
    )

    return directory_form_view(
        request=request,
        form_class=StudentGroupForm,
        instance=group,
        template_context={
            'title': 'Редактировать группу',
            'description': 'Измените данные студенческой группы.',
            'submit_label': 'Сохранить',
            'cancel_url': '/study-directories/groups/'
        }
    )


@login_required(login_url='/login/')
@study_master_required
@never_cache
def group_delete_view(request, pk):

    group = get_object_or_404(
        StudentGroup,
        pk=pk
    )

    return directory_delete_view(
        request=request,
        instance=group,
        title='Удалить группу',
        cancel_url='/study-directories/groups/'
    )


def directory_form_view(
    request,
    form_class,
    template_context,
    instance=None
):

    if request.method == 'POST':

        form = form_class(
            request.POST,
            instance=instance
        )

        if form.is_valid():

            form.save()

            return redirect(template_context['cancel_url'])

    else:

        form = form_class(instance=instance)

    context = {
        'form': form
    }

    context.update(template_context)

    return render(
        request,
        'study/directories/form.html',
        context
    )


def directory_delete_view(
    request,
    instance,
    title,
    cancel_url
):

    if request.method == 'POST':

        instance.delete()

        return redirect(cancel_url)

    return render(
        request,
        'study/directories/confirm_delete.html',
        {
            'title': title,
            'object': instance,
            'cancel_url': cancel_url
        }
    )
