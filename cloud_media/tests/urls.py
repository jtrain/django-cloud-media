from django.conf.urls.defaults import patterns, url, include

from cloud_media.tests.models import FamousPerson

from django.contrib import admin
admin.autodiscover()

def make_test_url(number, prefix='', template_name=None, extra_context=None):
    if not template_name:
        template_name = '%d.html' % number

    if extra_context is None:
        extra_context = {}
    extra_context.update({'people': FamousPerson.objects.all})

    return url(r'^%s%d$' % (prefix, number),
                'django.views.generic.simple.direct_to_template',
                {'template': template_name,
                 'extra_context': extra_context})

urlpatterns = patterns('',
            make_test_url(2),
            make_test_url(2, prefix='blip/', template_name='blip2.html'),
            (r'^admin/', include(admin.site.urls)),

)
