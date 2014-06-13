from django import forms
from django.forms.widgets import HiddenInput
from crits.core import form_consts
from crits.core.handlers import get_source_names
from crits.core.user_tools import get_user_organization

class AddScreenshotForm(forms.Form):
    """
    Django form for adding an Object.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    screenshot = forms.FileField(required=False)
    screenshot_ids = forms.CharField(required=False,
                                     widget=forms.Textarea(attrs={'cols':'80',
                                                               'rows':'2'}),
                                    help_text=('If it is an existing '
                                               'screenshot (or screenshots), '
                                               'enter the ID(s) instead. All '
                                               'other data <br>will be copied '
                                               'from the existing screenshot(s).'))
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'80',
                                                               'rows':'2'}),
                                                               required=False)
    tags = forms.CharField(widget=forms.TextInput(attrs={'size':'90'}),
                           required=False,
                           help_text='Comma-separated list of tags')
    source = forms.ChoiceField(required=True,
                               label=form_consts.Object.SOURCE,
                               widget=forms.Select(attrs={'class': 'no_clear bulknoinitial'}))
    method = forms.CharField(required=False, label=form_consts.Object.METHOD)
    reference = forms.CharField(widget=forms.TextInput(attrs={'size':'90'}),
                                required=False, label=form_consts.Object.REFERENCE)
    otype = forms.CharField(required=False,
                            widget=HiddenInput(attrs={'class':'bulkskip'}),
                            label=form_consts.Object.PARENT_OBJECT_TYPE)
    oid = forms.CharField(required=False,
                          widget=HiddenInput(attrs={'class':'bulkskip'}),
                          label=form_consts.Object.PARENT_OBJECT_ID)

    def __init__(self, username, *args, **kwargs):
        super(AddScreenshotForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name,
                                          c.name) for c in get_source_names(True,
                                                                            True,
                                                                            username)]
        self.fields['source'].initial = get_user_organization(username)
