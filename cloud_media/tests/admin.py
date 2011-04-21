from django.contrib import admin

from cloud_media.admin import CloudMediaAdminInline
from cloud_media.tests.models import FamousPerson

class PersonAdmin(admin.ModelAdmin):

    inlines = (CloudMediaAdminInline,)

admin.site.register(FamousPerson, PersonAdmin)
