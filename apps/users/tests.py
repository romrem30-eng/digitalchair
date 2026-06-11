import pyotp
from django.contrib.auth import get_user_model
from django.test import TestCase


class TwoFactorAuthTests(TestCase):

    def setUp(self):

        User = get_user_model()

        self.admin_user = User.objects.create_user(
            email='admin-2fa@example.com',
            password='password',
            role='ADMIN'
        )

        self.head_user = User.objects.create_user(
            email='head-2fa@example.com',
            password='password',
            role='HEAD'
        )

        self.teacher_user = User.objects.create_user(
            email='teacher-2fa@example.com',
            password='password',
            role='TEACHER'
        )

    def test_enable_2fa(self):

        self.client.force_login(self.admin_user)

        response = self.client.get('/2fa/setup/')

        self.assertEqual(response.status_code, 200)

        secret = self.client.session.get('pending_totp_secret')

        self.assertIsNotNone(secret)

        code = pyotp.TOTP(secret).now()

        response = self.client.post(
            '/2fa/setup/',
            {
                'enable_2fa': '1',
                'code': code
            }
        )

        self.assertRedirects(response, '/2fa/setup/')

        self.admin_user.refresh_from_db()

        self.assertTrue(self.admin_user.is_2fa_enabled)
        self.assertEqual(self.admin_user.totp_secret, secret)

    def test_successful_login_with_correct_totp_code(self):

        secret = pyotp.random_base32()

        self.head_user.is_2fa_enabled = True
        self.head_user.totp_secret = secret
        self.head_user.save()

        response = self.client.post(
            '/login/',
            {
                'email': 'head-2fa@example.com',
                'password': 'password'
            }
        )

        self.assertRedirects(response, '/2fa/verify/')

        code = pyotp.TOTP(secret).now()

        response = self.client.post(
            '/2fa/verify/',
            {
                'code': code
            }
        )

        self.assertRedirects(response, '/head-dashboard/')

    def test_login_fails_with_invalid_totp_code(self):

        secret = pyotp.random_base32()

        self.head_user.is_2fa_enabled = True
        self.head_user.totp_secret = secret
        self.head_user.save()

        self.client.post(
            '/login/',
            {
                'email': 'head-2fa@example.com',
                'password': 'password'
            }
        )

        response = self.client.post(
            '/2fa/verify/',
            {
                'code': '000000'
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверный TOTP-код')

    def test_disable_2fa(self):

        self.admin_user.is_2fa_enabled = True
        self.admin_user.totp_secret = pyotp.random_base32()
        self.admin_user.save()

        self.client.force_login(self.admin_user)

        response = self.client.post(
            '/2fa/setup/',
            {
                'disable_2fa': '1'
            }
        )

        self.assertRedirects(response, '/2fa/setup/')

        self.admin_user.refresh_from_db()

        self.assertFalse(self.admin_user.is_2fa_enabled)
        self.assertIsNone(self.admin_user.totp_secret)
