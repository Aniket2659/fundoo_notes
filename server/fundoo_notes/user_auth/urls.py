
from django.urls import path
from .views import RegisterUserView,LoginUserView,verify_registered_user,signin, signup, home


urlpatterns = [
    path('register/',RegisterUserView.as_view(),name='sign_in'),
    path('login/',LoginUserView.as_view(),name='login'),
    path('verify/<str:token>',verify_registered_user,name='verify'),
]
