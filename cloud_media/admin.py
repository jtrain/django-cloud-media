from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _

from cloud_media.models import RelatedMedia

class CloudMediaAdminInline(generic.GenericStackedInline):
    """
    Attach cloud media to any other model in the admin.

    """
    model = RelatedMedia

