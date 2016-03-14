from django import forms

from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.handlers import get_source_names, get_item_names
from crits.core.user_tools import get_user_organization
from crits.raw_data.raw_data import RawDataType
from crits.vocabulary.relationships import RelationshipTypes

relationship_choices = [(c, c) for c in RelationshipTypes.values(sort=True)]

class UploadRawDataFileForm(forms.Form):
    """
    Django form for uploading raw data as a file.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    filedata = forms.FileField()
    title = forms.CharField(required=True)
    tool_name = forms.CharField(required=True)
    tool_version = forms.CharField(required=False)
    tool_details = forms.CharField(required=False)
    data_type = forms.ChoiceField(required=True, widget=forms.Select(attrs={'class': 'no_clear'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'80',
                                                               'rows':'2'}),
                                                               required=False)
    source = forms.ChoiceField(required=True,
                               widget=forms.Select(attrs={'class': 'no_clear'}),
                               label=form_consts.RawData.SOURCE)
    method = forms.CharField(required=False, widget=forms.TextInput,
                             label=form_consts.RawData.SOURCE_METHOD)
    reference = forms.CharField(required=False,
                                widget=forms.TextInput(attrs={'size': '90'}),
                                label=form_consts.RawData.SOURCE_REFERENCE)
    related_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    related_type = forms.CharField(widget=forms.HiddenInput(), required=False)
    relationship_type = forms.ChoiceField(required=False,
                                          label='Relationship Type',
                                          widget=forms.Select(attrs={'id':'relationship_type'}))

    def __init__(self, username, *args, **kwargs):
        super(UploadRawDataFileForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name,
                                          c.name
                                          ) for c in get_source_names(True,
                                                                      True,
                                                                      username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['data_type'].choices = [(c.name,
                                             c.name
                                             ) for c in get_item_names(RawDataType,
                                                                       True)]
        self.fields['relationship_type'].choices = relationship_choices
        self.fields['relationship_type'].initial = RelationshipTypes.RELATED_TO

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)

class UploadRawDataForm(forms.Form):
    """
    Django form for uploading raw data as a field in the form.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    title = forms.CharField(required=True)
    tool_name = forms.CharField(required=True)
    tool_version = forms.CharField(required=False)
    tool_details = forms.CharField(required=False)
    data_type = forms.ChoiceField(required=True, widget=forms.Select(attrs={'class': 'no_clear'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'80',
                                                               'rows':'2'}),
                                                               required=False)
    source = forms.ChoiceField(required=True,
                               widget=forms.Select(attrs={'class': 'no_clear'}),
                               label=form_consts.RawData.SOURCE)
    method = forms.CharField(required=False, widget=forms.TextInput,
                             label=form_consts.RawData.SOURCE_METHOD)
    reference = forms.CharField(required=False,
                                widget=forms.TextInput(attrs={'size': '90'}),
                                label=form_consts.RawData.SOURCE_REFERENCE)
    data = forms.CharField(widget=forms.Textarea(attrs={'cols':'80',
                                                        'rows':'2'}),
                                                        required=True)

    related_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    related_type = forms.CharField(widget=forms.HiddenInput(), required=False)
    relationship_type = forms.ChoiceField(required=False,
                                          label='Relationship Type',
                                          widget=forms.Select(attrs={'id':'relationship_type'}))

    def __init__(self, username, *args, **kwargs):
        super(UploadRawDataForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name,
                                          c.name
                                          ) for c in get_source_names(True,
                                                                      True,
                                                                      username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['data_type'].choices = [(c.name,
                                             c.name
                                             ) for c in get_item_names(RawDataType,
                                                                       True)]
        self.fields['relationship_type'].choices = relationship_choices
        self.fields['relationship_type'].initial = RelationshipTypes.RELATED_TO
        
        add_bucketlist_to_form(self)
        add_ticket_to_form(self)

class NewRawDataTypeForm(forms.Form):
    """
    Django form for uploading a new raw data type.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    data_type = forms.CharField(widget=forms.TextInput, required=True)
