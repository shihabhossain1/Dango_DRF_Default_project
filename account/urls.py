from django.urls import path
from .views import *

urlpatterns = [
    #auth
    path('register/', RegisterView.as_view(), name='register'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    path('countries/', CountryListView.as_view(), name='country_list'),  # List all countries
    path('cities/', CityListCreateAPIView.as_view(), name='city_list_create'),
    path('cities/<int:pk>/', CityDetailAPIView.as_view(), name='city_detail'),

    path('profile/', ProfileGetView.as_view(), name='profile-get'),  # GET request to retrieve profile
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change-password'),


]