from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import connection
from django.contrib.gis.geos import Point
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .models import MapItem, Comment, Profile, Verification, RoadEdge
from .serializers import (
    MapItemSerializer, MapItemCreateSerializer, MapItemGeoSerializer,
    CommentSerializer, UserSerializer,
)


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        profile = getattr(request.user, 'profile', None)
        return profile and profile.is_moderator or request.user.is_staff


class MapItemViewSet(viewsets.ModelViewSet):
    queryset = MapItem.objects.select_related('author').prefetch_related('comments')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['item_type', 'status', 'category', 'privacy', 'activity_type']
    search_fields = ['title', 'address', 'description']

    def get_serializer_class(self):
        if self.action == 'create':
            return MapItemCreateSerializer
        return MapItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Публичный каталог — только approved
        if self.action in ('list', 'retrieve', 'geojson') and not self.request.query_params.get('mine'):
            user = self.request.user
            if user.is_authenticated:
                profile = getattr(user, 'profile', None)
                if profile and profile.is_moderator:
                    return qs  # модератор видит всё
            return qs.filter(status='approved')
        if self.request.query_params.get('mine') and self.request.user.is_authenticated:
            return qs.filter(author=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        qs = self.filter_queryset(self.get_queryset().filter(location__isnull=False))
        serializer = MapItemGeoSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def verify(self, request, pk=None):
        item = self.get_object()
        if Verification.objects.filter(map_item=item, user=request.user).exists():
            return Response({'detail': 'Вы уже подтвердили этот объект'}, status=400)
        Verification.objects.create(map_item=item, user=request.user)
        item.verifications += 1
        item.save(update_fields=['verifications'])
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.verified_count += 1
        profile.save(update_fields=['verified_count'])
        return Response({'verifications': item.verifications})

    @action(detail=True, methods=['post'], permission_classes=[IsModerator])
    def approve(self, request, pk=None):
        item = self.get_object()
        item.status = 'approved'
        item.save(update_fields=['status'])
        return Response(MapItemSerializer(item, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsModerator])
    def reject(self, request, pk=None):
        item = self.get_object()
        item.status = 'rejected'
        item.save(update_fields=['status'])
        return Response(MapItemSerializer(item, context={'request': request}).data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Comment.objects.select_related('author', 'map_item')
        item_id = self.request.query_params.get('map_item')
        if item_id:
            qs = qs.filter(map_item_id=item_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user and not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class AuthView(APIView):
    def post(self, request):
        """Login or register (simplified)."""
        action = request.data.get('action', 'login')
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if not email or not password:
            return Response({'detail': 'Email и пароль обязательны'}, status=400)

        if action == 'register':
            if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
                return Response({'detail': 'Пользователь уже существует'}, status=400)
            user = User.objects.create_user(username=email, email=email, password=password)
            Profile.objects.create(user=user)
            login(request, user)
            return Response(UserSerializer(user).data)

        # login
        user = authenticate(username=email, password=password)
        if not user:
            # try by email
            try:
                u = User.objects.get(email=email)
                user = authenticate(username=u.username, password=password)
            except User.DoesNotExist:
                pass
        if not user:
            return Response({'detail': 'Неверный email или пароль'}, status=400)
        login(request, user)
        Profile.objects.get_or_create(user=user)
        return Response(UserSerializer(user).data)

    def delete(self, request):
        logout(request)
        return Response({'detail': 'ok'})

    def get(self, request):
        if request.user.is_authenticated:
            Profile.objects.get_or_create(user=request.user)
            return Response(UserSerializer(request.user).data)
        return Response({'detail': 'anonymous'}, status=401)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_moderator(request):
    """Переключение роли модератора (для демо, как toggleRole в оригинале)."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.is_moderator = not profile.is_moderator
    profile.save(update_fields=['is_moderator'])
    return Response(UserSerializer(request.user).data)


@api_view(['GET'])
def shortest_path(request):
    """
    Пример использования pgRouting: кратчайший путь между двумя точками.
    Query params: lat1, lng1, lat2, lng2
    Требует заполненной таблицы mapapp_roadedge + топологии pgr.
    """
    try:
        lat1 = float(request.query_params['lat1'])
        lng1 = float(request.query_params['lng1'])
        lat2 = float(request.query_params['lat2'])
        lng2 = float(request.query_params['lng2'])
    except (KeyError, ValueError):
        return Response({'detail': 'Нужны lat1,lng1,lat2,lng2'}, status=400)

    # Находим ближайшие вершины (упрощённо — через closest edge)
    sql = """
    WITH start_pt AS (
        SELECT id FROM mapapp_roadedge
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326) LIMIT 1
    ),
    end_pt AS (
        SELECT id FROM mapapp_roadedge
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326) LIMIT 1
    )
    SELECT seq, node, edge, cost, agg_cost
    FROM pgr_dijkstra(
        'SELECT id, source, target, cost, reverse_cost FROM mapapp_roadedge',
        (SELECT source FROM mapapp_roadedge WHERE id = (SELECT id FROM start_pt)),
        (SELECT target FROM mapapp_roadedge WHERE id = (SELECT id FROM end_pt)),
        directed := false
    );
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, [lng1, lat1, lng2, lat2])
            rows = cursor.fetchall()
        path = [{'seq': r[0], 'node': r[1], 'edge': r[2], 'cost': r[3], 'agg_cost': r[4]} for r in rows]
        return Response({'path': path, 'note': 'Требует загруженной дорожной сети и pgr_createTopology'})
    except Exception as e:
        return Response({
            'detail': 'pgRouting недоступен или таблица рёбер пуста',
            'error': str(e),
            'hint': 'Загрузите OSM через osm2pgrouting и выполните pgr_createTopology'
        }, status=503)
