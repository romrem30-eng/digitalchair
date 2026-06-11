from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.shortcuts import render

from apps.notifications.models import Notification


@login_required(login_url='/login/')
@never_cache
def notification_center_view(request):

    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related(
        'task'
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'notifications/notification_center.html',
        {
            'notifications': notifications
        }
    )
