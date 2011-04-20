"""
Backend for uploading and downloading from http://www.blip.tv.
"""

try:
    import json
    loads = json.loads
except ImportError:
    from django.core import serializers
    from functools import partial
    loads = partial(serializers.deserialize, "json")

try:
    from urllib2 import urlopen
except ImportError:
    from urllib import urlopen

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import get_model

import cloud_media.settings as backup_settings
from cloud_media.exceptions import StorageException

# time in seconds to cache the result of a remote resource.
CACHE_TIME = getattr(
                settings,
                "CLOUD_MEDIA_REMOTE_RESOURCE_CACHE_TIME",
                backup_settings.CLOUD_MEDIA_REMOTE_RESOURCE_CACHE_TIME)

class BlipTVStorage(object):

    def blip_file_uri(self):
        return u"http://www.blip.tv/file/%s/?skin=json"

    def _urlopen_read(self, uri):
        return urlopen(uri).read()

    def get_remote_resource(self, uri, resource):
        """
        Get the remote resource from the cache if it is available.
        Otherwise download it, then store it in the cache.
        """
        
        # resource_type and resource_id are unique together so use them as
        # cache keys.
        key = unicode((resource.resource_type, resource.resource_id)).replace(' ', '')
        remote_resource = cache.get(key)
        if not remote_resource:
            remote_resource = self._urlopen_read(uri)
            cache.set(key, remote_resource, CACHE_TIME)
        return remote_resource

    def serve(self, resource):
        """
        Retrieve the resource from the blip tv provider and
        return the oembed code.

        Interpretation of resource_id
        -----------------------------

        {'id': 'unique_blip_tv_id',
         'url':'url for the blip_tv_video'}

        id: the blip.tv unique file id number (assigned to all their videos.
       url: the blip.tv url that includes the unique file id number.

        either the id or url may be specifified.
        the url must be of the format:

            http://showname.blip.tv/file/(number)/
        or:
            http://www.blip.tv/file/(number)/

        (trailing slash is optional.)
        """

        resource_id = loads(resource.resource_id)

        if resource_id.get('id'):
            uri = self.blip_file_uri() % resource_id.get('id')
        elif resource_id.get('url'):
            uri = resource_id.get('url') + '?skin=json'
        else:
            raise StorageException(
                "resource with pk=%s did not contain an 'id' or 'url' field.")
        
        illformatted_json = self.get_remote_resource(uri, resource)

        # blip response with a json that begins with:
        #  blip_ws_results([...]);\n
        # which isn't valid json so I remove the surrounding function call.
        blip_json = illformatted_json.replace('blip_ws_results(', '')[:-3]

        embed_url = loads(blip_json)[0]['embedUrl']
        return ('<embed src="%s" '
                   'type="application/x-shockwave-flash" width="480" '
                   'height="300" allowscriptaccess="always" '
                   'allowfullscreen="true">'
                 '</embed>') % embed_url

