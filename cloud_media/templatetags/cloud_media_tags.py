"""
a collection of tags for rendering and getting cloud media.

"""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.contenttypes.models import ContentType
from django import template
from django.utils.importlib import import_module

from cloud_media.models import RelatedMedia
import cloud_media.settings as backup_settings

register = template.Library()

BACKEND_LOOKUP = getattr(
                        settings,
                        'CLOUD_MEDIA_HOSTING_BACKENDS',
                        backup_settings.CLOUD_MEDIA_HOSTING_BACKENDS)


_backends_cache = {}

class RelatedMediaForObjectNode(template.Node):
    def __init__(self, obj, var_name):
        self.obj = obj
        self.var_name = var_name

    def resolve(self, var, context):
        """Resolves a variable out of context if it is not in quotes."""
        if var[0] in ('"', "'") and var[-1] == var[0]:
            return var[1:-1]
        else:
            return template.Variable(var).resolve(context)

    def render(self, context):
        obj = self.resolve(self.obj, context)
        var_name = self.resolve(self.var_name, context)
        context[var_name] = _get_media_for(obj)
        return ''

@register.tag
def retrieve_media_for(parser, token):

    bits = token.contents.split()
    kwargs = {
            'obj': _next_bit_for(bits, bits[0]),
            'var_name': _next_bit_for(bits, 'as', '"related_media"'),
    }

    return RelatedMediaForObjectNode(**kwargs)

@register.inclusion_tag('cloud_media/includes/default.html')
def render_media_for(obj, template_name='cloud_media/includes/default.html'):
    """
    Finds media attached to obj and renders with the template provided.

    """
    media_content = _get_media_for(obj)

    return {'template_name': template_name,
            'media_content': media_content}
                
#-------------------------------------------------------------------------
# Utility functions.

def _load_backend(backend):
    if not backend:
            raise ImproperlyConfigured(
                "%s isn't in your CLOUD_MEDIA_HOSTING_BACKENDS"
                "and neither is 'default'" % resource_type)
            
    if backend not in _backends_cache:
        module_name, func_name = backend.rsplit('.', 1)
        _backends_cache[backend] = getattr(import_module(module_name),
                                           func_name)

    return  _backends_cache[backend]

def _get_media_for(obj):
    # find all related media for obj.
    media_objects = RelatedMedia.objects.filter(
            object_id=obj.id,
         content_type=ContentType.objects.get_for_model(obj))

    # find the backend for this media.
    media_content = []
    for m in media_objects:
        for resource in m.resources.all():
            resource_type = resource.resource_type

            backend = BACKEND_LOOKUP.get(
                            resource_type,
                            BACKEND_LOOKUP.get('default')
            )

            Backend = _load_backend(backend)
            backend = Backend()
            media_content.append(backend.serve(resource))

    return media_content

def _next_bit_for(bits, key, default=None):
    try:
        return bits[bits.index(key) + 1]
    except ValueError:
        return default

