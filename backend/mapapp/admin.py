from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.contrib.gis.forms.widgets import OSMWidget
from .models import MapItem, Comment, Profile, Verification, RoadEdge


class EsriWidget(OSMWidget):
    """Тайлы Esri Dark Gray вместо OSM"""
    default_lon = 87.13
    default_lat = 53.76
    default_zoom = 12
    template_name = 'gis/openlayers.html'

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/ol3/3.20.1/ol.css',)
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/ol3/3.20.1/ol.js',
            'gis/js/OLMapWidget.js',
        )


@admin.register(MapItem)
class MapItemAdmin(GISModelAdmin):
    list_display = ('title', 'item_type', 'status', 'author', 'verifications', 'created_at')
    list_filter = ('item_type', 'status', 'category', 'privacy')
    search_fields = ('title', 'address', 'description')
    default_lon = 87.13
    default_lat = 53.76
    default_zoom = 12
    gis_widget = EsriWidget

    class Media:
        js = (
            'https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.15.1/build/ol.js',
        )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('map_item', 'author', 'created_at')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_moderator', 'added_count', 'verified_count')


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ('map_item', 'user', 'created_at')


@admin.register(RoadEdge)
class RoadEdgeAdmin(GISModelAdmin):
    list_display = ('id', 'source', 'target', 'cost')
    default_lon = 87.13
    default_lat = 53.76
    default_zoom = 12