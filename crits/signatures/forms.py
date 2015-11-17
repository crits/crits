from django import forms

from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.handlers import get_source_names, get_item_names
from crits.core.user_tools import get_user_organization
from crits.signatures.signature import SignatureType, SignatureDependency


class UploadSignatureForm(forms.Form):
    """
    Django form for uploading signatures as a field in the form.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    title = forms.CharField(required=True)
    data_type = forms.ChoiceField(required=True, widget=forms.Select(attrs={'class': 'no_clear'}))
    data_type_min_version = forms.CharField(required=False)
    data_type_max_version = forms.CharField(required=False)
    data_type_dependency = forms.CharField(required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'80',
                                                               'rows':'2'}),
                                                               required=False)
    source = forms.ChoiceField(required=True,
                               widget=forms.Select(attrs={'class': 'no_clear'}),
                               label=form_consts.Signature.SOURCE)
    method = forms.CharField(required=False, widget=forms.TextInput,
                             label=form_consts.Signature.SOURCE_METHOD)
    reference = forms.CharField(required=False,
                                widget=forms.TextInput(attrs={'size': '90'}),
                                label=form_consts.Signature.SOURCE_REFERENCE)
    data = forms.CharField(widget=forms.Textarea(attrs={'cols':'80',
                                                        'rows':'4'}),
                                                        required=True)

    def __init__(self, username, *args, **kwargs):
        super(UploadSignatureForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name,
                                          c.name
                                          ) for c in get_source_names(True,
                                                                      True,
                                                                      username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['data_type'].choices = [(c.name,
                                             c.name
                                             ) for c in get_item_names(SignatureType,
                                                                       True)]

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)


class NewSignatureTypeForm(forms.Form):
    """
    Django form for uploading a new signature type.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    data_type = forms.CharField(widget=forms.TextInput, required=True)


class NewSignatureDependencyForm(forms.Form):
    """
    Django form for uploading a new signature dependency. Might be done behind the scenes.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    data_type_dependency = forms.CharField(widget=forms.TextInput, required=True)