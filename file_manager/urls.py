# file_manager/urls.py
from django.urls import path
from . import views
from . import views_execution

urlpatterns = [
    path('', views.index, name='index'),
    path('edit/<path:path>/', views.edit_file, name='edit_file'),
    path('execute/<path:path>/', views_execution.execute_code_view, name='execute_code_view'),
    path('api/execute/', views_execution.execute_code, name='execute_code'),
    path('api/file-operations/', views.api_file_operations, name='api_file_operations'),
    path('download/', views.download_file, name='download_file'),
]