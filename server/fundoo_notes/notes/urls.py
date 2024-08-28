from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotesViewSet


router = DefaultRouter()
router.register(r'', NotesViewSet ,basename="note")

urlpatterns = [
    path('', include(router.urls)),
]