from django import forms
from django.forms.widgets import HiddenInput
from crits.core import form_consts
from crits.core.forms import SourceInForm
from crits.core.handlers import get_source_names
from crits.core.user_tools import get_user_organization

from crits.vocabulary.objects import ObjectTypes

class AddObjectForm(SourceInForm):
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
        super(AddObjectForm, self).__init__(username, *args, **kwargs)
        self.fields['object_type'].choices = [
            (c,c) for c in ObjectTypes.values(sort=True)
        ]
        self.fields['object_type'].widget.attrs = {'class':'object-types'}
