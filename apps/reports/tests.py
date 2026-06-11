from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.assignments.models import Task
from apps.core.models import StudentGroup
from apps.core.models import Subject
from apps.core.models import Teacher
from apps.core.models import WorkloadPlan
from apps.workload.models import WorkloadAssignment


class ReportsAccessTests(TestCase):

    def setUp(self):

        User = get_user_model()

        self.admin_user = User.objects.create_user(
            email='reports-admin@example.com',
            password='password',
            role='ADMIN'
        )

        self.head_user = User.objects.create_user(
            email='reports-head@example.com',
            password='password',
            role='HEAD'
        )

        self.study_master_user = User.objects.create_user(
            email='reports-study@example.com',
            password='password',
            role='STUDY_MASTER'
        )

        self.teacher_user = User.objects.create_user(
            email='reports-teacher@example.com',
            password='password',
            role='TEACHER'
        )

        self.second_teacher_user = User.objects.create_user(
            email='reports-teacher-2@example.com',
            password='password',
            role='TEACHER'
        )

        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            full_name='Иванов Иван Иванович',
            position='docent',
            academic_degree='к.т.н.',
            rate='1.0',
            max_hours=800
        )

        self.second_teacher = Teacher.objects.create(
            user=self.second_teacher_user,
            full_name='Петров Петр Петрович',
            position='assistant',
            academic_degree='',
            rate='1.0',
            max_hours=700
        )

        self.subject = Subject.objects.create(
            name='Программирование',
            hours=144,
            semester=1,
            control_type='exam'
        )

        self.second_subject = Subject.objects.create(
            name='Базы данных',
            hours=90,
            semester=2,
            control_type='test'
        )

        self.group = StudentGroup.objects.create(
            name='ИВТ-101',
            course=1,
            direction='Информатика и вычислительная техника'
        )

        self.plan = WorkloadPlan.objects.create(
            кафедра='Кафедра информатики',
            academic_year='2025-2026',
            total_hours=300,
            status=WorkloadPlan.Statuses.DRAFT
        )

        WorkloadAssignment.objects.create(
            plan=self.plan,
            teacher=self.teacher,
            subject=self.subject,
            academic_year='2025-2026',
            semester=1,
            assigned_hours=144
        )

        WorkloadAssignment.objects.create(
            plan=self.plan,
            teacher=self.second_teacher,
            subject=self.second_subject,
            academic_year='2025-2026',
            semester=2,
            assigned_hours=90
        )

        Task.objects.create(
            title='Подготовить отчет кафедры',
            description='Собрать сводные данные.',
            teacher=self.teacher,
            created_by=self.head_user,
            due_date=timezone.localdate() + timedelta(days=5),
            status=Task.Statuses.IN_PROGRESS,
            priority=Task.Priorities.HIGH
        )

    def test_admin_sees_all_reports_in_center(self):

        self.client.login(
            email='reports-admin@example.com',
            password='password'
        )

        response = self.client.get('/reports/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Сводная нагрузка кафедры')
        self.assertContains(response, 'Индивидуальная нагрузка преподавателя')
        self.assertContains(response, 'Отчет о выполнении нагрузки')
        self.assertContains(response, 'Отчет по поручениям')
        self.assertContains(response, 'Справка по контингенту')

    def test_head_can_open_workload_and_task_reports(self):

        self.client.login(
            email='reports-head@example.com',
            password='password'
        )

        response = self.client.get('/reports/workload-summary/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Программирование')

        response = self.client.get('/reports/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Подготовить отчет кафедры')

        response = self.client.get('/reports/contingent/')
        self.assertEqual(response.status_code, 302)

    def test_study_master_can_open_workload_and_contingent_reports(self):

        self.client.login(
            email='reports-study@example.com',
            password='password'
        )

        response = self.client.get('/reports/workload-execution/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Кафедра информатики')

        response = self.client.get('/reports/contingent/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['teachers_count'], 2)
        self.assertEqual(response.context['subjects_count'], 2)
        self.assertEqual(response.context['groups_count'], 1)

        response = self.client.get('/reports/tasks/')
        self.assertEqual(response.status_code, 302)

    def test_teacher_sees_only_personal_workload_report(self):

        self.client.login(
            email='reports-teacher@example.com',
            password='password'
        )

        response = self.client.get('/reports/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Индивидуальная нагрузка преподавателя')
        self.assertNotContains(response, 'Отчет по поручениям')

        response = self.client.get('/reports/teacher-workload/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Иванов Иван Иванович')
        self.assertContains(response, 'Программирование')
        self.assertNotContains(response, 'Петров Петр Петрович')

        response = self.client.get('/reports/workload-summary/')
        self.assertEqual(response.status_code, 302)

    def test_admin_can_filter_teacher_workload_report(self):

        self.client.login(
            email='reports-admin@example.com',
            password='password'
        )

        response = self.client.get(
            '/reports/teacher-workload/',
            {
                'teacher': self.second_teacher.id
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Петров Петр Петрович')
        self.assertContains(response, 'Базы данных')
        self.assertNotContains(response, 'Программирование')

    def test_admin_can_open_contingent_report_counts(self):

        self.client.login(
            email='reports-admin@example.com',
            password='password'
        )

        response = self.client.get('/reports/contingent/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['teachers_count'], 2)
        self.assertEqual(response.context['subjects_count'], 2)
        self.assertEqual(response.context['groups_count'], 1)
