import json
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import connections, OperationalError, transaction, DatabaseError, IntegrityError,connection
from .models import Database, Permission, PermissionGroup, Query
from .forms import QueryForm
from django.db.transaction import TransactionManagementError  # 여기서 가져옴
from django.urls import reverse, NoReverseMatch
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 이것을 추가하여 GUI 백엔드가 아닌 Agg 백엔드를 사용

def check_user_permission(user, database, query_text):
    permissions = Permission.objects.filter(database=database, users=user)
    if not permissions.exists():
        return False

    query_lower = query_text.strip().lower()
    for permission in permissions:
        for permission_group in permission.groups.all():

            if query_lower.startswith('select'):
                if ' from ' in query_lower:
                    return permission_group.can_select_all
                else:
                    return permission_group.can_select_specific_columns

            if query_lower.startswith('insert'):
                if ' into ' in query_lower:
                    return permission_group.can_insert_all
                else:
                    return permission_group.can_insert_specific_columns

            if query_lower.startswith('update'):
                if ' set ' in query_lower:
                    return permission_group.can_update_all
                else:
                    return permission_group.can_update_specific_columns

            if query_lower.startswith('delete'):
                if ' from ' in query_lower:
                    return permission_group.can_delete_all
                else:
                    return permission_group.can_delete_specific_rows

            if query_lower.startswith('create '):
                return permission_group.can_create_table

            if query_lower.startswith('alter table'):
                return permission_group.can_alter_table

            if query_lower.startswith('drop table'):
                return permission_group.can_drop_table

            if query_lower.startswith('create index'):
                return permission_group.can_create_index

            if query_lower.startswith('drop index'):
                return permission_group.can_drop_index

            if query_lower.startswith('call'):
                return permission_group.can_execute_procedure

            if query_lower.startswith('select') and ' from ' in query_lower:
                return permission_group.can_select_all

    return False

#access_control

@login_required
def execute_query(request, db_id):
    db = get_object_or_404(Database, id=db_id)
    tables = get_tables_list(db)
    db_connection = connections[db.name]

    # 사용자의 권한 그룹 가져오기
    user_permission_groups = PermissionGroup.objects.filter(permission__users=request.user, permission__database=db)

    if request.method == "POST":
        form = QueryForm(request.POST)
        if form.is_valid():
            query_instance = form.save(commit=False)
            query_instance.user = request.user
            query_instance.database = db

            query_text = query_instance.query_text.strip().lower()
            # 복호화 쿼리 차단
            if 'decrypt' in query_text:
                query_instance.success = False
                query_instance.error_message = 'Decryption queries are not allowed.'
                query_instance.save()
                return render(request, 'access_control/execute_query.html', {'form': form, 'database': db, 'query': query_instance, 'tables': tables})

            # 쿼리 유형에 따라 필요한 권한 확인
            permission_mapping = {
                'select': 'can_select_all',
                'insert': 'can_insert_all',
                'update': 'can_update_all',
                'delete': 'can_delete_all',
                'create': 'can_create_table',
                'alter': 'can_alter_table',
                'drop': 'can_drop_table'
            }

            query_type = query_text.split()[0]
            required_permission = permission_mapping.get(query_type)

            if required_permission and not user_permission_groups.filter(**{required_permission: True}).exists():
                query_instance.success = False
                query_instance.error_message = 'You do not have the required permissions to execute this query.'
                query_instance.save()
            else:
                try:
                    with db_connection.cursor() as cursor:
                        cursor.execute("SET autocommit=0")  # 자동 커밋 모드 비활성화
                        cursor.execute("SAVEPOINT my_savepoint")
                        cursor.execute(query_instance.query_text)
                        if query_text.startswith('select'):
                            query_instance.result = cursor.fetchall()
                            query_instance.columns = [col[0] for col in cursor.description]
                        query_instance.success = True
                        cursor.execute("COMMIT")  # 트랜잭션 커밋
                except (OperationalError, IntegrityError, DatabaseError) as e:
                    try:
                        with db_connection.cursor() as cursor:
                            cursor.execute("ROLLBACK TO SAVEPOINT my_savepoint")
                        query_instance.success = False
                        query_instance.error_message = f"Error: {str(e)}"
                    except Exception as rollback_error:
                        query_instance.success = False
                        query_instance.error_message = f"Error: {str(e)} | Rollback Error: {str(rollback_error)}"
                except Exception as e:
                    query_instance.success = False
                    query_instance.error_message = f"Unexpected Error: {str(e)}"
                finally:
                    with db_connection.cursor() as cursor:
                        cursor.execute("SET autocommit=1")  # 자동 커밋 모드 재활성화
                    query_instance.save()

            return render(request, 'access_control/execute_query.html', {'form': form, 'database': db, 'query': query_instance, 'tables': tables})
    else:
        form = QueryForm()

    query_history = Query.objects.filter(database=db, user=request.user).order_by('-executed_at')

    return render(request, 'access_control/execute_query.html', {'form': form, 'database': db, 'tables': tables, 'query_history': query_history})

@login_required
def commit_transaction(request, query_id):
    query_instance = get_object_or_404(Query, id=query_id)
    connection = connections[query_instance.database.name]

    try:
        with connection.cursor() as cursor:
            cursor.execute("COMMIT")
        query_instance.success = True
        query_instance.is_committed = True
        query_instance.query_text = "COMMIT"
    except OperationalError as e:
        query_instance.success = False
        query_instance.error_message = str(e)
    finally:
        query_instance.save()

    redirect_url = reverse('access_control:execute_query', args=[query_instance.database.id])
    print(f"Redirecting to: {redirect_url}")
    return redirect(redirect_url)

@login_required
def rollback_transaction(request, query_id):
    query_instance = get_object_or_404(Query, id=query_id)
    connection = connections[query_instance.database.name]

    try:
        with connection.cursor() as cursor:
            cursor.execute("ROLLBACK")
        query_instance.success = True
        query_instance.query_text = "ROLLBACK"
    except OperationalError as e:
        query_instance.success = False
        query_instance.error_message = str(e)
    finally:
        query_instance.save()

    redirect_url = reverse('access_control:execute_query', args=[query_instance.database.id])
    print(f"Rollback redirecting to: {redirect_url}")
    return redirect(redirect_url)


def get_tables_list(db):
    connection = connections[db.name]
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        return [row[0] for row in cursor.fetchall()]


@login_required
def database_list(request):
    user_permissions = Permission.objects.filter(users=request.user)
    accessible_databases = [permission.database for permission in user_permissions]
    return render(request, 'access_control/database_list.html', {'databases': accessible_databases})



#otp 
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django_otp.decorators import otp_required

@login_required
@otp_required
def home(request):
    return render(request, 'home.html')



from django.contrib.auth.views import LoginView as BaseLoginView
from django.shortcuts import redirect
from two_factor.forms import AuthenticationTokenForm
from django_otp.plugins.otp_totp.models import TOTPDevice


class CustomLoginView(BaseLoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.get_user()

        # OTP 토큰 확인
        otp_token = self.request.POST.get('otp_token')
        if otp_token:
            device = TOTPDevice.objects.filter(user=user).first()
            otp_form = AuthenticationTokenForm(user=user, initial_device=device, data={'otp_token': otp_token})
            if otp_form.is_valid():
                return response
            else:
                form.add_error(None, "Invalid OTP Token")
        return self.form_invalid(form)
