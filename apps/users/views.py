from datetime import timedelta
from urllib.parse import quote

import pyotp
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone

from apps.notifications.telegram import generate_telegram_bind_code
from apps.notifications.telegram import TELEGRAM_BIND_CODE_TTL_MINUTES
from apps.notifications.telegram import unbind_telegram_account
from apps.users.models import User


def is_2fa_eligible(user):

    return user.is_authenticated and user.role in (
        User.Roles.ADMIN,
        User.Roles.HEAD,
    )


two_fa_eligible_required = user_passes_test(
    is_2fa_eligible,
    login_url='/login/'
)


def get_role_redirect_url(user):

    if user.role == User.Roles.ADMIN:

        return '/admin-dashboard/'

    if user.role == User.Roles.HEAD:

        return '/head-dashboard/'

    if user.role == User.Roles.TEACHER:

        return '/teacher-dashboard/'

    if user.role == User.Roles.STUDY_MASTER:

        return '/study-dashboard/'

    return '/'


def login_view(request):

    if request.method == 'POST':

        email = request.POST.get('email')

        password = request.POST.get('password')

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:

            if (
                user.role in (
                    User.Roles.ADMIN,
                    User.Roles.HEAD,
                )
                and user.is_2fa_enabled
                and user.totp_secret
            ):

                request.session['pending_2fa_user_id'] = user.id

                request.session['pending_2fa_backend'] = getattr(
                    user,
                    'backend',
                    'django.contrib.auth.backends.ModelBackend'
                )

                return redirect('/2fa/verify/')

            login(request, user)

            return redirect(get_role_redirect_url(user))

        messages.error(
            request,
            'Неверный email или пароль'
        )

    return render(
        request,
        'auth/login.html'
    )


def totp_verify_view(request):

    pending_user_id = request.session.get('pending_2fa_user_id')

    if not pending_user_id:

        return redirect('/login/')

    pending_user = get_object_or_404(
        User,
        pk=pending_user_id
    )

    if request.method == 'POST':

        code = request.POST.get('code', '').strip()

        totp = pyotp.TOTP(pending_user.totp_secret)

        if totp.verify(code, valid_window=1):

            backend = request.session.get(
                'pending_2fa_backend',
                'django.contrib.auth.backends.ModelBackend'
            )

            login(
                request,
                pending_user,
                backend=backend
            )

            request.session.pop('pending_2fa_user_id', None)

            request.session.pop('pending_2fa_backend', None)

            return redirect(
                get_role_redirect_url(pending_user)
            )

        messages.error(
            request,
            'Неверный TOTP-код'
        )

    return render(
        request,
        'auth/totp_verify.html',
        {
            'email': pending_user.email
        }
    )


@login_required(login_url='/login/')
@two_fa_eligible_required
def totp_setup_view(request):

    pending_secret = request.session.get('pending_totp_secret')

    if not request.user.is_2fa_enabled and not pending_secret:

        pending_secret = pyotp.random_base32()

        request.session['pending_totp_secret'] = pending_secret

    active_secret = request.user.totp_secret or pending_secret

    provisioning_uri = None
    qr_code_url = None

    if active_secret:

        provisioning_uri = pyotp.TOTP(active_secret).provisioning_uri(
            name=request.user.email,
            issuer_name='DigitalChair'
        )

        qr_code_url = (
            'https://api.qrserver.com/v1/create-qr-code/'
            f'?size=220x220&data={quote(provisioning_uri)}'
        )

    if request.method == 'POST':

        if 'enable_2fa' in request.POST and not request.user.is_2fa_enabled:

            code = request.POST.get('code', '').strip()

            totp = pyotp.TOTP(active_secret)

            if totp.verify(code, valid_window=1):

                request.user.totp_secret = active_secret

                request.user.is_2fa_enabled = True

                request.user.save(
                    update_fields=[
                        'totp_secret',
                        'is_2fa_enabled'
                    ]
                )

                request.session.pop('pending_totp_secret', None)

                messages.success(
                    request,
                    'Двухфакторная аутентификация включена.'
                )

                return redirect('/2fa/setup/')

            messages.error(
                request,
                'Неверный код подтверждения.'
            )

        if 'disable_2fa' in request.POST and request.user.is_2fa_enabled:

            request.user.is_2fa_enabled = False

            request.user.totp_secret = None

            request.user.save(
                update_fields=[
                    'is_2fa_enabled',
                    'totp_secret'
                ]
            )

            request.session.pop('pending_totp_secret', None)

            messages.success(
                request,
                'Двухфакторная аутентификация отключена.'
            )

            return redirect('/2fa/setup/')

    return render(
        request,
        'auth/totp_setup.html',
        {
            'is_2fa_enabled': request.user.is_2fa_enabled,
            'totp_secret': active_secret,
            'qr_code_url': qr_code_url,
            'provisioning_uri': provisioning_uri,
        }
    )


def logout_view(request):

    request.session.pop('pending_2fa_user_id', None)

    request.session.pop('pending_2fa_backend', None)

    request.session.pop('pending_totp_secret', None)

    logout(request)

    return redirect('/login/')


@login_required(login_url='/login/')
def telegram_settings_view(request):

    bind_code = request.user.telegram_bind_code
    bind_expires_at = None

    if request.user.telegram_bind_code_created_at:

        bind_expires_at = (
            request.user.telegram_bind_code_created_at
            + timedelta(
                minutes=TELEGRAM_BIND_CODE_TTL_MINUTES
            )
        )

    if request.method == 'POST':

        if 'generate_code' in request.POST:

            bind_code = generate_telegram_bind_code(
                request.user
            )

            bind_expires_at = (
                request.user.telegram_bind_code_created_at
                + timedelta(
                    minutes=TELEGRAM_BIND_CODE_TTL_MINUTES
                )
            )

            messages.success(
                request,
                'Новый код привязки сгенерирован.'
            )

            return redirect('/telegram/')

        if 'unbind_telegram' in request.POST:

            unbind_telegram_account(
                request.user
            )

            messages.success(
                request,
                'Telegram-аккаунт отвязан.'
            )

            return redirect('/telegram/')

    return render(
        request,
        'notifications/telegram_settings.html',
        {
            'telegram_id': request.user.telegram_id,
            'bind_code': bind_code,
            'bind_expires_at': bind_expires_at,
        }
    )
