from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from apps.assignments.forms import TaskCreateForm
from apps.assignments.forms import TaskUpdateForm
from apps.assignments.models import Task
from apps.core.models import Teacher
from apps.notifications.models import Notification
from apps.notifications.models import create_task_notification


def is_head(user):

    return user.is_authenticated and user.role == 'HEAD'


def is_teacher(user):

    return user.is_authenticated and user.role == 'TEACHER'


head_required = user_passes_test(
    is_head,
    login_url='/login/'
)

teacher_required = user_passes_test(
    is_teacher,
    login_url='/login/'
)


def get_task_statistics(tasks):

    stats = tasks.aggregate(
        total=Count('id'),
        new_count=Count('id', filter=Q(status=Task.Statuses.NEW)),
        in_progress_count=Count('id', filter=Q(status=Task.Statuses.IN_PROGRESS)),
        completed_count=Count('id', filter=Q(status=Task.Statuses.COMPLETED)),
    )

    return {
        'total': stats['total'] or 0,
        'new_count': stats['new_count'] or 0,
        'in_progress_count': stats['in_progress_count'] or 0,
        'completed_count': stats['completed_count'] or 0,
    }


def notify_task_update(task, previous_status, previous_teacher):

    if previous_teacher != task.teacher and task.teacher.user != task.created_by:

        create_task_notification(
            task.teacher.user,
            task,
            Notification.Types.NEW_TASK
        )

    if previous_status != task.status:

        if task.status == Task.Statuses.COMPLETED:

            recipient = task.teacher.user
            notification_type = Notification.Types.TASK_COMPLETED

        else:

            recipient = task.teacher.user
            notification_type = Notification.Types.STATUS_CHANGED

        create_task_notification(
            recipient,
            task,
            notification_type
        )


@login_required(login_url='/login/')
@head_required
@never_cache
def task_list_view(request):

    tasks = Task.objects.select_related(
        'teacher',
        'teacher__user',
        'created_by'
    ).order_by(
        '-created_at'
    )

    status = request.GET.get('status')
    teacher_id = request.GET.get('teacher')
    priority = request.GET.get('priority')

    if status:

        tasks = tasks.filter(status=status)

    if teacher_id:

        tasks = tasks.filter(teacher_id=teacher_id)

    if priority:

        tasks = tasks.filter(priority=priority)

    return render(
        request,
        'assignments/task_list.html',
        {
            'tasks': tasks,
            'teachers': Teacher.objects.order_by('full_name'),
            'statuses': Task.Statuses,
            'priorities': Task.Priorities,
            'selected_status': status or '',
            'selected_teacher': teacher_id or '',
            'selected_priority': priority or '',
            'stats': get_task_statistics(tasks),
        }
    )


@login_required(login_url='/login/')
@head_required
@never_cache
def task_create_view(request):

    if request.method == 'POST':

        form = TaskCreateForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            task = form.save(commit=False)

            task.created_by = request.user

            task.save()

            create_task_notification(
                task.teacher.user,
                task,
                Notification.Types.NEW_TASK
            )

            messages.success(
                request,
                'Поручение создано.'
            )

            return redirect('/assignments/')

    else:

        form = TaskCreateForm()

    return render(
        request,
        'assignments/task_form.html',
        {
            'form': form,
            'title': 'Создать поручение',
            'submit_label': 'Создать',
            'cancel_url': '/assignments/'
        }
    )


@login_required(login_url='/login/')
@head_required
@never_cache
def task_detail_view(request, pk):

    task = get_object_or_404(
        Task.objects.select_related(
            'teacher',
            'teacher__user',
            'created_by'
        ),
        pk=pk
    )

    return render(
        request,
        'assignments/task_detail.html',
        {
            'task': task,
            'back_url': '/assignments/',
            'is_head': True,
        }
    )


@login_required(login_url='/login/')
@head_required
@never_cache
def task_update_view(request, pk):

    task = get_object_or_404(
        Task,
        pk=pk
    )

    previous_status = task.status
    previous_teacher = task.teacher

    if request.method == 'POST':

        form = TaskUpdateForm(
            request.POST,
            request.FILES,
            instance=task
        )

        if form.is_valid():

            task = form.save()

            notify_task_update(
                task,
                previous_status,
                previous_teacher
            )

            messages.success(
                request,
                'Поручение обновлено.'
            )

            return redirect(f'/assignments/{task.id}/')

    else:

        form = TaskUpdateForm(instance=task)

    return render(
        request,
        'assignments/task_form.html',
        {
            'form': form,
            'title': 'Редактировать поручение',
            'submit_label': 'Сохранить',
            'cancel_url': f'/assignments/{task.id}/'
        }
    )


@login_required(login_url='/login/')
@head_required
@never_cache
def task_delete_view(request, pk):

    task = get_object_or_404(
        Task,
        pk=pk
    )

    if request.method == 'POST':

        task.delete()

        messages.success(
            request,
            'Поручение удалено.'
        )

        return redirect('/assignments/')

    return render(
        request,
        'assignments/task_confirm_delete.html',
        {
            'task': task,
            'cancel_url': f'/assignments/{task.id}/'
        }
    )


@login_required(login_url='/login/')
@teacher_required
@never_cache
def my_tasks_view(request):

    teacher = getattr(
        request.user,
        'teacher_profile',
        None
    )

    tasks = Task.objects.none()

    if teacher is not None:

        tasks = Task.objects.filter(
            teacher=teacher
        ).order_by(
            'due_date',
            '-created_at'
        )

    return render(
        request,
        'assignments/my_tasks.html',
        {
            'teacher': teacher,
            'tasks': tasks,
        }
    )


@login_required(login_url='/login/')
@teacher_required
@never_cache
def my_task_detail_view(request, pk):

    teacher = getattr(
        request.user,
        'teacher_profile',
        None
    )

    task = get_object_or_404(
        Task.objects.select_related(
            'teacher',
            'teacher__user',
            'created_by'
        ),
        pk=pk,
        teacher=teacher
    )

    allowed_next_status = None

    if task.status == Task.Statuses.NEW:

        allowed_next_status = Task.Statuses.IN_PROGRESS

    elif task.status == Task.Statuses.IN_PROGRESS:

        allowed_next_status = Task.Statuses.COMPLETED

    return render(
        request,
        'assignments/task_detail.html',
        {
            'task': task,
            'back_url': '/my-assignments/',
            'is_teacher': True,
            'allowed_next_status': allowed_next_status,
        }
    )


@login_required(login_url='/login/')
@teacher_required
@never_cache
def my_task_status_update_view(request, pk):

    teacher = getattr(
        request.user,
        'teacher_profile',
        None
    )

    task = get_object_or_404(
        Task,
        pk=pk,
        teacher=teacher
    )

    if request.method == 'POST':

        if task.status == Task.Statuses.NEW:

            task.status = Task.Statuses.IN_PROGRESS

            notification_type = Notification.Types.STATUS_CHANGED

        elif task.status == Task.Statuses.IN_PROGRESS:

            task.status = Task.Statuses.COMPLETED

            notification_type = Notification.Types.TASK_COMPLETED

        else:

            messages.error(
                request,
                'Недопустимая смена статуса.'
            )

            return redirect(f'/my-assignments/{task.id}/')

        task.save()

        create_task_notification(
            task.created_by,
            task,
            notification_type
        )

        messages.success(
            request,
            'Статус поручения обновлен.'
        )

    return redirect(f'/my-assignments/{task.id}/')
