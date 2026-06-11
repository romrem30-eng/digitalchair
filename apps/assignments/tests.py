from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.assignments.models import Task
from apps.core.models import Teacher
from apps.notifications.models import Notification


class AssignmentTaskTests(TestCase):

    def setUp(self):

        User = get_user_model()

        self.head_user = User.objects.create_user(
            email='head-task@example.com',
            password='password',
            role='HEAD'
        )

        self.teacher_user = User.objects.create_user(
            email='teacher-task@example.com',
            password='password',
            role='TEACHER'
        )

        self.second_teacher_user = User.objects.create_user(
            email='teacher-task-2@example.com',
            password='password',
            role='TEACHER'
        )

        self.teacher_profile = Teacher.objects.create(
            user=self.teacher_user,
            full_name='Иванов Иван Иванович',
            position='docent',
            academic_degree='к.т.н.',
            rate='1.0',
            max_hours=600
        )

        self.second_teacher_profile = Teacher.objects.create(
            user=self.second_teacher_user,
            full_name='Петров Петр Петрович',
            position='assistant',
            academic_degree='',
            rate='1.0',
            max_hours=500
        )

        self.task = Task.objects.create(
            title='Подготовить отчет',
            description='Подготовить учебный отчет по кафедре.',
            teacher=self.teacher_profile,
            created_by=self.head_user,
            due_date=timezone.localdate() + timedelta(days=7),
            status=Task.Statuses.NEW,
            priority=Task.Priorities.HIGH
        )

        self.second_task = Task.objects.create(
            title='Обновить методичку',
            description='Обновить методические материалы.',
            teacher=self.second_teacher_profile,
            created_by=self.head_user,
            due_date=timezone.localdate() + timedelta(days=10),
            status=Task.Statuses.IN_PROGRESS,
            priority=Task.Priorities.LOW
        )

    def test_head_can_create_task(self):

        self.client.login(
            email='head-task@example.com',
            password='password'
        )

        response = self.client.post(
            '/assignments/create/',
            {
                'title': 'Собрать документы',
                'description': 'Собрать пакет документов.',
                'teacher': self.teacher_profile.id,
                'due_date': (timezone.localdate() + timedelta(days=5)).isoformat(),
                'priority': Task.Priorities.MEDIUM
            }
        )

        self.assertRedirects(
            response,
            '/assignments/'
        )

        self.assertTrue(
            Task.objects.filter(title='Собрать документы').exists()
        )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.teacher_user,
                notification_type=Notification.Types.NEW_TASK
            ).exists()
        )

    def test_teacher_sees_new_task_notification_in_notification_center(self):

        self.client.login(
            email='head-task@example.com',
            password='password'
        )

        response = self.client.post(
            '/assignments/create/',
            {
                'title': 'Подготовить презентацию',
                'description': 'Собрать материалы для презентации кафедры.',
                'teacher': self.teacher_profile.id,
                'due_date': (timezone.localdate() + timedelta(days=3)).isoformat(),
                'priority': Task.Priorities.HIGH
            }
        )

        self.assertRedirects(
            response,
            '/assignments/'
        )

        self.client.logout()

        self.client.login(
            email='teacher-task@example.com',
            password='password'
        )

        response = self.client.get(
            '/notifications/'
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            'Новое поручение'
        )

        self.assertContains(
            response,
            'Подготовить презентацию'
        )

    def test_teacher_sees_only_own_tasks(self):

        self.client.login(
            email='teacher-task@example.com',
            password='password'
        )

        response = self.client.get(
            '/my-assignments/'
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            'Подготовить отчет'
        )

        self.assertNotContains(
            response,
            'Обновить методичку'
        )

    def test_teacher_can_change_status_to_in_progress(self):

        self.client.login(
            email='teacher-task@example.com',
            password='password'
        )

        response = self.client.post(
            f'/my-assignments/{self.task.id}/status/'
        )

        self.assertRedirects(
            response,
            f'/my-assignments/{self.task.id}/'
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Statuses.IN_PROGRESS
        )

    def test_teacher_can_change_status_to_completed(self):

        self.task.status = Task.Statuses.IN_PROGRESS
        self.task.save()

        self.client.login(
            email='teacher-task@example.com',
            password='password'
        )

        response = self.client.post(
            f'/my-assignments/{self.task.id}/status/'
        )

        self.assertRedirects(
            response,
            f'/my-assignments/{self.task.id}/'
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Statuses.COMPLETED
        )

        self.assertIsNotNone(
            self.task.completed_at
        )

    def test_access_control_forbidden(self):

        self.client.login(
            email='teacher-task@example.com',
            password='password'
        )

        response = self.client.get(
            '/assignments/'
        )

        self.assertEqual(
            response.status_code,
            302
        )

        response = self.client.get(
            f'/my-assignments/{self.second_task.id}/'
        )

        self.assertEqual(
            response.status_code,
            404
        )

    def test_filtering_works(self):

        self.client.login(
            email='head-task@example.com',
            password='password'
        )

        response = self.client.get(
            '/assignments/',
            {
                'status': Task.Statuses.NEW,
                'teacher': str(self.teacher_profile.id),
                'priority': Task.Priorities.HIGH
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            'Подготовить отчет'
        )

        self.assertNotContains(
            response,
            'Обновить методичку'
        )
