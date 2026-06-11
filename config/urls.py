from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from apps.reports.views import (
    contingent_report_view,
    contingent_export_view,
    report_center_view,
    tasks_report_view,
    tasks_report_export_view,
    teacher_workload_report_view,
    teacher_workload_docx_export_view,
    teacher_workload_pdf_export_view,
    workload_execution_report_view,
    workload_execution_export_view,
    workload_summary_report_view,
    workload_summary_export_view
)
from apps.assignments.views import (
    my_task_detail_view,
    my_task_status_update_view,
    my_tasks_view,
    task_create_view,
    task_delete_view,
    task_detail_view,
    task_list_view,
    task_update_view
)
from apps.notifications.views import (
    notification_center_view
)

from apps.users.views import (
    login_view,
    logout_view,
    telegram_settings_view,
    totp_setup_view,
    totp_verify_view
)

from apps.core.views import (
    admin_dashboard,
    head_dashboard,
    teacher_dashboard,
    teacher_my_workload_view,
    study_dashboard,
    workload_view,
    workload_distribution_view,
    workload_assignment_delete_view,
    study_workload_view,
    workload_plan_create_view,
    workload_plan_detail_view,
    workload_plan_update_view,
    workload_plan_delete_view,
    import_center_view,
    import_template_download_view,
    study_directories_view,
    teacher_list_view,
    teacher_create_view,
    teacher_update_view,
    teacher_delete_view,
    subject_list_view,
    subject_create_view,
    subject_update_view,
    subject_delete_view,
    group_list_view,
    group_create_view,
    group_update_view,
    group_delete_view
)


urlpatterns = [

    path('admin/', admin.site.urls),

    path('login/', login_view),
    path('2fa/verify/', totp_verify_view),
    path('2fa/setup/', totp_setup_view),

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
        'my-workload/',
        teacher_my_workload_view
    ),
    path(
        'my-assignments/',
        my_tasks_view
    ),
    path(
        'my-assignments/<int:pk>/',
        my_task_detail_view
    ),
    path(
        'my-assignments/<int:pk>/status/',
        my_task_status_update_view
    ),
    path(
        'notifications/',
        notification_center_view
    ),
    path(
        'telegram/',
        telegram_settings_view
    ),
    path(
        'reports/',
        report_center_view
    ),
    path(
        'reports/workload-summary/',
        workload_summary_report_view
    ),
    path(
        'reports/workload-summary/export/xlsx/',
        workload_summary_export_view
    ),
    path(
        'reports/teacher-workload/',
        teacher_workload_report_view
    ),
    path(
        'reports/teacher-workload/export/docx/',
        teacher_workload_docx_export_view
    ),
    path(
        'reports/teacher-workload/export/pdf/',
        teacher_workload_pdf_export_view
    ),
    path(
        'reports/workload-execution/',
        workload_execution_report_view
    ),
    path(
        'reports/workload-execution/export/xlsx/',
        workload_execution_export_view
    ),
    path(
        'reports/tasks/',
        tasks_report_view
    ),
    path(
        'reports/tasks/export/xlsx/',
        tasks_report_export_view
    ),
    path(
        'reports/contingent/',
        contingent_report_view
    ),
    path(
        'reports/contingent/export/xlsx/',
        contingent_export_view
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
        'workload/plans/<int:pk>/',
        workload_distribution_view
    ),
    path(
        'workload/plans/<int:plan_pk>/assignments/<int:assignment_pk>/delete/',
        workload_assignment_delete_view
    ),
    path(
        'assignments/',
        task_list_view
    ),
    path(
        'assignments/create/',
        task_create_view
    ),
    path(
        'assignments/<int:pk>/',
        task_detail_view
    ),
    path(
        'assignments/<int:pk>/edit/',
        task_update_view
    ),
    path(
        'assignments/<int:pk>/delete/',
        task_delete_view
    ),
path(
    'study-workload/',
    study_workload_view
),
path(
    'study-workload/plans/create/',
    workload_plan_create_view
),
path(
    'study-workload/plans/<int:pk>/',
    workload_plan_detail_view
),
path(
    'study-workload/plans/<int:pk>/edit/',
    workload_plan_update_view
),
path(
    'study-workload/plans/<int:pk>/delete/',
    workload_plan_delete_view
),
path(
    'imports/',
    import_center_view
),
path(
    'imports/templates/<str:import_type>/',
    import_template_download_view
),
path(
    'study-directories/',
    study_directories_view
),
path(
    'study-directories/teachers/',
    teacher_list_view
),
path(
    'study-directories/teachers/create/',
    teacher_create_view
),
path(
    'study-directories/teachers/<int:pk>/edit/',
    teacher_update_view
),
path(
    'study-directories/teachers/<int:pk>/delete/',
    teacher_delete_view
),
path(
    'study-directories/subjects/',
    subject_list_view
),
path(
    'study-directories/subjects/create/',
    subject_create_view
),
path(
    'study-directories/subjects/<int:pk>/edit/',
    subject_update_view
),
path(
    'study-directories/subjects/<int:pk>/delete/',
    subject_delete_view
),
path(
    'study-directories/groups/',
    group_list_view
),
path(
    'study-directories/groups/create/',
    group_create_view
),
path(
    'study-directories/groups/<int:pk>/edit/',
    group_update_view
),
path(
    'study-directories/groups/<int:pk>/delete/',
    group_delete_view
),
path('', login_view),
]

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
