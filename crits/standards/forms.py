from django import forms

from crits.core.handlers import get_source_names
from crits.core.user_tools import get_user_organization

class UploadStandardsForm(forms.Form):
    """
    Django form for uploading a standards document.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    filedata = forms.FileField()
    source = forms.ChoiceField(required=True)
    reference = forms.CharField(required=False)  # SAB Add new field
    make_event = forms.BooleanField(required=False, label="Create event", initial=True)

    def __init__(self, username, *args, **kwargs):
        super(UploadStandardsForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name,
                                          c.name) for c in get_source_names(True,
                                                                            True,
                                                                            username)]
        self.fields['source'].initial = get_user_organization(username)
