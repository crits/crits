from django import forms

from crits.services.core import ServiceConfigOption, ServiceConfigError

import logging

logger = logging.getLogger(__name__)


class ImportServiceConfigForm(forms.Form):
    """
    Django form for importing service configuration files.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    file = forms.FileField()


def _get_config_fields(service_class, exclude_private):
    """
    Return a dict of Django Form fields for a given service class.

    Idea taken from http://www.b-list.org/weblog/2008/nov/09/dynamic-forms/ .
    """

    fields = {}

    for option in service_class.default_config:
        if option.private and exclude_private:
            continue
        name = option.name
        kwargs = {
            'required': option.required,
            'help_text': option.description
        }
        if option.type_ == ServiceConfigOption.STRING:
            fields[name] = forms.CharField(widget=forms.Textarea(
                attrs={'cols': '80', 'rows': '1'}), **kwargs)
        elif option.type_ == ServiceConfigOption.INT:
            fields[name] = forms.IntegerField(**kwargs)
        elif option.type_ == ServiceConfigOption.BOOL:
            fields[name] = forms.BooleanField(**kwargs)
        elif option.type_ == ServiceConfigOption.LIST:
            fields[name] = forms.CharField(widget=forms.Textarea(
                attrs={'cols': '80', 'rows': '5'}), **kwargs)
        elif option.type_ == ServiceConfigOption.SELECT:
            fields[name] = forms.ChoiceField(widget=forms.Select,
                    choices=option.enumerate_choices(),
                    **kwargs)
        elif option.type_ == ServiceConfigOption.MULTI_SELECT:
            fields[name] = forms.MultipleChoiceField(
                    widget=forms.CheckboxSelectMultiple,
                    choices=option.enumerate_choices(),
                    **kwargs)
        elif option.type_ == ServiceConfigOption.PASSWORD:
            fields[name] = forms.CharField(widget=forms.PasswordInput(),
                    **kwargs)
        else:
            # Should never get here, since the types should be checked in
            # the constructor of ServiceConfigOption.
            raise ServiceConfigError("Unknown Config Option Type: %s" %
                                            option.type_)

    return fields


def make_edit_config_form(service_class):
    """
    Return a Django Form for editing a service's config.

    This should be used when the administrator is editing a service
    configuration.
    """

    # Include private fields since this is for an administrator.
    fields = _get_config_fields(service_class, False)

    if not fields:
        return None

    return type("ServiceEditConfigForm",
                (forms.BaseForm,),
                {'base_fields': fields})


def make_run_config_form(service_class):
    """
    Return a Django form used when running a service.

    This is the same as make_edit_config_form, but adds a BooleanField
    (checkbox) for whether to "Force" the service to run.
    """

    # Hide private fields
    fields = _get_config_fields(service_class, True)

    if not service_class.rerunnable:
        fields['force'] = forms.BooleanField(required=False,
                                         help_text="Force the service to run.")

    if fields:
        return type("ServiceRunConfigForm",
                    (forms.BaseForm,),
                    {'base_fields': fields})
    else:
        return None
