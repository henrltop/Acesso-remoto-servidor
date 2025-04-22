# file_manager/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('edit/<path:path>/', views.edit_file, name='edit_file'),
    path('api/file-operations/', views.api_file_operations, name='api_file_operations'),
    path('download/', views.download_file, name='download_file'),
]