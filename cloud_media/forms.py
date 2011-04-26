"""
A collection of forms for adding a new resource in the admin.

"""
from django import forms
from django.conf import settings
from django.contrib.admin.helpers import AdminForm
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
from django.utils.importlib import import_module
from django.utils.encoding import force_unicode
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from cloud_media.models import Resource
from cloud_media.wizard import FormWizard
import cloud_media.settings as backup_settings


BACKENDS = getattr(
                settings,
                'CLOUD_MEDIA_HOSTING_BACKENDS',
                backup_settings.CLOUD_MEDIA_HOSTING_BACKENDS)
                
HOSTING_PROVIDERS = getattr(
                settings,
                'CLOUD_MEDIA_HOSTING_PROVIDERS',
                backup_settings.CLOUD_MEDIA_HOSTING_PROVIDERS)
                

class RemoteMediaWizard(FormWizard):
    """
    User fills in generic title + description on page 1.
    Page 2 is dynamic. The form shown depends on the remote host chosen
    for the file. It could be a BlipForm or a YoutubeForm etc..

    """

    @property
    def __name__(self):
        return self.__class__.__name__

    def get_template(self, step):
        return 'cloud_media/forms/wizard.html'

    def done(self, request, form_list):
        """

        The first form should specify the title, description and resource_type.
        The final form should provide the resource_id.

        """

        data = {}
        resource_id = None
        for form in form_list:
            try:
                resource_id = form.get_resource_id(self.backend)
            except AttributeError:
                pass
            data.update(form.cleaned_data)
        
        if not resource_id:
            raise forms.ValidationError("Backend failed to provide resource id")
        
        data['resource_id'] = resource_id

        # remove data that is extra to that required by Resource model.
        required_fields = set(f.name for f in Resource._meta.fields)
        provided_fields = set(data)

        data_to_remove = provided_fields - required_fields
        map(data.pop, data_to_remove)

        resource = Resource.objects.create(**data)

        # redirect or remove popup window.
        return self._model_admin.response_add(request, resource)

    def process_step(self, request, form, step):
        """
        Dynamically set the final form_list depending on the set request_type.

        """
        super(RemoteMediaWizard, self).process_step(request, form, step)

        resource_type = form.cleaned_data.get('resource_type')
        if not resource_type:
            return         

        # user can override default backend form in settings.
        try:
            NextForm = settings.CLOUD_MEDIA_HOSTING_UPLOAD_FORM[resource_type]
        except (AttributeError, KeyError):
            # not overridden select form based on backend. 
            backendname = BACKENDS.get(resource_type, BACKENDS.get('default'))
            self.backend = _load_backend(backendname)()
            NextForm = self.backend.get_form()

        self.form_list[1] = NextForm

    def render_template(self, request, form, previous_fields, step, context=None):
        """
        Renders the template for the given step, returning an HttpResponse object.

        Override this method if you want to add a custom context, return a
        different MIME type, etc. If you only need to override the template
        name, use get_template() instead.

        The template will be rendered with the following context:
            step_field -- The name of the hidden field containing the step.
            step0      -- The current step (zero-based).
            step       -- The current step (one-based).
            step_count -- The total number of steps.
            form       -- The Form instance for the current step (either empty
                          or with errors).
            previous_fields -- A string representing every previous data field,
                          plus hashes for completed forms, all in the form of
                          hidden fields. Note that you'll need to run this
                          through the "safe" template filter, to prevent
                          auto-escaping, because it's raw HTML.
        """
        context = context or {}
        context.update(self.extra_context)

        # add the adminform mixin to form's class.
        form.__class__.__bases__ = (AdminFormMixin,)

        return render_to_response(self.get_template(step), dict(context,
            step_field=self.step_field_name,
            step0=step,
            step=step + 1,
            step_count=self.num_steps(),
            form=form,
            is_popup='_popup' in request.REQUEST,
            previous_fields=previous_fields
        ), context_instance=RequestContext(request))
   
    def parse_params(self, request, admin=None, *args, **kwargs):
        self._model_admin = admin
        opts = admin.model._meta
        self.extra_context.update({
            'title': u'Add %s' % force_unicode(opts.verbose_name),
            'current_app': admin.admin_site.name,
            'has_change_permission': admin.has_change_permission(request),
            'add': True,
            'opts': opts,
            'root_path': admin.admin_site.root_path,
            'app_label': opts.app_label,
        })

_backends_cache = {}
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

class AdminFormMixin(forms.Form):
    """
    Provides some admin-form-like features to ease the pain of having non
    modeladmin forms in the admin. 

    Idea inspired by the formadmin project.
    """
    fieldsets = ()
    prepopulated_fields = {}
    readonly_fields = None
    model_admin = None

    def adminform(self):
        if not self.fieldsets:
            self.fieldsets = [
                        (None,
                            {'fields':
                                self.fields.keys()})
            ]
        adminform = AdminForm(self, self.fieldsets, self.prepopulated_fields,
                              self.readonly_fields, self.model_admin)
        return adminform

class RemoteMediaBasicForm(forms.Form):
    """
    A basic form to capture title, description and resource_type.

    """

    title         = forms.CharField(max_length=255)
    description   = forms.CharField(widget=forms.Textarea)

    resource_type = forms.ChoiceField(
                        choices=HOSTING_PROVIDERS,
                        help_text=_("Where would you like to upload to?")
                    )

remote_media_wizard = RemoteMediaWizard([RemoteMediaBasicForm, 0])
