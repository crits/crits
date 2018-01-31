from django import forms

from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form, SourceInForm
from crits.core.handlers import get_source_names
from crits.core.user_tools import get_user_organization
from crits.vocabulary.relationships import RelationshipTypes

relationship_choices = [(c, c) for c in RelationshipTypes.values(sort=True)]

class UploadPcapForm(SourceInForm):
    """
    Django form for uploading new PCAPs.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    filedata = forms.FileField()
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'80', 'rows':'2'}), required=False)
    related_id = forms.CharField(widget=forms.HiddenInput(), required=False, label=form_consts.Common.RELATED_ID)
    related_type = forms.CharField(widget=forms.HiddenInput(), required=False, label=form_consts.Common.RELATED_TYPE)
    relationship_type = forms.ChoiceField(required=False,
                                          label=form_consts.Common.RELATIONSHIP_TYPE,
                                          widget=forms.Select(attrs={'id':'relationship_type'}))


    def __init__(self, username, *args, **kwargs):
        super(UploadPcapForm, self).__init__(username, *args, **kwargs)
        self.fields['relationship_type'].choices = relationship_choices
        self.fields['relationship_type'].initial = RelationshipTypes.RELATED_TO
        add_bucketlist_to_form(self)
        add_ticket_to_form(self)
