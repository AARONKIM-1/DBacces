from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User,Group
from django_otp.plugins.otp_totp.models import TOTPDevice

from django.urls import path, reverse
from django.http import HttpResponseRedirect
from .models import AllowedIP, Database, PermissionGroup, Permission, Query, UserBehavior

class MyAdminSite(admin.AdminSite):
    site_header = "DB Solution Admin"
    site_title = "DB Solution"
    index_title = "Welcome to the DB Solution Admin"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('execute_query/', self.admin_view(self.execute_query_view), name='execute_query'),
        ]
        return custom_urls + urls

    def execute_query_view(self, request):
        return HttpResponseRedirect(reverse('access_control:database_list'))

    def each_context(self, request):
        context = super().each_context(request)
        context['custom_menu_items'] = [
            {'name': 'Execute Query', 'url': reverse('admin:execute_query')}
        ]
        return context


admin_site = MyAdminSite(name='myadmin')

class PermissionInline(admin.TabularInline):
    model = Permission
    extra = 1

class DatabaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'db_type', 'user', 'host', 'port', 'status')
    readonly_fields = ('status',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['password'].widget.attrs['type'] = 'password'
        return form

    def save_model(self, request, obj, form, change):
        obj.save()

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('user', 'database', 'query_type', 'timestamp', 'success')
    list_filter = ('user', 'timestamp')

    readonly_fields = ('user', 'database', 'query_text', 'query_type', 'success', 'error_message', 'result', 'is_committed', 'executed_at', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

class PermissionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

    # fieldsets = (
    #     (None, {
    #         'fields': ('name', 'description')
    #     }),
    #     ('SELECT Permissions', {
    #         'fields': ('can_select_all', 'can_select_specific_columns')
    #     }),
    #     ('INSERT Permissions', {
    #         'fields': ('can_insert_all', 'can_insert_specific_columns')
    #     }),
    #     ('UPDATE Permissions', {
    #         'fields': ('can_update_all', 'can_update_specific_columns')
    #     }),
    #     ('DELETE Permissions', {
    #         'fields': ('can_delete_all', 'can_delete_specific_rows')
    #     }),
    #     ('DDL Permissions', {
    #         'fields': ('can_create_table', 'can_alter_table', 'can_drop_table', 'can_create_index', 'can drop_index')
    #     }),
    #     ('Other Permissions', {
    #         'fields': ('can_execute_procedure', 'can_execute_function')
    #     }),
    # )

class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ('username', 'timestamp', 'action', 'ip_address')
    list_filter = ('user', 'timestamp')
    readonly_fields = ('username', 'timestamp', 'action', 'ip_address')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

class AllowedIPAdmin(admin.ModelAdmin):
    list_display = ('ip_address',)

class AllowedMACAdmin(admin.ModelAdmin):
    list_display = ('mac_address',)


from django.utils.html import mark_safe
import qrcode
import base64
from io import BytesIO

class TOTPDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'confirmed', 'throttling_failure_timestamp', 'qr_code')
    search_fields = ('user__username', 'name')
    list_filter = ('confirmed', 'throttling_failure_timestamp')

    def qr_code(self, obj):
        qr_url = obj.config_url
        qr_image = qrcode.make(qr_url)
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return mark_safe(f'<img src="data:image/png;base64,{img_str}" width="150" height="150" />')

    qr_code.short_description = 'QR Code'


# Custom admin site 사용
admin.site.unregister(User)
admin.site.unregister(Group)

admin_site.register(TOTPDevice,TOTPDeviceAdmin)
admin_site.register(Group)
admin_site.register(User, BaseUserAdmin)
admin_site.register(Database, DatabaseAdmin)
admin_site.register(Query, QueryAdmin)
admin_site.register(PermissionGroup, PermissionGroupAdmin)
admin_site.register(UserBehavior, UserBehaviorAdmin)
admin_site.register(AllowedIP, AllowedIPAdmin)



# 원격접근 로깅
from .models import RemoteLog
class RemoteLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_host', 'command_type', 'argument')
    list_filter = ('timestamp', 'user_host', 'command_type')

admin_site.register(RemoteLog, RemoteLogAdmin)