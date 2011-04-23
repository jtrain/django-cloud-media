from django.contrib import admin
from cloud_test.zoo.models import Zookeeper
from cloud_media.admin import CloudMediaAdminInline

class ZookeeperAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_favourite_animal_display')
    inlines = (CloudMediaAdminInline,)

admin.site.register(Zookeeper, ZookeeperAdmin)
