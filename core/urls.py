# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.auth_view, name='auth_page'),
    path('logout/', views.logout_view, name='logout'),
    path('worker/dashboard/', views.worker_dashboard_view, name='worker_dashboard'),
    path('official/dashboard/', views.official_dashboard_view, name='official_dashboard'),

    # Add this new line for the API
    path('api/submit-report/', views.submit_health_report_api, name='submit_health_report_api'),
    # core/urls.py
# ... inside urlpatterns list
path('serviceworker.js', views.service_worker_view, name='serviceworker'),
path('api/water-quality/', views.water_quality_api, name='water_quality_api'),
path('api/dashboard-data/', views.dashboard_data_api, name='dashboard_data_api'),
]