"""
Backend for uploading and downloading from http://www.blip.tv.
"""

try:
    import json
    loads = json.loads
    dumps = json.dumps
except ImportError:
    from django.core import serializers
    from functools import partial
    loads = partial(serializers.deserialize, "json")
    dumps = serializers.serialize("json")()

try:
    from urllib2 import urlopen
except ImportError:
    from urllib import urlopen

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import get_model
from django.db.models.signals import pre_save
from django.dispatch import receiver

import cloud_media.settings as backup_settings
from cloud_media.exceptions import StorageException
from cloud_media.backends.base import BaseStorage
from cloud_media.models import Resource

# time in seconds to cache the result of a remote resource.
CACHE_TIME = getattr(
                settings,
                "CLOUD_MEDIA_REMOTE_RESOURCE_CACHE_TIME",
                backup_settings.CLOUD_MEDIA_REMOTE_RESOURCE_CACHE_TIME)

class BlipTVURLForm(forms.Form):
    """
    A custom form that allows a person to copy+paste the blip.tv video url (no
    direct upload I am afraid yet..)

    """
    video_url = forms.URLField()

    def get_resource_id(self, request, backend):
        """
        Returns a json string that looks like:

        {'url':'url for the blip_tv_video'}

        where the url value is the 'video_url' field on this form.

        """
        return dumps({'url': self.cleaned_data['video_url']})

class BlipTVStorage(BaseStorage):

    def get_template(self):
        return u'cloud_media/backends/blip_serve.html'

    def get_form(self):
        return BlipTVURLForm

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
        key = unicode(
                (resource.resource_type,
                 resource.resource_id)
              ).replace(' ', '')

        remote_resource = cache.get(key)
        if not remote_resource:
            remote_resource = self._urlopen_read(uri)
            cache.set(key, remote_resource, CACHE_TIME)
        return remote_resource

    def handle_url_resource_id(self, url):
        """
        Given a url, return an appropriate url to use to access the resource.

        >>> handle_url_resource_id('http://blip.tv/file/1234/')
        http://blip.tv/file/1234/?skin=json
        """
        return url + '?skin=json'

    def handle_id_resource_id(self, _id):
        """
        Given the resource_id specified id, return a url suitable for accessing
        the resource from blip.

        >>> handle_id_resource_id(56)
        http://blip.tv/file/56/
        """
        return self.blip_file_uri() % _id


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
        or:
            http://blip.tv/<username>/<videoname>-<posts_id>

        this last one is generally what the user will see when visiting the
        site.

        (trailing slash is optional.)
        """

        resource_id = loads(resource.resource_id)

        if resource_id.get('id'):
            uri = self.handle_id_resource_id(resource_id.get('id'))
        elif resource_id.get('url'):
            uri = self.handle_url_resource_id(resource_id.get('url'))
        else:
            raise StorageException(
                "resource with pk=%s did not contain an 'id' or 'url' field.")
        
        illformatted_json = self.get_remote_resource(uri, resource)
        blip_json = self._reformat_json(illformatted_json)

        resource.payload = self.get_payload(loads(blip_json))
        return self.render_resource(resource)

    def _reformat_json(self, raw_json):
        """
        blip response with a json that begins with:
            blip_ws_results([...]);\n
        which isn't valid json so I remove the surrounding function call.
        """
        return raw_json.replace('blip_ws_results(', '')[:-3]

    def get_payload(self, blip_retval):
        """
        Returns an object that will be set as the resource payload attribute.

        Args:
            blip_retval: The loaded json returned by bliptv api call.
        """
        return blip_retval[0]['embedUrl']

#--------------------------------------------------------------------------------
# Signals.

@receiver(pre_save, sender=Resource)
def save_file_id_if_given_posts_id(sender, instance, **kwargs):
    """
    For the blip tv json api, it is always best to use the:

        blip.tv/file/<file_id>

    url. However, I think this is very difficult for the average user to get.
    They may only be able to find the:

        blip.tv/<username>/<video_name>-<posts_id>

    url which gives the posts_id, and does not have a json skin (?skin=json
    doesn't work). So I find the file_id based on an api call and save the
    first url version if given the second.
    """
    resource_id = loads(instance.resource_id)

    url = resource_id.pop('url', None)
    _id = resource_id.pop('id', None)

    if not url:
        return

    if resource_id:
        # exit early if there are still keys in resource_id.
        # We are using local storage and not blip storage which has
        # only url and id keys.
        return

    if '/file/' in url:
        return

    # was given the public facing video url that contains post_id,
    # need to make 1 additional api call to get the file_id.
    reformat_json = BlipTVStorage._reformat_json.im_func

    # url of form http://blip.tv/username/videoname-123/ -> 123
    posts_id = url.split('-')[-1].replace('/', '')
    json_url = 'http://blip.tv/posts/%s/?skin=json&version=2' % posts_id

    # query the blip.tv api to find the file_id for this post_id.
    vid_info, = loads(reformat_json(None, urlopen(json_url).read()))

    new_resource_id = dumps({'url': vid_info[0]['url'] + '/'})

    instance.resource_id = new_resource_id
