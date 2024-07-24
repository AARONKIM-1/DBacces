# Generated by Django 5.0.7 on 2024-07-15 00:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0010_query_query_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='permissiongroup',
            old_name='can_ddl',
            new_name='can_alter_table',
        ),
        migrations.RenameField(
            model_name='permissiongroup',
            old_name='can_delete',
            new_name='can_create_index',
        ),
        migrations.RenameField(
            model_name='permissiongroup',
            old_name='can_execute',
            new_name='can_create_table',
        ),
        migrations.RenameField(
            model_name='permissiongroup',
            old_name='can_insert',
            new_name='can_delete_all',
        ),
        migrations.RenameField(
            model_name='permissiongroup',
            old_name='can_select',
            new_name='can_delete_specific_rows',
        ),
        migrations.RenameField(
            model_name='permissiongroup',
            old_name='can_update',
            new_name='can_drop_index',
        ),
        migrations.AddField(
            model_name='permissiongroup',
            name='can_drop_table',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='permissiongroup',
            name='can_execute_function',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='permissiongroup',
            name='can_execute_procedure',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='permissiongroup',
            name='can_insert_all',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='permissiongroup',
            name='can_insert_specific_columns',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='permissiongroup',
            name='can_select_all',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='permissiongroup',
            name='can_select_specific_columns',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='permissiongroup',
            name='can_update_all',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='permissiongroup',
            name='can_update_specific_columns',
            field=models.BooleanField(default=False),
        ),
    ]