from django import forms
from django.forms.widgets import HiddenInput
from crits.core import form_consts
from crits.core.handlers import get_source_names
from crits.core.user_tools import get_user_organization

from crits.vocabulary.objects import ObjectTypes

class AddObjectForm(forms.Form):
    """
    Django form for adding an Object.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    object_type = forms.ChoiceField(
        widget=forms.Select(),
        required=True,
        label=form_consts.Object.OBJECT_TYPE)
    value = forms.CharField(
        widget=forms.Textarea(attrs={'rows': '5', 'cols': '28'}),
        label=form_consts.Object.VALUE,
        required=True)
    source = forms.ChoiceField(
        required=True,
        label=form_consts.Object.SOURCE,
        widget=forms.Select(attrs={'class': 'no_clear bulknoinitial'}))
    method = forms.CharField(
        required=False,
        label=form_consts.Object.METHOD)
    reference = forms.CharField(
        widget=forms.TextInput(attrs={'size':'90'}),
        required=False,
        label=form_consts.Object.REFERENCE)
    otype = forms.CharField(
        required=False,
        widget=HiddenInput(attrs={'class':'bulkskip'}),
        label=form_consts.Object.PARENT_OBJECT_TYPE)
    oid = forms.CharField(
        required=False,
        widget=HiddenInput(attrs={'class':'bulkskip'}),
        label=form_consts.Object.PARENT_OBJECT_ID)
    add_indicator = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput,
        label=form_consts.Object.ADD_INDICATOR)

    def __init__(self, username, *args, **kwargs):
        super(AddObjectForm, self).__init__(*args, **kwargs)
        self.fields['object_type'].choices = [
            (c,c) for c in ObjectTypes.values(sort=True)
        ]
        self.fields['object_type'].widget.attrs = {'class':'object-types'}
        self.fields['source'].choices = [(c.name,
                                          c.name) for c in get_source_names(True,
                                                                            True,
                                                                            username)]
        self.fields['source'].initial = get_user_organization(username)
