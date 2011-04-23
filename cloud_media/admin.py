from django.conf import settings
from django.conf.urls.defaults import url, patterns
from django.contrib import admin
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import update_wrapper

from cloud_media.models import RelatedMedia, Resource
from cloud_media.forms import remote_media_wizard

class CloudMediaAdminInline(generic.GenericStackedInline):
    """
    Attach cloud media to any other model in the admin.

    """
    model = RelatedMedia
    extra = 0

class ResourceAdmin(admin.ModelAdmin):
    """
    The resource model has three main purposes:

    * title and description for the resource, and
    * a method to retrieve a unique resource from a remote location.

    This admin form is a wizard type form, it has a generic first page where
    the title and description are given, and the remote host is chosen. That
    remote host might be blip, youtube, vimeo, flickr or even local. 

    The second page of the form is dependant on the first remote host choice.
    If the user selects "blip" there is a text box to cut and paste the blip
    video url or video id into. If it was a local storage a file select field
    should appear so that user can normally upload the file.

    """

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwds):
                kwds['admin'] = self
                return self.admin_site.admin_view(view)(*args, **kwds)
            return update_wrapper(wrapper, view)
 
        urlpatterns = patterns('',
            url(r'^add/$',
                wrap(remote_media_wizard),
                name='cloud_media_resource_add')
        )

        urlpatterns += super(ResourceAdmin, self).get_urls()
        return urlpatterns

admin.site.register(Resource, ResourceAdmin)
