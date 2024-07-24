from django.urls import path

from access_control.object_search_view import object_explorer, view_table_data
from . import views
from . import edr_view
from django.conf import settings
from django.conf.urls.static import static


app_name = 'access_control'
urlpatterns = [
    path('execute_query/<int:db_id>/', views.execute_query, name='execute_query'),
    path('commit/<int:query_id>/', views.commit_transaction, name='commit_transaction'),
    path('rollback/<int:query_id>/', views.rollback_transaction, name='rollback_transaction'),
    path('databases/', views.database_list, name='database_list'),
    path('edr_view/<int:db_id>/', edr_view.edr_view, name='edr_view'),
    path('object_explorer/<int:db_id>/', object_explorer, name='object_explorer'),
    path('view_table_data/<int:db_id>/<str:table_name>/', view_table_data, name='view_table_data'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

