from django import forms
from django.forms.utils import ErrorList

from crits.campaigns.campaign import Campaign
from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.handlers import get_item_names

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
    campaign = forms.ChoiceField(widget=forms.Select, required=False,
                                 label=form_consts.Target.CAMPAIGN)
    camp_conf = forms.ChoiceField(required=False,
                                  label=form_consts.Target.CAMPAIGN_CONFIDENCE)

    def __init__(self, *args, **kwargs):
        super(TargetInfoForm, self).__init__(*args, **kwargs)
        campaigns = [('', '')] + [(c.name,
                                   c.name) for c in get_item_names(Campaign,
                                                                   True)]
        self.fields['campaign'].choices = campaigns
        self.fields['camp_conf'].choices = [('',''),
                                            ('low', 'low'),
                                            ('medium', 'medium'),
                                            ('high', 'high')]

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)

    def clean(self):
        cleaned_data = super(TargetInfoForm, self).clean()
        campaign = cleaned_data.get('campaign')

        if campaign:
            confidence = cleaned_data.get('camp_conf')

            if not confidence or confidence == '':
                self._errors.setdefault('camp_conf', ErrorList())
                self._errors['camp_conf'].append(u'This field is required if campaign is specified.')

        return cleaned_data
