from django.conf import settings
from django import forms
from django.forms.utils import ErrorList

from crits.campaigns.campaign import Campaign
from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.widgets import CalWidget
from crits.core.handlers import get_source_names, get_item_names
from crits.core.user_tools import get_user_organization

from crits.vocabulary.ips import IPTypes

ip_choices = [(c,c) for c in IPTypes.values(sort=True)]

class TLDUpdateForm(forms.Form):
    """
    Django form for updating TLD entries.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    filedata = forms.FileField()

class AddDomainForm(forms.Form):
    """
    Django form for adding a domain.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    domain = forms.CharField(label=form_consts.Domain.DOMAIN_NAME)
    campaign = forms.ChoiceField(widget=forms.Select, required=False,
                                 label=form_consts.Domain.CAMPAIGN)
    confidence = forms.ChoiceField(required=False, label=form_consts.Domain.CAMPAIGN_CONFIDENCE)
    domain_source = forms.ChoiceField(required=True,
                                      widget=forms.Select(attrs={'class': 'bulknoinitial'}),
                                      label=form_consts.Domain.DOMAIN_SOURCE)
    domain_method = forms.CharField(required=False,
                                    widget=forms.TextInput,
                                    label=form_consts.Domain.DOMAIN_METHOD)
    domain_reference = forms.CharField(widget=forms.TextInput(attrs={'size':'90'}),
                                       required=False,
                                       label=form_consts.Domain.DOMAIN_REFERENCE)
    add_ip = forms.BooleanField(required=False,
                                widget=forms.CheckboxInput(attrs={'class':'bulkskip'}),
                                label=form_consts.Domain.ADD_IP_ADDRESS)
    ip = forms.CharField(required=False,
                         label=form_consts.Domain.IP_ADDRESS,
                         widget=forms.TextInput(attrs={'class': 'togglewithip bulkrequired'}))
    ip_type = forms.ChoiceField(required=False,
                                label=form_consts.Domain.IP_TYPE,
                                widget=forms.Select(attrs={'class':'togglewithip bulkrequired bulknoinitial'}),)
    created = forms.DateTimeField(widget=CalWidget(format=settings.PY_DATETIME_FORMAT,
                                                   attrs={'class':'datetimeclass togglewithip bulkrequired',
                                                          'size':'25',
                                                          'id':'id_domain_ip_date'}),
                                  input_formats=settings.PY_FORM_DATETIME_FORMATS,
                                  required=False,
                                  label=form_consts.Domain.IP_DATE)
    same_source = forms.BooleanField(required=False,
                                     widget=forms.CheckboxInput(attrs={'class':'togglewithip bulkskip'}),
                                     label=form_consts.Domain.SAME_SOURCE)
    ip_source = forms.ChoiceField(required=False,
                                  widget=forms.Select(attrs={'class':'togglewithipsource togglewithip bulkrequired bulknoinitial'}),
                                  label=form_consts.Domain.IP_SOURCE)
    ip_method = forms.CharField(required=False,
                                widget=forms.TextInput(attrs={'class':'togglewithipsource togglewithip'}),
                                label=form_consts.Domain.IP_METHOD)
    ip_reference = forms.CharField(widget=forms.TextInput(attrs={'size':'90',
                                                                 'class':'togglewithipsource togglewithip'}),
                                   required=False,
                                   label=form_consts.Domain.IP_REFERENCE)
    add_indicators = forms.BooleanField(required=False,
                                        widget=forms.CheckboxInput(attrs={'class':'bulkskip'}),
                                        label=form_consts.Domain.ADD_INDICATORS)

    def __init__(self, username, *args, **kwargs):
        super(AddDomainForm, self).__init__(*args, **kwargs)
        self.fields['domain_source'].choices = self.fields['ip_source'].choices = [(c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['domain_source'].initial = get_user_organization(username)
        self.fields['ip_source'].initial = get_user_organization(username)
        self.fields['campaign'].choices = [('', '')] + [(c.name, c.name) for c in get_item_names(Campaign, True)]
        self.fields['confidence'].choices = [('',''),
                                             ('low', 'low'),
                                             ('medium', 'medium'),
                                             ('high', 'high')]

        self.fields['ip_type'].choices = ip_choices
        self.fields['ip_type'].initial = "Address - ipv4-addr"

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)

    def clean(self):
        cleaned_data = super(AddDomainForm, self).clean()
        add_ip = cleaned_data.get('add_ip')
        ip = cleaned_data.get('ip')
        date = cleaned_data.get('created')
        same_source = cleaned_data.get('same_source')
        ip_source = cleaned_data.get('ip_source')
        ip_type = cleaned_data.get('ip_type')

        campaign = cleaned_data.get('campaign')

        if campaign:
            confidence = cleaned_data.get('confidence')

            if not confidence or confidence == '':
                self._errors.setdefault('confidence', ErrorList())
                self._errors['confidence'].append(u'This field is required if campaign is specified.')

        if add_ip:
            if not ip:
                self._errors.setdefault('ip', ErrorList())
                self._errors['ip'].append(u'This field is required.')
            if not ip_type:
                self._errors.setdefault('ip_type', ErrorList())
                self._errors['ip_type'].append(u'This field is required.')
            if not date:
                self._errors.setdefault('created', ErrorList())
                self._errors['created'].append(u"This field is required.") #add error to created field
            if not (same_source or ip_source):
                self._errors.setdefault('same_source', ErrorList())
                self._errors['same_source'].append(u"This field is required.") #add error to IP source field
            if not same_source and not ip_source:
                self._errors.setdefault('ip_source', ErrorList())
                self._errors['ip_source'].append(u"This field is required.") #add error to IP source field
        return cleaned_data
