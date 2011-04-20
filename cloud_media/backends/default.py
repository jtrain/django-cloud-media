"""
Backends that do not store their contents in the cloud, but rather 
store their content locally.

"""
try:
    import json
    loads = json.loads
except ImportError:
    from django.core import serializers
    from functools import partial
    loads = partial(serializers.deserialize, "json")

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import get_model

class LocalStorage(object):

    def serve(self, resource):
        """
        Retrieve the resource from the local storage provider and return 
        the local resource url. 

        Interpretation of resource_id
        -----------------------------

        This function interprets resource_id as a JSON field:
        {'model': 'appname.modelname',
         'pk'   : 'primarykey',
         'url'  : 'get_absolute_url'
        }

        ModelName: The appname.modelname to identify which model we should look
                   up.
        pk       : The primary key to identify which model instance to get.
        url      : an attribute or method on the model which will return the
                   model url.

        """
        resource_id = loads(resource.resource_id)

        # get the model.
        Model = get_model(*resource_id['model'].split('.'))
        obj = Model._default_manager.get(pk=resource_id['pk'])

        _url = getattr(obj, resource_id['url'])
        local_url = _url() if callable(_url) else _url

        return local_url

        
