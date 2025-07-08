from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('features/', views.features_view, name='features'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('contact/', views.contact_view, name='contact'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('about/', views.about_view, name='about'),
    path('terms/', views.terms_view, name='terms'),
    path('password-reset/', views.reset_password_view, name='reset_password'),
    path("dashboard/<str:rqd_user_id>/", views.dashboard_view, name="dashboard"),
    path('update-visibility/', views.update_visibility, name='update_visibility'),
    path('update-username/',views.update_username,name="update-username"),
    path('verify/<str:platform_name>/', views.verify_platform, name='verify_platform'),
    path('search/', views.search, name='search'),
    path('delete-platform/<str:platform_name>/', views.delete_platform, name='delete_platform'),
    path('delete-user/<str:id>',views.delete_user,name='delete-user'),

]