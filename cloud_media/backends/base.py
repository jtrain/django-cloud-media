try:
    import json
    loads = json.loads
    dumps = json.dumps
except ImportError:
    from django.core import serializers
    from functools import partial
    loads = partial(serializers.deserialize, "json")
    dumps = serializers.serialize("json")()

from django.template.loader import render_to_string


class BaseStorage(object):
    """
    A base class for remote media backends to override functionality.

    """

    def get_template(self):
        raise NotImplementedError(
            "You must provide a template in your subclassed storage")

    def get_template_resource_name(self):
        return "resource"

    def get_form(self):
        raise NotImplementedError(
            "You must provide a form in your subclassed storage")

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

    def render_resource(self, resource):
        return render_to_string(self.get_template(),
            {self.get_template_resource_name(): resource})


