from django import forms

from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.handlers import get_source_names, get_item_names
from crits.core.user_tools import get_user_organization
from crits.disassembly.disassembly import DisassemblyType

class UploadDisassemblyFileForm(forms.Form):
    """
    Django form for uploading disassembly as a file.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    filedata = forms.FileField(required=True)
    tool_name = forms.CharField(required=True)
    tool_version = forms.CharField(required=False)
    tool_details = forms.CharField(required=False)
    data_type = forms.ChoiceField(required=True, widget=forms.Select(attrs={'class': 'no_clear'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'40',
                                                               'rows':'2'}),
                                                               required=False)
    source = forms.ChoiceField(required=True, widget=forms.Select(attrs={'class': 'no_clear'}))

    def __init__(self, username, *args, **kwargs):
        super(UploadDisassemblyFileForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name,
                                          c.name
                                          ) for c in get_source_names(True,
                                                                      True,
                                                                      username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['data_type'].choices = [(c.name,
                                             c.name
                                             ) for c in get_item_names(DisassemblyType,
                                                                       True)]

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)

class NewDisassemblyTypeForm(forms.Form):
    """
    Django form for uploading a new disassembly type.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    data_type = forms.CharField(widget=forms.TextInput, required=True)
