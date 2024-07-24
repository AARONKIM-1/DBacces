# Generated by Django 5.0.7 on 2024-07-15 01:38

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0015_remove_permission_group_permission_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]