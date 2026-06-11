from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.models import StudentGroup
from apps.core.models import Subject
from apps.core.models import Teacher
from apps.core.models import WorkloadPlan
from apps.workload.models import WorkloadAssignment


class WorkloadPlanCrudTests(TestCase):

    def setUp(self):

        User = get_user_model()

        self.study_master = User.objects.create_user(
            email='study@example.com',
            password='password',
            role='STUDY_MASTER'
        )

        self.teacher = User.objects.create_user(
            email='teacher@example.com',
            password='password',
            role='TEACHER'
        )

    def test_study_master_can_create_workload_plan(self):

        self.client.login(
            email='study@example.com',
            password='password'
        )

        response = self.client.post(
            '/study-workload/plans/create/',
            {
                'кафедра': 'Кафедра информатики',
                'academic_year': '2025-2026',
                'total_hours': 720,
                'status': WorkloadPlan.Statuses.DRAFT
            }
        )

        self.assertRedirects(
            response,
            '/study-workload/'
        )

        self.assertTrue(
            WorkloadPlan.objects.filter(
                academic_year='2025-2026',
                total_hours=720
            ).exists()
        )

    def test_study_master_can_update_and_delete_workload_plan(self):

        self.client.login(
            email='study@example.com',
            password='password'
        )

        plan = WorkloadPlan.objects.create(
            кафедра='Кафедра математики',
            academic_year='2025-2026',
            total_hours=600,
            status=WorkloadPlan.Statuses.DRAFT
        )

        response = self.client.post(
            f'/study-workload/plans/{plan.id}/edit/',
            {
                'кафедра': 'Кафедра прикладной математики',
                'academic_year': '2026-2027',
                'total_hours': 800,
                'status': WorkloadPlan.Statuses.APPROVED
            }
        )

        self.assertRedirects(
            response,
            '/study-workload/'
        )

        plan.refresh_from_db()

        self.assertEqual(
            plan.academic_year,
            '2026-2027'
        )

        self.assertEqual(
            plan.total_hours,
            800
        )

        response = self.client.post(
            f'/study-workload/plans/{plan.id}/delete/'
        )

        self.assertRedirects(
            response,
            '/study-workload/'
        )

        self.assertFalse(
            WorkloadPlan.objects.filter(pk=plan.pk).exists()
        )

    def test_non_study_master_cannot_access_workload_plan_crud(self):

        self.client.login(
            email='teacher@example.com',
            password='password'
        )

        plan = WorkloadPlan.objects.create(
            кафедра='Кафедра физики',
            academic_year='2025-2026',
            total_hours=500,
            status=WorkloadPlan.Statuses.DRAFT
        )

        urls = (
            '/study-workload/',
            '/study-workload/plans/create/',
            f'/study-workload/plans/{plan.id}/',
            f'/study-workload/plans/{plan.id}/edit/',
            f'/study-workload/plans/{plan.id}/delete/',
        )

        for url in urls:

            response = self.client.get(url)

            self.assertEqual(
                response.status_code,
                302
            )


class StudyDirectoryCrudTests(TestCase):

    def setUp(self):

        User = get_user_model()

        self.study_master = User.objects.create_user(
            email='directory-study@example.com',
            password='password',
            role='STUDY_MASTER'
        )

        self.teacher_user = User.objects.create_user(
            email='directory-teacher@example.com',
            password='password',
            role='TEACHER'
        )

        self.other_user = User.objects.create_user(
            email='directory-other@example.com',
            password='password',
            role='TEACHER'
        )

    def test_study_master_can_create_directory_items(self):

        self.client.login(
            email='directory-study@example.com',
            password='password'
        )

        teacher_response = self.client.post(
            '/study-directories/teachers/create/',
            {
                'user': self.teacher_user.id,
                'full_name': 'Иванов Иван Иванович',
                'position': 'docent',
                'academic_degree': 'к.т.н.',
                'rate': '1.0',
                'max_hours': 900
            }
        )

        self.assertRedirects(
            teacher_response,
            '/study-directories/teachers/'
        )

        subject_response = self.client.post(
            '/study-directories/subjects/create/',
            {
                'name': 'Программирование',
                'hours': 144,
                'semester': 1,
                'control_type': 'exam'
            }
        )

        self.assertRedirects(
            subject_response,
            '/study-directories/subjects/'
        )

        group_response = self.client.post(
            '/study-directories/groups/create/',
            {
                'name': 'ИВТ-101',
                'course': 1,
                'direction': 'Информатика и вычислительная техника'
            }
        )

        self.assertRedirects(
            group_response,
            '/study-directories/groups/'
        )

        self.assertTrue(
            Teacher.objects.filter(full_name='Иванов Иван Иванович').exists()
        )

        self.assertTrue(
            Subject.objects.filter(name='Программирование').exists()
        )

        self.assertTrue(
            StudentGroup.objects.filter(name='ИВТ-101').exists()
        )

    def test_study_master_can_update_and_delete_subject(self):

        self.client.login(
            email='directory-study@example.com',
            password='password'
        )

        subject = Subject.objects.create(
            name='Математика',
            hours=120,
            semester=1,
            control_type='test'
        )

        response = self.client.post(
            f'/study-directories/subjects/{subject.id}/edit/',
            {
                'name': 'Высшая математика',
                'hours': 180,
                'semester': 2,
                'control_type': 'exam'
            }
        )

        self.assertRedirects(
            response,
            '/study-directories/subjects/'
        )

        subject.refresh_from_db()

        self.assertEqual(
            subject.name,
            'Высшая математика'
        )

        response = self.client.post(
            f'/study-directories/subjects/{subject.id}/delete/'
        )

        self.assertRedirects(
            response,
            '/study-directories/subjects/'
        )

        self.assertFalse(
            Subject.objects.filter(pk=subject.pk).exists()
        )

    def test_non_study_master_cannot_access_directories(self):

        self.client.login(
            email='directory-other@example.com',
            password='password'
        )

        urls = (
            '/study-directories/',
            '/study-directories/teachers/',
            '/study-directories/teachers/create/',
            '/study-directories/subjects/',
            '/study-directories/subjects/create/',
            '/study-directories/groups/',
            '/study-directories/groups/create/',
        )

        for url in urls:

            response = self.client.get(url)

            self.assertEqual(
                response.status_code,
                302
            )


class HeadWorkloadDistributionTests(TestCase):

    def setUp(self):

        User = get_user_model()

        self.head_user = User.objects.create_user(
            email='head@example.com',
            password='password',
            role='HEAD'
        )

        self.teacher_user = User.objects.create_user(
            email='teacher-load@example.com',
            password='password',
            role='TEACHER'
        )

        self.other_teacher_user = User.objects.create_user(
            email='teacher-second@example.com',
            password='password',
            role='TEACHER'
        )

        self.teacher_profile = Teacher.objects.create(
            user=self.teacher_user,
            full_name='Иванов Иван Иванович',
            position='docent',
            academic_degree='к.т.н.',
            rate='1.0',
            max_hours=200
        )

        self.second_teacher_profile = Teacher.objects.create(
            user=self.other_teacher_user,
            full_name='Петров Петр Петрович',
            position='assistant',
            academic_degree='',
            rate='1.0',
            max_hours=80
        )

        self.plan = WorkloadPlan.objects.create(
            кафедра='Кафедра информатики',
            academic_year='2025-2026',
            total_hours=300,
            status=WorkloadPlan.Statuses.DRAFT
        )

        self.subject = Subject.objects.create(
            name='Программирование',
            hours=120,
            semester=1,
            control_type='exam'
        )

        self.second_subject = Subject.objects.create(
            name='Базы данных',
            hours=90,
            semester=2,
            control_type='test'
        )

    def test_head_can_open_distribution_page(self):

        self.client.login(
            email='head@example.com',
            password='password'
        )

        response = self.client.get(
            '/workload/'
        )

        self.assertEqual(
            response.status_code,
            200
        )

        response = self.client.get(
            f'/workload/plans/{self.plan.id}/'
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.context['plan'],
            self.plan
        )

    def test_head_can_assign_subject_within_limits(self):

        self.client.login(
            email='head@example.com',
            password='password'
        )

        response = self.client.post(
            f'/workload/plans/{self.plan.id}/',
            {
                'subject': self.subject.id,
                'teacher': self.teacher_profile.id
            }
        )

        self.assertRedirects(
            response,
            f'/workload/plans/{self.plan.id}/'
        )

        assignment = WorkloadAssignment.objects.get(
            plan=self.plan,
            subject=self.subject
        )

        self.assertEqual(
            assignment.teacher,
            self.teacher_profile
        )

        self.assertEqual(
            assignment.assigned_hours,
            120
        )

    def test_head_cannot_assign_subject_if_teacher_limit_exceeded(self):

        self.client.login(
            email='head@example.com',
            password='password'
        )

        response = self.client.post(
            f'/workload/plans/{self.plan.id}/',
            {
                'subject': self.subject.id,
                'teacher': self.second_teacher_profile.id
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertFalse(
            WorkloadAssignment.objects.filter(
                plan=self.plan,
                subject=self.subject
            ).exists()
        )

    def test_head_can_approve_distribution(self):

        WorkloadAssignment.objects.create(
            plan=self.plan,
            teacher=self.teacher_profile,
            subject=self.subject,
            academic_year=self.plan.academic_year,
            semester=self.subject.semester,
            assigned_hours=self.subject.hours
        )

        self.client.login(
            email='head@example.com',
            password='password'
        )

        response = self.client.post(
            f'/workload/plans/{self.plan.id}/',
            {
                'approve_distribution': '1'
            }
        )

        self.assertRedirects(
            response,
            f'/workload/plans/{self.plan.id}/'
        )

        self.plan.refresh_from_db()

        self.assertEqual(
            self.plan.status,
            WorkloadPlan.Statuses.APPROVED
        )

        self.assertIsNotNone(
            self.plan.approved_at
        )


class TeacherMyWorkloadTests(TestCase):

    def setUp(self):

        User = get_user_model()

        self.teacher_user = User.objects.create_user(
            email='my-workload@example.com',
            password='password',
            role='TEACHER'
        )

        self.teacher_profile = Teacher.objects.create(
            user=self.teacher_user,
            full_name='Сидоров Сергей Сергеевич',
            position='senior_teacher',
            academic_degree='',
            rate='1.0',
            max_hours=700
        )

        self.plan = WorkloadPlan.objects.create(
            кафедра='Кафедра математики',
            academic_year='2025-2026',
            total_hours=400,
            status=WorkloadPlan.Statuses.DRAFT
        )

        self.subject = Subject.objects.create(
            name='Дискретная математика',
            hours=110,
            semester=1,
            control_type='exam'
        )

        WorkloadAssignment.objects.create(
            plan=self.plan,
            teacher=self.teacher_profile,
            subject=self.subject,
            academic_year=self.plan.academic_year,
            semester=self.subject.semester,
            assigned_hours=self.subject.hours
        )

    def test_teacher_can_open_my_workload_page(self):

        self.client.login(
            email='my-workload@example.com',
            password='password'
        )

        response = self.client.get(
            '/my-workload/'
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.context['total_hours'],
            110
        )

        self.assertContains(
            response,
            'Дискретная математика'
        )
