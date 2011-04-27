"""
Backends that do not store their contents in the cloud, but rather 
store their content locally.

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

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import get_model

from cloud_media.backends.base import BaseStorage

class DefaultStorageForm(forms.Form):
    """
    A simple form that provides an upload file field.

    """

    resource = forms.FileField(required=True, max_length=255)

    def create_resource(self, request, backend):
        resource = self.cleaned_data['resource']
        return backend.save_resource(resource)

    def get_resource_id(self, request, backend):
        """
        return a json string that looks like:

        {'model': 'appname.modelname',
         'pk'   : 'primarykey',
         'url'  : 'get_absolute_url'
        }

        the function creates and saves a new resource in the local storage by
        using the backend argument provided.

        """
        stored = self.create_resource(request, backend)
        
        model = "%s.%s" % (stored._meta.app_label,
                           stored._meta.object_name)
        pk = stored.pk
        filefield = getattr(stored,
                            backend.get_storage_filefield_name())
        url = filefield.url

        return dumps({'model': model, 'pk': pk, 'url': url})

class LocalStorage(BaseStorage):
    """
    A base class to provide storage locally on your server.

    Override this class and at least provide:

        get_storage - Returns the django Model to store resources
        get_storage_filefield_name - the name of the file field on that Model.

    e.g.

    class MyLocalStorage(models.Model):
        stored_file = model.FileField(upload_to='anywhere')

    class CustomLocalStorage(LocalStorage):

        def get_storage(self):
            return MyLocalStorage

        def get_storage_filefield_name(self):
            return 'stored_file'

    """

    def get_template(self):
        return "cloud_media/backends/default_serve.html"

    def get_template_resource_name(self):
        return "resource"

    def get_form(self):
        return DefaultStorageForm

    def get_storage(self):
        """
        Return a model with at least a FileField to store the resource on.
        """
        raise NotImplementedError(
            "You must override %s.%s and provide your own storage model"
            % (self.__class__.__name__, 'get_storage'))

    def get_storage_filefield_name(self):
        """
        Return the field name on the storage model. e.g.

            class MyLocalStorage(model.Model):
                title = model.CharField(max_length=255)
                desc = model.TextField()
                stored_file = model.FileField(upload_to='wherever')
            
            the field name here is 'stored_file', return this as a string.

        >>> mystorage.get_storage_filefield_name()
        'stored_file'

        """
        raise NotImplementedError(
            "You must override %s.%s and return your storage model's field name"
            % (self.__class__.__name__, 'get_storage_filefield_name'))

    def save_resource(self, file_resource, **kwargs):

        StorageModel = self.get_storage()
        file_field = self.get_storage_filefield_name()
        kwargs[file_field] = file_resource

        stored_resource = StorageModel(**kwargs)
        stored_resource.save()
        return stored_resource

    def serve(self, resource):
        """
        Retrieve the resource from the local storage provider and return 
        the local resource url.

        Interpretation of resource_id
        -----------------------------

        This function interprets resource_id as a JSON field:
        {'model': 'appname.modelname',
         'pk'   : 'primarykey',
         'url'  : 'file_url'
        }

        ModelName: The appname.modelname to identify which model we should look
                   up.
        pk       : The primary key to identify which model instance to get.
        url      : the url of the resource (optional).

        """
        resource_id = loads(resource.resource_id)

        # get the model.
        Model = get_model(*resource_id['model'].split('.'))
        obj = Model._default_manager.get(pk=resource_id['pk'])

        local_url = resource_id.get('url')
        if not local_url:
            local_url = getattr(obj, self.get_storage_filefield_name()).url

        resource.payload = local_url

        return self.render_resource(resource)

