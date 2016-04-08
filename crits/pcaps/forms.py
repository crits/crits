from django import forms

from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form, SourceInForm
from crits.core.handlers import get_source_names
from crits.core.user_tools import get_user_organization

class UploadPcapForm(SourceInForm):
    """
    Django form for uploading new PCAPs.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    filedata = forms.FileField()
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'80', 'rows':'2'}), required=False)
    related_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    related_type = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, username, *args, **kwargs):
        super(UploadPcapForm, self).__init__(username, *args, **kwargs)

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)
