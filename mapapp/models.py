from django.conf import settings
from django.db import models


class Category(models.TextChoices):
    CULTURAL_HERITAGE = 'cultural_heritage', 'Культурное наследие'
    STREET_ART = 'street_art', 'Уличное искусство'
    ABANDONED = 'abandoned', 'Заброшенные пространства'
    NATURE = 'nature', 'Природные уголки'


class SolitudeLevel(models.TextChoices):
    HIGH = 'high', 'Высокий'
    MEDIUM = 'medium', 'Средний'
    LOW = 'low', 'Низкий'


class ActivityType(models.TextChoices):
    WALK = 'walk', 'Прогулка'
    PHOTO = 'photo', 'Фотосессия'
    BIKE = 'bike', 'Велосипед'
    RUN = 'run', 'Бег'


class ModerationStatus(models.TextChoices):
    PENDING = 'pending', 'На проверке'
    PUBLISHED = 'published', 'Опубликован'
    REJECTED = 'rejected', 'Отклонён'


class MediaType(models.TextChoices):
    PHOTO = 'photo', 'Фотография'
    VIDEO = 'video', 'Видео'


class Location(models.Model):
    """Объект (метка) на карте"""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Ссылаемся на пользователя
        on_delete=models.CASCADE,  # Удалить объекты вместе с пользователем
        related_name='locations',  # Обращение со стороны пользователя
        verbose_name='Автор'  # Подпись для админки
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Широта')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Долгота')
    category = models.CharField(
        max_length=32, choices=Category.choices, verbose_name='Категория'
    )
    solitude_level = models.CharField(
        max_length=16, choices=SolitudeLevel.choices, verbose_name='Уровень уединённости'
    )
    activity_type = models.CharField(
        max_length=16, choices=ActivityType.choices, verbose_name='Тип активности'
    )
    status = models.CharField(
        max_length=16,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
        verbose_name='Статус модерации'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'
        indexes = [
            models.Index(fields=['author'], name='idx_location_user')  # Индекс на FK author
        ]

    def __str__(self):
        return self.title  # Строковое представление: название объекта


class Route(models.Model):
    """Прогулочный маршрут"""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='routes',
        verbose_name='Автор'
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    activity_type = models.CharField(
        max_length=16, choices=ActivityType.choices, verbose_name='Тип активности'
    )
    duration_minutes = models.PositiveIntegerField(
        default=0, verbose_name='Длительность, минут'
    )
    status = models.CharField(
        max_length=16,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
        verbose_name='Статус модерации'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршруты'
        indexes = [
            models.Index(fields=['author'], name='idx_route_user')
        ]

    def __str__(self):
        return self.title


class RouteLocation(models.Model):
    """Связь маршрута и объекта с порядковым номером"""

    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='route_locations',
        verbose_name='Маршрут'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='route_locations',
        verbose_name='Объект'
    )
    order = models.PositiveIntegerField(verbose_name='Порядок в маршруте')

    class Meta:
        verbose_name = 'Точка маршрута'
        verbose_name_plural = 'Точки маршрута'
        unique_together = [('route', 'order')]  # Уникальность пары (маршрут, порядок)
        ordering = ['route', 'order']  # Сортировка по умолчанию
        indexes = [
            models.Index(fields=['route'], name='idx_route_location_route'),
            models.Index(fields=['location'], name='idx_route_location_location')
        ]

    def __str__(self):
        return f'{self.route} → {self.location} (#{self.order})'


class Media(models.Model):
    """Медиафайл, прикреплённый к объекту"""

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='media',
        verbose_name='Объект'
    )
    file_url = models.URLField(max_length=500, verbose_name='Ссылка на файл')
    media_type = models.CharField(max_length=8, choices=MediaType.choices, verbose_name='Тип медиа')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    class Meta:
        verbose_name = 'Медиафайл'
        verbose_name_plural = 'Медиафайлы'
        indexes = [
            models.Index(fields=['location'], name='idx_media_location')
        ]

    def __str__(self):
        return f'{self.media_type}: {self.file_url}'


class Comment(models.Model):
    """Комментарий к объекту или маршруту"""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='comments',
        null=True, blank=True,
        verbose_name='Объект'
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='comments',
        null=True, blank=True,
        verbose_name='Маршрут'
    )
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        indexes = [
            models.Index(fields=['author'], name='idx_comment_user'),
            models.Index(fields=['location'], name='idx_comment_location'),
            models.Index(fields=['route'], name='idx_comment_route')
        ]

    def __str__(self):
        target = self.location or self.route
        return f'{self.author} → {target}'


class Verification(models.Model):
    """Подтверждение достоверности объекта другим пользователем"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verifications',
        verbose_name='Пользователь'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='verifications',
        verbose_name='Объект'
    )
    verified_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подтверждения')

    class Meta:
        verbose_name = 'Подтверждение'
        verbose_name_plural = 'Подтверждения'
        unique_together = [('user', 'location')]
        indexes = [
            models.Index(fields=['user'], name='idx_verification_user'),
            models.Index(fields=['location'], name='idx_verification_location')
        ]

    def __str__(self):
        return f'{self.user} подтвердил {self.location}'
