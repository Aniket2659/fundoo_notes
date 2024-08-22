
from django.urls import path
from .views import RegisterUserView,LoginUserView


urlpatterns = [
    path('register/',RegisterUserView.as_view(),name='sign in'),
    path('login/',LoginUserView.as_view(),name='login'),

    
]
