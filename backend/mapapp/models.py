from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point, LineString


class Profile(models.Model):
    """Расширение пользователя: статистика."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_moderator = models.BooleanField(default=False)
    added_count = models.PositiveIntegerField(default=0)
    verified_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'Profile of {self.user.email or self.user.username}'


class MapItem(models.Model):
    """Базовая модель для объектов и маршрутов (социальная карта прогулок)."""

    ITEM_TYPES = (
        ('object', 'Объект'),
        ('route', 'Маршрут'),
    )
    STATUS_CHOICES = (
        ('pending', 'На модерации'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    )
    PRIVACY_LEVELS = (
        ('тихий', 'Тихий'),
        ('средний', 'Средний'),
        ('высокий', 'Высокий'),
    )
    CATEGORIES = (
        ('Культурное наследие', 'Культурное наследие'),
        ('Уличное искусство', 'Уличное искусство'),
        ('Природный объект', 'Природный объект'),
        ('Парки и отдых', 'Парки и отдых'),
        ('Маршруты', 'Маршруты'),
    )
    ACTIVITY_TYPES = (
        ('Прогулка', 'Прогулка'),
        ('Фотосессия', 'Фотосессия'),
        ('Велосипед', 'Велосипед'),
        ('Экскурсия', 'Экскурсия'),
        ('Пеший маршрут', 'Пеший маршрут'),
        ('Веломаршрут', 'Веломаршрут'),
        ('Бег', 'Бег'),
    )

    item_type = models.CharField(max_length=10, choices=ITEM_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='map_items')
    verifications = models.PositiveIntegerField(default=0)
    address = models.CharField(max_length=500, blank=True)

    # Геометрия: Point для объекта, LineString для маршрута
    location = models.PointField(srid=4326, null=True, blank=True)  # для объектов и старта маршрута
    track = models.LineStringField(srid=4326, null=True, blank=True)  # для маршрутов

    category = models.CharField(max_length=50, choices=CATEGORIES, blank=True)
    privacy = models.CharField(max_length=20, choices=PRIVACY_LEVELS, blank=True)
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    image = models.ImageField(upload_to='map_items/', null=True, blank=True)
    image_url = models.URLField(blank=True)  # fallback для демо-данных

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Объект / Маршрут'
        verbose_name_plural = 'Объекты и маршруты'

    def __str__(self):
        return f'[{self.get_item_type_display()}] {self.title}'

    @property
    def lat(self):
        if self.location:
            return self.location.y
        return None

    @property
    def lng(self):
        if self.location:
            return self.location.x
        return None


class Comment(models.Model):
    map_item = models.ForeignKey(MapItem, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author} on {self.map_item}'


class Verification(models.Model):
    """Кто подтвердил существование объекта (чтобы не считать повторно)."""
    map_item = models.ForeignKey(MapItem, on_delete=models.CASCADE, related_name='verification_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('map_item', 'user')


# --- pgRouting support ---
# Для полноценного pgRouting нужна таблица рёбер дорожной сети (edge table).
# Ниже — минимальная модель-заглушка + raw SQL helper.
# Улучшения модели с помощью OSM / дорожной сети через osm2pgrouting.

class RoadEdge(models.Model):
    """
    Упрощённая таблица рёбер для pgRouting.
    После миграции выполнить:
    SELECT pgr_createTopology('mapapp_roadedge', 0.0001, 'geom', 'id');
    """
    source = models.IntegerField(null=True, blank=True)
    target = models.IntegerField(null=True, blank=True)
    cost = models.FloatField(default=1.0)
    reverse_cost = models.FloatField(default=1.0)
    geom = models.LineStringField(srid=4326)

    class Meta:
        db_table = 'mapapp_roadedge'
