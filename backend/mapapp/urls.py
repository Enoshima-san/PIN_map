from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'items', views.MapItemViewSet, basename='mapitem')
router.register(r'comments', views.CommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', views.AuthView.as_view(), name='auth'),
    path('auth/toggle-moderator/', views.toggle_moderator, name='toggle-moderator'),
    path('routing/shortest-path/', views.shortest_path, name='shortest-path'),
]
