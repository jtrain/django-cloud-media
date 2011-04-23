from django.db import models
from django.utils.translation import ugettext_lazy as _

from cloud_media.backends.default import LocalStorage

FAV_ANIMAL = (
        ('gorilla', "Gorilla"),
        ('eagle'  , "Eagle"  ),
        ('walrus', "Walrus"),
        ('hippo' , "Hippo" )
)

class Zookeeper(models.Model):

    name             = models.CharField(
                            _("name"),
                            help_text=_("This zookeeper's name"),
                            max_length=12)

    favourite_animal = models.CharField(
                            _("favourite animal"),
                            choices=FAV_ANIMAL,
                            max_length=12,
                            help_text=_("Which animal outshines them all?")
                     )

    def __unicode__(self):
        return self.name


class ZookeeperLicenceStorage(models.Model):
    """
    Local storage for zookeeper licenses (*.txt files probably).

    """

    licence_file = models.FileField(upload_to="licences")


class CustomLicenceStorage(LocalStorage):
    """
    Custom licence storage.

    """

    def get_storage(self):
        return ZookeeperLicenceStorage

    def get_storage_filefield_name(self):
        return u'licence_file'
