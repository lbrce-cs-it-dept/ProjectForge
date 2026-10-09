from .models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {
            "unread_notification_count": 0,
        }

    unread_notification_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    return {
        "unread_notification_count": unread_notification_count,
    }
