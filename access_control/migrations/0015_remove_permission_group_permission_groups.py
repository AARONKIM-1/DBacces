# Generated by Django 5.0.7 on 2024-07-15 01:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0014_remove_permission_user_permissiongroup_users'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='permission',
            name='group',
        ),
        migrations.AddField(
            model_name='permission',
            name='groups',
            field=models.ManyToManyField(to='access_control.permissiongroup'),
        ),
    ]