# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import LabelViewSet , LabelAPIView

# router = DefaultRouter()
# # router.register(r'', LabelViewSet, basename='label')
# router.register(r'raw', LabelAPIView, basename='raw-label')

# urlpatterns = [
#     path('', include(router.urls)),
# ]

from django.urls import path
from .views import LabelListCreateAPIView, LabelDetailAPIView

urlpatterns = [
    path('labels/', LabelListCreateAPIView.as_view(), name='label-list-create'),
    path('labels/<int:label_id>/', LabelDetailAPIView.as_view(), name='label-detail'),
]




