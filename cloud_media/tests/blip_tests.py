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
from django.core.cache import cache
from django.test import TestCase
from django.test.client import Client

from cloud_media.tests.models import FamousPerson
from cloud_media.models import Resource, RelatedMedia

class CloudMediaBaseCase(TestCase):

    def setUp(self):
        self.client = Client()

class BlipTVStorageBaseCase(CloudMediaBaseCase):

    def setUp(self):
        super(BlipTVStorageBaseCase, self).setUp()

        self.person = FamousPerson.objects.create(
                                            name='Stuart Holloway',
        )

        # now create a resource object.
        resource_id = dumps(dict(url='http://www.blip.tv/file/4824610/'))
                    
        self.resource = Resource.objects.create(
                title='Stuart Holloway: "Simplicity Ain\'t Easy"',
                description=(
                     'A quick review of what programmers have to say about '
                     'simplicity might lead you to the following (incorrect!) '
                     'conclusions: every language/design approach/tool under '
                     'the sun lays claim to simplicity, usually as a key '
                     'virtuesimplicity means many different things and is so '
                     'subjective as to be worthless In fact, simplicity is '
                     'objective. It has a definition, and an etymology, that '
                     'are very useful to software developers. In this talk, '
                     'we will: cut through the noise to the definition of '
                     'simplicitydemonstrate how simplicity informs the design '
                     'of Clojure, and Clojure programshelp you make your '
                     'programs simpler, and explain to others what this '
                     'means, and why.'),
                resource_id=resource_id,
                resource_type='blip.tv'
        )
        
        # relate the resource to the person.
        media = RelatedMedia.objects.create(
                            object_id=self.person.id,
                         content_type=ContentType.objects.get_for_model(
                                                                FamousPerson)
        )

        media.resources = [self.resource]
        media.save()


class BlipStorageRetrieval(BlipTVStorageBaseCase):
    '''
    Test that the backend can retrieve the media from the remote blip.tv host.

    '''

    urls = 'cloud_media.tests.urls'

    def test_blip_storage_backend_retreives_url(self):
        from cloud_media.backends.bliptv import BlipTVStorage

        backend = BlipTVStorage()
        embed = backend.serve(self.resource)

        self.assertEqual(
                embed,
                ('<embed src="http://blip.tv/play/AYKnyioC" '
                   'type="application/x-shockwave-flash" width="480" '
                   'height="300" allowscriptaccess="always" '
                   'allowfullscreen="true">'
                 '</embed>'))

    def test_retrieve_media_template_tag(self):
        response = self.client.get('/blip/2')
        self.assertContains(response,
                        ('<embed src="http://blip.tv/play/AYKnyioC" '
                   'type="application/x-shockwave-flash" width="480" '
                   'height="300" allowscriptaccess="always" '
                   'allowfullscreen="true">'
                 '</embed>'), count=1, status_code=200)

    def test_json_response_cached(self):
        """
        The json response for a given resource_id should be cached until
        invalidated.

        """
        from cloud_media.backends.bliptv import BlipTVStorage

        class CountURIAccess(BlipTVStorage):

            count = 0

            def _urlopen_read(self, uri):
                self.count += 1
                return super(CountURIAccess, self)._urlopen_read(uri)

        cache.clear()
        backend = CountURIAccess()
        embed = backend.serve(self.resource)
        embed = backend.serve(self.resource)

        self.assertEqual(backend.count, 1)

        self.assertEqual(
                embed,
                ('<embed src="http://blip.tv/play/AYKnyioC" '
                   'type="application/x-shockwave-flash" width="480" '
                   'height="300" allowscriptaccess="always" '
                   'allowfullscreen="true">'
                 '</embed>'))

    def test_cache_invalidates_on_object_save(self):
        """
        The json response for a given resource_id should be cached until
        invalidated.

        """
        from cloud_media.backends.bliptv import BlipTVStorage

        class CountURIAccess(BlipTVStorage):

            count = 0

            def _urlopen_read(self, uri):
                self.count += 1
                return super(CountURIAccess, self)._urlopen_read(uri)

        cache.clear()
        backend = CountURIAccess()
        embed = backend.serve(self.resource)
        embed = backend.serve(self.resource)
        self.resource.title = self.resource.title + 'postfix'
        self.resource.save()
        embed = backend.serve(self.resource)

        self.assertEqual(backend.count, 2)

        self.assertEqual(
                embed,
                ('<embed src="http://blip.tv/play/AYKnyioC" '
                   'type="application/x-shockwave-flash" width="480" '
                   'height="300" allowscriptaccess="always" '
                   'allowfullscreen="true">'
                 '</embed>'))
