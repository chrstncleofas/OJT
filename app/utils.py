from app.models import StoreActivityLogs
from datetime import datetime

def saveActivityLogs(user, action, request, description) -> None:
    """
    Save activity logs to the database.
    :param user: The user who performed the action
    :param action: The action performed
    :param description: Additional details about the action
    """
    ip_address = request.META.get('REMOTE_ADDR')
    first_name = user.first_name
    last_name = user.last_name
    position = user.position

    StoreActivityLogs.objects.create(
        user=user,
        first_name=first_name,
        last_name=last_name,
        position=position,
        action=action,
        ip_address=ip_address,
        description=description
    )
