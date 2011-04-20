import datetime
import os
import shutil

try:
    import json
    loads = json.loads
    dumps = json.dumps
except ImportError:
    from django.core import serializers
    from functools import partial
    loads = partial(serializers.deserialize, 'json')
    dumps = serializers.serialize('json')()

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.test import TestCase
from django.test.client import Client

from cloud_media.tests.models import FamousPerson, Storage
from cloud_media.models import Resource, RelatedMedia

class CloudMediaBaseCase(TestCase):

    def setUp(self):
        self.client = Client()

class LocalStorageBaseCase(CloudMediaBaseCase):

    def setUp(self):
        super(LocalStorageBaseCase, self).setUp()

        self.bio = 'he was a good engine.'
        cf = ContentFile(self.bio)
        cf.name = 'Thomas Bio'

        # stash the file somewhere.
        self.storedfile = Storage.objects.create(file=cf)

        self.person = FamousPerson.objects.create(
                                            name='Thomas Tank Engine',
        )

        # now create a resource object.
        resource_id = dumps(
                        dict(model='tests.storage',
                                pk=self.storedfile.pk,
                               url='get_file_url')
        )
                    
        self.resource = Resource.objects.create(
                                        title='Thomas Bio',
                                  description='a long and satisfying read.',
                                  resource_id=resource_id,
                                resource_type='default'
        )
        
        # relate the resource to the person.
        media = RelatedMedia.objects.create(
                            object_id=self.person.id,
                         content_type=ContentType.objects.get_for_model(
                                                                FamousPerson)
        )

        media.resources = [self.resource]
        media.save()

    def tearDown(self):
        super(LocalStorageBaseCase, self).tearDown()

        # remove that file.
        shutil.rmtree(settings.MEDIA_ROOT)

class LocalStorageRetrieval(LocalStorageBaseCase):
    '''
    Test that the backend can retrieve a local storage object.

    '''

    urls = 'cloud_media.tests.urls'

    def test_local_storage_backend_retreives_url(self):
        from cloud_media.backends.default import LocalStorage

        backend = LocalStorage()
        url = backend.serve(self.resource)

        self.assertEqual(
                url,
                self.storedfile.file.url)

    def test_retrieve_media_template_tag(self):
        response = self.client.get('/2')
        self.assertContains(response,
                            self.storedfile.file.url, count=2, status_code=200)
