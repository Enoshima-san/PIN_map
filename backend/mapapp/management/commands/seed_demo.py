from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point, LineString
from mapapp.models import MapItem, Comment, Profile


class Command(BaseCommand):
    help = 'Заполняет БД демо-данными Новокузнецка (как в оригинальном index.html)'

    def handle(self, *args, **options):
        admin_user, created = User.objects.get_or_create(
            username='admin@mail.ru',
            defaults={'email': 'admin@mail.ru', 'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        Profile.objects.get_or_create(user=admin_user, defaults={'is_moderator': True})

        demo = [
            {
                'item_type': 'object',
                'title': 'Кузнецкая крепость',
                'category': 'Культурное наследие',
                'privacy': 'тихий',
                'activity_type': 'Экскурсия',
                'status': 'approved',
                'verifications': 14,
                'address': 'крепость Кузнецкая, 1',
                'location': Point(87.1850, 53.7711, srid=4326),
                'description': 'Исторический архитектурный музей-заповедник на возвышенности в Кузнецком районе.',
                'image_url': 'https://commons.wikimedia.org/wiki/Special:FilePath/Kuznetsk_fortress_003.jpg',
            },
            {
                'item_type': 'object',
                'title': 'Новокузнецкий драматический театр',
                'category': 'Культурное наследие',
                'privacy': 'средний',
                'activity_type': 'Экскурсия',
                'status': 'approved',
                'verifications': 19,
                'address': 'пр. Металлургов, 28',
                'location': Point(87.1265, 53.7615, srid=4326),
                'description': 'Главный драматический театр города на проспекте Металлургов с богатой культурной историей.',
                'image_url': 'https://commons.wikimedia.org/wiki/Special:FilePath/File:Drama_Theatre_of_Novokuznetsk.jpg',
            },
            {
                'item_type': 'object',
                'title': 'Сквер им. Ермакова',
                'category': 'Парки и отдых',
                'privacy': 'средний',
                'activity_type': 'Прогулка',
                'status': 'approved',
                'verifications': 8,
                'address': 'пр. Ермакова, 11',
                'location': Point(87.1392, 53.7635, srid=4326),
                'description': 'Уютный прогулочный сквер с зелёными аллеями, скамейками и светомузыкальным фонтаном.',
                'image_url': 'https://commons.wikimedia.org/wiki/Special:FilePath/File:Views_of_Novokuznetsk_2015-06-22.JPG',
            },
            {
                'item_type': 'route',
                'title': 'Культурное наследие Центрального района',
                'category': 'Маршруты',
                'activity_type': 'Пеший маршрут',
                'duration_minutes': 45,
                'status': 'approved',
                'verifications': 31,
                'address': 'Драмтеатр — Проспект Металлургов — Сквер Ермакова',
                'location': Point(87.1265, 53.7615, srid=4326),
                'track': LineString(
                    (87.1265, 53.7615),
                    (87.1320, 53.7618),
                    (87.1392, 53.7635),
                    srid=4326
                ),
                'description': 'Прогулочный маршрут по главным культурным и историческим достопримечательностям.',
            },
        ]

        for data in demo:
            item, created = MapItem.objects.update_or_create(
                title=data['title'],
                defaults={**data, 'author': admin_user}
            )
            if created:
                self.stdout.write(f'  + {item.title}')

        # demo comments
        fortress = MapItem.objects.filter(title='Кузнецкая крепость').first()
        if fortress and not fortress.comments.exists():
            u1, _ = User.objects.get_or_create(username='user1@mail.ru', defaults={'email': 'user1@mail.ru'})
            if _:
                u1.set_password('pass123')
                u1.save()
                Profile.objects.get_or_create(user=u1)
            Comment.objects.create(map_item=fortress, author=u1, text='Замечательный исторический музей под открытым небом!')

        self.stdout.write(self.style.SUCCESS('Демо-данные загружены'))
