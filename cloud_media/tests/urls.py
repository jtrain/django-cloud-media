from django.conf.urls.defaults import patterns, url

from cloud_media.tests.models import FamousPerson

def make_test_url(number, template_name=None, extra_context=None):
    if not template_name:
        template_name = '%d.html' % number

    if extra_context is None:
        extra_context = {}
    extra_context.update({'people': FamousPerson.objects.all})

    return url(r'^%d$' % number,
                'django.views.generic.simple.direct_to_template',
                {'template': template_name,
                 'extra_context': extra_context})

urlpatterns = patterns('',
            make_test_url(1),
            make_test_url(2)

)
