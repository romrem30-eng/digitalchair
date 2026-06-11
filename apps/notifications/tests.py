from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.assignments.models import Task
from apps.core.models import Subject
from apps.core.models import Teacher
from apps.core.models import WorkloadPlan
from apps.notifications.models import Notification
from apps.notifications.models import create_task_notification
from apps.notifications.telegram import bind_user_to_telegram
from apps.notifications.telegram import build_tasks_message
from apps.notifications.telegram import complete_task_via_telegram
from apps.notifications.telegram import generate_telegram_bind_code
from apps.notifications.telegram import notify_workload_approved
from apps.workload.models import WorkloadAssignment


class TelegramModuleTests(TestCase):

    def setUp(self):

        user_model = get_user_model()

        self.head_user = user_model.objects.create_user(
            email='head-telegram@example.com',
            password='password',
            role='HEAD'
        )

        self.teacher_user = user_model.objects.create_user(
            email='teacher-telegram@example.com',
            password='password',
            role='TEACHER'
        )

        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            full_name='Иванов Иван Иванович',
            position='docent',
            academic_degree='к.т.н.',
            rate='1.0',
            max_hours=700
        )

        self.task = Task.objects.create(
            title='Подготовить отчет',
            description='Подготовить отчет по кафедре.',
            teacher=self.teacher,
            created_by=self.head_user,
            due_date=timezone.localdate() + timedelta(days=3),
            status=Task.Statuses.NEW,
            priority=Task.Priorities.HIGH
        )

        self.completed_task = Task.objects.create(
            title='Архивное поручение',
            description='Уже выполнено.',
            teacher=self.teacher,
            created_by=self.head_user,
            due_date=timezone.localdate() + timedelta(days=1),
            status=Task.Statuses.COMPLETED,
            priority=Task.Priorities.LOW
        )

    def create_plan(self):

        department_field = next(
            field.name
            for field in WorkloadPlan._meta.fields
            if field.name not in (
                'id',
                'total_hours',
                'academic_year',
                'status',
                'created_at',
                'approved_at',
            )
        )

        return WorkloadPlan.objects.create(
            **{
                department_field: 'Кафедра информатики',
                'academic_year': '2025-2026',
                'total_hours': 120,
                'status': WorkloadPlan.Statuses.DRAFT,
            }
        )

    def test_generate_telegram_bind_code(self):

        code = generate_telegram_bind_code(
            self.teacher_user
        )

        self.teacher_user.refresh_from_db()

        self.assertEqual(
            self.teacher_user.telegram_bind_code,
            code
        )
        self.assertEqual(
            len(code),
            6
        )
        self.assertTrue(code.isdigit())
        self.assertIsNotNone(
            self.teacher_user.telegram_bind_code_created_at
        )

    def test_bind_user_to_telegram(self):

        code = generate_telegram_bind_code(
            self.teacher_user
        )

        user, message = bind_user_to_telegram(
            code,
            987654321
        )

        self.teacher_user.refresh_from_db()

        self.assertEqual(user, self.teacher_user)
        self.assertIn('успешно', message.lower())
        self.assertEqual(
            self.teacher_user.telegram_id,
            '987654321'
        )
        self.assertIsNone(
            self.teacher_user.telegram_bind_code
        )

    def test_build_tasks_message_lists_active_tasks(self):

        message = build_tasks_message(
            self.teacher_user
        )

        self.assertIn(
            f'#{self.task.id}',
            message
        )
        self.assertIn(
            self.task.title,
            message
        )
        self.assertNotIn(
            self.completed_task.title,
            message
        )

    @patch('apps.notifications.telegram.send_telegram_text', return_value=True)
    def test_complete_task_via_telegram(self, mocked_send):

        self.head_user.telegram_id = '555001'
        self.head_user.save(
            update_fields=['telegram_id']
        )

        success, message = complete_task_via_telegram(
            self.teacher_user,
            self.task.id
        )

        self.task.refresh_from_db()

        self.assertTrue(success)
        self.assertIn('выполн', message.lower())
        self.assertEqual(
            self.task.status,
            Task.Statuses.COMPLETED
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.head_user,
                task=self.task,
                notification_type=Notification.Types.TASK_COMPLETED
            ).exists()
        )
        mocked_send.assert_called_once()

    @patch('apps.notifications.telegram.send_telegram_text', return_value=True)
    def test_create_task_notification_sends_telegram_notification(self, mocked_send):

        self.teacher_user.telegram_id = '777001'
        self.teacher_user.save(
            update_fields=['telegram_id']
        )

        create_task_notification(
            self.teacher_user,
            self.task,
            Notification.Types.NEW_TASK
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.teacher_user,
                task=self.task,
                notification_type=Notification.Types.NEW_TASK
            ).exists()
        )
        mocked_send.assert_called_once()

    @patch('apps.notifications.telegram.send_telegram_text', return_value=True)
    def test_notify_workload_approved_creates_telegram_notification(self, mocked_send):

        self.teacher_user.telegram_id = '999001'
        self.teacher_user.save(
            update_fields=['telegram_id']
        )

        subject = Subject.objects.create(
            name='Программирование',
            hours=120,
            semester=1,
            control_type='exam'
        )

        plan = self.create_plan()

        WorkloadAssignment.objects.create(
            plan=plan,
            teacher=self.teacher,
            subject=subject,
            academic_year=plan.academic_year,
            semester=subject.semester,
            assigned_hours=subject.hours
        )

        notify_workload_approved(plan)

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.teacher_user,
                task__isnull=True,
                title='Учебная нагрузка утверждена'
            ).exists()
        )
        mocked_send.assert_called_once()
