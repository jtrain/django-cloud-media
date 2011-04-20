from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

import cloud_media.settings as backup_settings

HOSTING_PROVIDERS = getattr(settings,
                            'CLOUD_MEDIA_HOSTING_PROVIDERS',
                            backup_settings.CLOUD_MEDIA_HOSTING_PROVIDERS)


#-------------------------------------------------------------------
# managers.

class ResourceManager(models.Manager):
    def get_by_natural_key(self, resource_id, resource_type):
        return self.get(
                resource_id=resource_id,
              resource_type=resource_type
        )

#-------------------------------------------------------------------
# models.

class Resource(models.Model):
    """
    The resource model contains the base information about a media file which is
    hosted elsewhere.

    The resource_id is a free-form field that contains sufficient information
    for this app to uniquely identify the resource somewhere on the web. An
    example might be the video id provided by blip.tv

    The resource_type is a field which indicates who is hosting the resource.
    This value will dictate which backend to use to retrieve the resource.

    eg. there might be a 'Blip.TV' resource_type, which would be connected to a
    BlipTvBackend. That backend is used for uploading and downloading files.

    The connection between 'Blip.TV' resource_type (defined as a choice in
    settings.py under 'CLOUD_MEDIA_HOSTING_PROVIDERS') and the BlipTvBackend
    occurs in the settings.py file. There is a variable called
    CLOUD_MEDIA_HOSTING_BACKENDS, which should be set to a dictionary mapping
    the resource_type (Id field not the display_name field) and the backend
    class name e.g.

    CLOUD_MEDIA_HOSTING_PROVIDERS = (
                    (0,         'Blip.TV'      ),
                    (1,         'Youtube'      ),
                    ('default', 'Local Storage'),
    )
    CLOUD_MEDIA_HOSTING_BACKENDS = {
                                0: 'cloud_media.backends.BlipTvBackend',
                                1: 'cloud_media.backends.YoutubeBackend',
                        'default': 'cloud_media.backends.LocalStorageBackend'
    }

    """

    title         = models.CharField(
                            _('title'),
                            max_length=255
                    )

    description   = models.TextField(
                            _('description'),
                            blank=True,
                            null=True
                    )

    resource_id   = models.TextField(
                            _('resource ID'),
                            blank=True,
                            null=True,
                            help_text=
                    _('Unique id provided by the hosting service provider')
                    )

    resource_type = models.CharField(
                            _('hosting provider'),
                            blank=True,
                            null=True,
                            max_length=255,
                            choices=HOSTING_PROVIDERS,
                            help_text=
                    _('hosting service provider')
                    )

    objects = ResourceManager()

    class Meta:
        verbose_name        = _('resource')
        verbose_name_plural = _('resources')
        unique_together     = (('resource_id', 'resource_type'),)
        ordering            = ('resource_type', 'title')

    def __unicode__(self):
        return u'%s %s %s' % (
                unicode(self.title),
                _('on'),
                unicode(self.get_resource_type_display))

    def natural_key(self):
        return (self.resource_id, self.resource_type)

class RelatedMedia(models.Model):
    """
    Acts as the middle man between a resource holder (e.g. a blog entry)
    and the resources attached to it.

    A resource holder may have many resources attached, and so too may a
    resource be attached to many resource holders.
    
    """

    object_id     = models.CharField(
                            _("object id"),
                            max_length=255,
                            blank=True,
                            null=True
                  )

    content_type  = models.ForeignKey(
                            ContentType,
                            blank=True,
                            null=True,
                            verbose_name=_("content type")
                  )

    content_object= generic.GenericForeignKey(
                            ct_field="content_type",
                            fk_field="object_id"
                  )

    resources     = models.ManyToManyField(
                            Resource,
                            blank=True,
                            null=True,
                            verbose_name=_("resources"),
                  )


    def __unicode__(self):
        return u'related media for %s' % (self.content_type)

    class Meta:
        verbose_name        = _("related media")
        verbose_name_plural = _("related media")
        ordering            = ('content_type', 'object_id')


#-------------------------------------------------------------------
# signals.

@receiver(post_save, sender=Resource)
def invalidate_resource_cache(sender, instance, **kwargs):
    """
    Invalidate the cache for key(resource_id, resource_type).replace(' ', '')
    when a save is made, just in case an update is required.

    """
    obj = instance

    key = unicode((obj.resource_type, obj.resource_id)).replace(' ', '')
    if cache.get(key):
        cache.delete(key)

