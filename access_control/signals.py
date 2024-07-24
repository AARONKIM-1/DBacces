from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from db_access_control import settings
from .models import UserBehavior
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from .models import Database
from .utils import load_databases

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    UserBehavior.objects.create(user=user, username=user.username, action='login', ip_address=ip)

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    UserBehavior.objects.create(user=user, username=user.username, action='logout', ip_address=ip)

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    username = credentials.get('username', 'Unknown user')
    user = User.objects.filter(username=username).first()
    UserBehavior.objects.create(user=user, username=username, action='login_failed', ip_address=ip)

@receiver(post_save, sender=Database)
def update_databases(sender, **kwargs):
    settings.DATABASES.update(load_databases())
