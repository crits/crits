from django import forms

from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.handlers import get_source_names
from crits.core.user_tools import get_user_organization
from crits.vocabulary.relationships import RelationshipTypes

relationship_choices = [(c, c) for c in RelationshipTypes.values(sort=True)]

class UploadPcapForm(forms.Form):
    """
    Django form for uploading new PCAPs.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    filedata = forms.FileField()
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'80', 'rows':'2'}), required=False)
    source = forms.ChoiceField(required=True,
                               widget=forms.Select(attrs={'class': 'no_clear'}),
                               label=form_consts.PCAP.SOURCE)
    method = forms.CharField(required=False, widget=forms.TextInput,
                             label=form_consts.PCAP.SOURCE_METHOD)
    reference = forms.CharField(required=False,
                                widget=forms.TextInput(attrs={'size': '90'}),
                                label=form_consts.PCAP.SOURCE_REFERENCE)
    related_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    related_type = forms.CharField(widget=forms.HiddenInput(), required=False)
    relationship_type = forms.ChoiceField(required=False,
                                          label='Relationship Type',
                                          widget=forms.Select(attrs={'id':'relationship_type'}))


    def __init__(self, username, *args, **kwargs):
        super(UploadPcapForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['relationship_type'].choices = relationship_choices
        self.fields['relationship_type'].initial = RelationshipTypes.RELATED_TO

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)
