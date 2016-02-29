from django import forms
from django.forms.utils import ErrorList

from crits.campaigns.campaign import Campaign
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.handlers import get_item_names, get_source_names
from crits.core.user_tools import get_user_organization
from crits.core import form_consts


class AddBackdoorForm(forms.Form):
    """
    Django form for adding a Backdoor to CRITs.
    """

    error_css_class = 'error'
    required_css_class = 'required'

    name = forms.CharField(label=form_consts.Backdoor.NAME, required=True)
    aliases = forms.CharField(label=form_consts.Backdoor.ALIASES,
                              required=False)
    version = forms.CharField(label=form_consts.Backdoor.VERSION,
                                  required=False)
    description = forms.CharField(label=form_consts.Backdoor.DESCRIPTION,
                                  required=False)
    campaign = forms.ChoiceField(widget=forms.Select,
                                 label=form_consts.Backdoor.CAMPAIGN,
                                 required=False)
    confidence = forms.ChoiceField(label=form_consts.Backdoor.CAMPAIGN_CONFIDENCE,
                                   required=False)
    source = forms.ChoiceField(widget=forms.Select(attrs={'class': 'bulknoinitial'}),
                               label=form_consts.Backdoor.SOURCE,
                               required=True)
    source_method = forms.CharField(label=form_consts.Backdoor.SOURCE_METHOD,
                                    required=False)
    source_reference = forms.CharField(widget=forms.TextInput(attrs={'size': '90'}),
                                       label=form_consts.Backdoor.SOURCE_REFERENCE,
                                       required=False)

    def __init__(self, username, *args, **kwargs):
        super(AddBackdoorForm, self).__init__(*args, **kwargs)

        self.fields['campaign'].choices = [('', '')] + [
            (c.name, c.name) for c in get_item_names(Campaign, True)]
        self.fields['confidence'].choices = [
            ('', ''),
            ('low', 'low'),
            ('medium', 'medium'),
            ('high', 'high')]
        self.fields['source'].choices = [
            (c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)

    def clean(self):
        cleaned_data = super(AddBackdoorForm, self).clean()
        campaign = cleaned_data.get('campaign')

        if campaign:
            confidence = cleaned_data.get('confidence')

            if not confidence or confidence == '':
                self._errors.setdefault('confidence', ErrorList())
                self._errors['confidence'].append(u'This field is required if campaign is specified.')

        return cleaned_data
