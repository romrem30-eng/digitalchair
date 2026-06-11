from apps.notifications.models import Notification


ROLE_META = {
    'ADMIN': {
        'label': 'Администратор',
        'home_url': '/admin-dashboard/',
        'theme_color': '#111827',
    },
    'HEAD': {
        'label': 'Заведующий кафедрой',
        'home_url': '/head-dashboard/',
        'theme_color': '#1e293b',
    },
    'STUDY_MASTER': {
        'label': 'Учебный отдел',
        'home_url': '/study-dashboard/',
        'theme_color': '#334155',
    },
    'TEACHER': {
        'label': 'Преподаватель',
        'home_url': '/teacher-dashboard/',
        'theme_color': '#0f172a',
    },
}


def build_role_navigation(role, notification_count):

    items_by_role = {
        'ADMIN': [
            {
                'label': 'Дашборд',
                'url': '/admin-dashboard/',
                'match_paths': ['/admin-dashboard/'],
            },
            {
                'label': 'Отчеты',
                'url': '/reports/',
                'match_paths': ['/reports/'],
            },
            {
                'label': 'Уведомления',
                'url': '/notifications/',
                'match_paths': ['/notifications/'],
                'badge': notification_count,
            },
            {
                'label': 'Telegram',
                'url': '/telegram/',
                'match_paths': ['/telegram/'],
            },
            {
                'label': '2FA',
                'url': '/2fa/setup/',
                'match_paths': ['/2fa/setup/'],
            },
        ],
        'HEAD': [
            {
                'label': 'Дашборд',
                'url': '/head-dashboard/',
                'match_paths': ['/head-dashboard/'],
            },
            {
                'label': 'Нагрузка',
                'url': '/workload/',
                'match_paths': ['/workload/'],
            },
            {
                'label': 'Поручения',
                'url': '/assignments/',
                'match_paths': ['/assignments/'],
            },
            {
                'label': 'Импорт',
                'url': '/imports/',
                'match_paths': ['/imports/'],
            },
            {
                'label': 'Отчеты',
                'url': '/reports/',
                'match_paths': ['/reports/'],
            },
            {
                'label': 'Уведомления',
                'url': '/notifications/',
                'match_paths': ['/notifications/'],
                'badge': notification_count,
            },
            {
                'label': 'Telegram',
                'url': '/telegram/',
                'match_paths': ['/telegram/'],
            },
            {
                'label': '2FA',
                'url': '/2fa/setup/',
                'match_paths': ['/2fa/setup/'],
            },
        ],
        'STUDY_MASTER': [
            {
                'label': 'Дашборд',
                'url': '/study-dashboard/',
                'match_paths': ['/study-dashboard/'],
            },
            {
                'label': 'Справочники',
                'url': '/study-directories/',
                'match_paths': ['/study-directories/'],
            },
            {
                'label': 'Нагрузка',
                'url': '/study-workload/',
                'match_paths': ['/study-workload/'],
            },
            {
                'label': 'Импорт',
                'url': '/imports/',
                'match_paths': ['/imports/'],
            },
            {
                'label': 'Отчеты',
                'url': '/reports/',
                'match_paths': ['/reports/'],
            },
            {
                'label': 'Уведомления',
                'url': '/notifications/',
                'match_paths': ['/notifications/'],
                'badge': notification_count,
            },
            {
                'label': 'Telegram',
                'url': '/telegram/',
                'match_paths': ['/telegram/'],
            },
        ],
        'TEACHER': [
            {
                'label': 'Дашборд',
                'url': '/teacher-dashboard/',
                'match_paths': ['/teacher-dashboard/'],
            },
            {
                'label': 'Моя нагрузка',
                'url': '/my-workload/',
                'match_paths': ['/my-workload/'],
            },
            {
                'label': 'Мои поручения',
                'url': '/my-assignments/',
                'match_paths': ['/my-assignments/'],
            },
            {
                'label': 'Отчеты',
                'url': '/reports/',
                'match_paths': ['/reports/'],
            },
            {
                'label': 'Уведомления',
                'url': '/notifications/',
                'match_paths': ['/notifications/'],
                'badge': notification_count,
            },
            {
                'label': 'Telegram',
                'url': '/telegram/',
                'match_paths': ['/telegram/'],
            },
        ],
    }

    return items_by_role.get(role, [])


def navigation_context(request):

    if not getattr(request, 'user', None) or not request.user.is_authenticated:

        return {}

    role = request.user.role

    role_meta = ROLE_META.get(
        role,
        {
            'label': role,
            'home_url': '/',
            'theme_color': '#111827',
        }
    )

    notification_count = Notification.objects.filter(
        recipient=request.user
    ).count()

    navigation_items = []

    for item in build_role_navigation(role, notification_count):

        navigation_items.append(
            {
                **item,
                'is_active': any(
                    request.path.startswith(prefix)
                    for prefix in item['match_paths']
                )
            }
        )

    return {
        'ui_role_label': role_meta['label'],
        'ui_home_url': role_meta['home_url'],
        'ui_theme_color': role_meta['theme_color'],
        'ui_navigation_items': navigation_items,
        'ui_notification_count': notification_count,
    }
