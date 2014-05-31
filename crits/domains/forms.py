from datetime import datetime
from django.conf import settings
from django import forms
from django.forms.util import ErrorList

from crits.campaigns.campaign import Campaign
from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.widgets import CalWidget
from crits.core.handlers import get_source_names, get_item_names
from crits.core.user_tools import get_user_organization
from crits.domains.domain import Domain

class UpdateWhoisForm(forms.Form):
    """
    Django form for updating WhoIs information.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    date = forms.ChoiceField(widget=forms.Select, required=False)
    data = forms.CharField(required=True,
                           widget=forms.Textarea(attrs={'cols':'100',
                                                        'rows':'30'}))

    def __init__(self, *args, **kwargs):
        #populate date choices
        self.domain = ""
        allow_adding = True
        if 'domain' in kwargs:
            self.domain = kwargs['domain']
            del kwargs['domain'] #keep the default __init__ from erroring out
        if 'allow_adding' in kwargs:
            allow_adding = kwargs['allow_adding']
            del kwargs['allow_adding']
        super(UpdateWhoisForm, self).__init__(*args, **kwargs)
        if self.domain:
            if allow_adding:
                date_choices = [("","Add New")]
            else:
                date_choices = []
            dmain = Domain.objects(domain=self.domain).first()
            if dmain:
                whois = dmain.whois
                whois.sort(key=lambda w: w['date'], reverse=True)
                for w in dmain.whois:
                    date = datetime.strftime(w['date'],
                                             settings.PY_DATETIME_FORMAT)
                    date_choices.append((date,date))
            self.fields['date'].choices = date_choices

    def clean_date(self):
        date = self.cleaned_data['date']
        if date:
            date_obj = datetime.strptime(self.cleaned_data['date'],
                                         settings.PY_DATETIME_FORMAT)
            domain = Domain.objects(domain=self.domain,
                                    whois__date=date_obj).first()
            if not domain:
                raise forms.ValidationError(u'%s is not a valid date.' % date)

class DiffWhoisForm(forms.Form):
    """
    Django form for diffing WhoIs information.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    from_date = forms.ChoiceField(widget=forms.Select, required=True)
    to_date = forms.ChoiceField(widget=forms.Select, required=True)

    def __init__(self, *args, **kwargs):
        #populate date choices
        domain = ""
        if 'domain' in kwargs:
            domain = kwargs['domain']
            del kwargs['domain'] #keep the default __init__ from erroring out
        super(DiffWhoisForm, self).__init__(*args, **kwargs)
        if domain:
            date_choices = [("","Select Date To Compare")]
            dmain = Domain.objects(domain=domain).first()
            if dmain:
                whois = dmain.whois
                whois.sort(key=lambda w: w['date'], reverse=True)
                for w in dmain.whois:
                    date = datetime.strftime(w['date'],
                                             settings.PY_DATETIME_FORMAT)
                    date_choices.append((date,date))
            self.fields['from_date'].choices = self.fields['to_date'].choices = date_choices


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
    ip = forms.GenericIPAddressField(required=False,
                                     label=form_consts.Domain.IP_ADDRESS,
                                     widget=forms.TextInput(attrs={'class': 'togglewithip bulkrequired'}))
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
                                        label=form_consts.Domain.ADD_INDICATOR)

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

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)

    def clean(self):
        cleaned_data = super(AddDomainForm, self).clean()
        add_ip = cleaned_data.get('add_ip')
        ip = cleaned_data.get('ip')
        date = cleaned_data.get('created')
        same_source = cleaned_data.get('same_source')
        ip_source = cleaned_data.get('ip_source')

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
