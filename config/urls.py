from django.contrib import admin
from django.urls import path


from apps.users.views import (
    login_view,
    logout_view
)

from apps.core.views import (
    admin_dashboard,
    head_dashboard,
    teacher_dashboard,
    study_dashboard,
    workload_view,
    study_workload_view
)


urlpatterns = [

    path('admin/', admin.site.urls),

    path('login/', login_view),

    path('logout/', logout_view),

    path(
        'admin-dashboard/',
        admin_dashboard
    ),

    path(
        'head-dashboard/',
        head_dashboard
    ),

    path(
        'teacher-dashboard/',
        teacher_dashboard
    ),

    path(
        'study-dashboard/',
        study_dashboard
    ),
    path(
        'workload/',
        workload_view
    ),
path(
    'study-workload/',
    study_workload_view
),
path('', login_view),
]