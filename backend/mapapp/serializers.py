from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point, LineString
from .models import MapItem, Comment, Profile, Verification


class UserSerializer(serializers.ModelSerializer):
    is_moderator = serializers.SerializerMethodField()
    added_count = serializers.SerializerMethodField()
    verified_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_moderator', 'added_count', 'verified_count')

    def get_is_moderator(self, obj):
        return getattr(getattr(obj, 'profile', None), 'is_moderator', False)

    def get_added_count(self, obj):
        return getattr(getattr(obj, 'profile', None), 'added_count', 0)

    def get_verified_count(self, obj):
        return getattr(getattr(obj, 'profile', None), 'verified_count', 0)


class CommentSerializer(serializers.ModelSerializer):
    author_email = serializers.CharField(source='author.email', read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'author', 'author_email', 'text', 'created_at')
        read_only_fields = ('author', 'created_at')


class MapItemSerializer(serializers.ModelSerializer):
    """Обычный сериализатор (не GeoJSON) — удобнее для списка + деталей."""
    author_email = serializers.CharField(source='author.email', read_only=True, default='')
    comments = CommentSerializer(many=True, read_only=True)
    lat = serializers.FloatField(read_only=True)
    lng = serializers.FloatField(read_only=True)
    track_coordinates = serializers.SerializerMethodField()
    image_display = serializers.SerializerMethodField()

    class Meta:
        model = MapItem
        fields = (
            'id', 'item_type', 'title', 'description', 'status',
            'author', 'author_email', 'verifications', 'address',
            'location', 'track', 'lat', 'lng', 'track_coordinates',
            'category', 'privacy', 'activity_type', 'duration_minutes',
            'image', 'image_url', 'image_display',
            'comments', 'created_at', 'updated_at',
        )
        read_only_fields = ('author', 'verifications', 'status', 'created_at', 'updated_at')

    def get_track_coordinates(self, obj):
        if obj.track:
            # LineString coords as [[lat, lng], ...] for Leaflet
            return [[y, x] for x, y in obj.track.coords]
        return None

    def get_image_display(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return obj.image_url or None

    def create(self, validated_data):
        request = self.context.get('request')
        # location / track приходят как GeoJSON или как lat/lng + points
        return super().create(validated_data)


class MapItemCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания: принимает lat/lng или массив точек."""
    lat = serializers.FloatField(required=False, write_only=True)
    lng = serializers.FloatField(required=False, write_only=True)
    track_points = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2),
        required=False, write_only=True,
        help_text='[[lat, lng], [lat, lng], ...]'
    )

    class Meta:
        model = MapItem
        fields = (
            'item_type', 'title', 'description', 'address',
            'category', 'privacy', 'activity_type', 'duration_minutes',
            'image', 'image_url',
            'lat', 'lng', 'track_points',
        )

    def validate(self, data):
        item_type = data.get('item_type')
        if item_type == 'object':
            if 'lat' not in data or 'lng' not in data:
                raise serializers.ValidationError('Для объекта нужны lat и lng')
        elif item_type == 'route':
            pts = data.get('track_points') or []
            if len(pts) < 2:
                raise serializers.ValidationError('Для маршрута нужно минимум 2 точки')
        return data

    def create(self, validated_data):
        lat = validated_data.pop('lat', None)
        lng = validated_data.pop('lng', None)
        track_points = validated_data.pop('track_points', None)
        request = self.context['request']

        item = MapItem(**validated_data)
        item.author = request.user if request.user.is_authenticated else None
        item.status = 'pending'

        if item.item_type == 'object' and lat is not None and lng is not None:
            item.location = Point(lng, lat, srid=4326)
            if not item.address:
                item.address = f'Координаты: {lat:.5f}, {lng:.5f}'
        elif item.item_type == 'route' and track_points:
            # Leaflet: [lat, lng] → GEOS: (lng, lat)
            coords = [(p[1], p[0]) for p in track_points]
            item.track = LineString(coords, srid=4326)
            item.location = Point(coords[0][0], coords[0][1], srid=4326)
            if not item.address:
                item.address = f'Составной маршрут ({len(track_points)} точек)'

        item.save()
        if item.author and hasattr(item.author, 'profile'):
            item.author.profile.added_count += 1
            item.author.profile.save(update_fields=['added_count'])
        return item


class MapItemGeoSerializer(GeoFeatureModelSerializer):
    """GeoJSON FeatureCollection для карты."""
    class Meta:
        model = MapItem
        geo_field = 'location'
        fields = (
            'id', 'item_type', 'title', 'status', 'category',
            'privacy', 'activity_type', 'verifications', 'address',
        )
