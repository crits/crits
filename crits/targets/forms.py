from django import forms

from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form

class TargetInfoForm(forms.Form):
    """
    Django form for adding/updating target information.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    firstname = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                                required=False)
    lastname = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                               required=False)
    division = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                               required=False)
    department = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                                 required=False)
    email_address = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                                    required=True)
    organization_id = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                                      required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                            required=False)
    note = forms.CharField(widget=forms.Textarea(attrs={'cols':'50', 'rows':'2'}),
                           required=False)

    def __init__(self, *args, **kwargs):
        super(TargetInfoForm, self).__init__(*args, **kwargs)
        add_bucketlist_to_form(self)
        add_ticket_to_form(self)
