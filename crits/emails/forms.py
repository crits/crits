from django.conf import settings
from django import forms
from django.forms.widgets import RadioSelect

from crits.campaigns.campaign import Campaign
from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.widgets import CalWidget
from crits.core.user_tools import get_user_organization
from crits.core.handlers import get_source_names, get_item_names

from datetime import datetime

class EmailOutlookForm(forms.Form):
    """
    Django form for uploading MSG files.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    msg_file = forms.FileField(label='MSG File', required=True)
    source = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'no_clear'}))
    source_reference = forms.CharField(widget=forms.TextInput(attrs={'size':'90'}), required=False)
    campaign = forms.ChoiceField(required=False, widget=forms.Select)
    campaign_confidence = forms.ChoiceField(required=False, widget=forms.Select)
    password = forms.CharField(widget=forms.TextInput, required=False, label='Attachment Password')
    def __init__(self, username, *args, **kwargs):
        super(EmailOutlookForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['campaign'].choices = [("","")]
        self.fields['campaign'].choices += [(c.name,
                                             c.name
                                             ) for c in get_item_names(Campaign,
                                                                       True)]
        self.fields['campaign_confidence'].choices = [("", ""),
                                             ("low", "low"),
                                             ("medium", "medium"),
                                             ("high", "high")]

class EmailAttachForm(forms.Form):
    """
    Django form for uploading attachments as Samples.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    upload_type = forms.ChoiceField(choices=[('File Upload', 'File Upload'), ('Metadata Upload', 'Metadata Upload')], widget=forms.RadioSelect(attrs={'class': 'toggle_upload_type'}))
    filedata = forms.FileField(required=False)
    filedata.widget.attrs=({'class': 'id_upload_type_0'})

    filename = forms.CharField(widget=forms.TextInput(attrs={'class': 'id_upload_type_1'}), required=False)
    md5 = forms.CharField(widget=forms.TextInput(attrs={'class': 'id_upload_type_1'}), required=False, label="MD5")
    file_format = forms.ChoiceField(widget=RadioSelect(attrs={'class': 'id_upload_type_0'}), choices=[("zip", "Zip"), ("rar", "RAR"), ("raw", "raw")], initial="zip", required=False)
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'id_upload_type_0'}), required=False)
    campaign = forms.ChoiceField(widget=forms.Select, required=False, label=form_consts.Sample.CAMPAIGN)
    confidence = forms.ChoiceField(widget=forms.Select, required=False, label=form_consts.Sample.CAMPAIGN_CONFIDENCE)
    source = forms.ChoiceField(widget=forms.Select(attrs={'class': 'no_clear'}))
    source_method = forms.CharField(widget=forms.TextInput(attrs={'size':'90'}), required=False)
    source_reference = forms.CharField(widget=forms.TextInput(attrs={'size':'90'}), required=False)
    source_date = forms.DateTimeField(required=False, widget=CalWidget(format=settings.PY_DATETIME_FORMAT, attrs={'class':'datetimeclass', 'size':'25', 'id':'email_attach_source_id'}), input_formats=settings.PY_FORM_DATETIME_FORMATS)

    def __init__(self, username, *args, **kwargs):
        super(EmailAttachForm, self).__init__(*args, **kwargs)
        self.fields['campaign'].choices = [('', '')] + [
                (c.name, c.name) for c in get_item_names(Campaign, True)]
        self.fields['confidence'].choices = [('', ''),
                                             ('low', 'low'),
                                             ('medium', 'medium'),
                                             ('high', 'high')]
        self.fields['source'].choices = [(c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['source_date'].value = datetime.now()

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)

    def clean(self):
        from django.forms.util import ErrorList
        cleaned_data = super(EmailAttachForm, self).clean()
        upload_type = cleaned_data.get('upload_type')
        if 'filedata' in self.files:
            filedata = True
        else:
            filedata = False

        campaign = cleaned_data.get('campaign')

        if campaign:
            confidence = cleaned_data.get('confidence')

            if not confidence or confidence == '':
                self._errors.setdefault('confidence', ErrorList())
                self._errors['confidence'].append(u'This field is required if campaign is specified.')

        # This duplicates a lot of sample's form, can these likely could be merged
        if upload_type == "Metadata Upload":
            md5 = cleaned_data.get('md5')
            filename = cleaned_data.get('filename')
            if not md5:
                self._errors.setdefault('md5', ErrorList())
                self._errors['md5'].append(u'This field is required.')
            if not filename:
                self._errors.setdefault('filename', ErrorList())
                self._errors['filename'].append(u'This field is required.')
        elif upload_type == "File Upload":
            upload_type = cleaned_data.get('upload_type')
            file_format = cleaned_data.get('file_format')
            if not upload_type:
                self._errors.setdefault('upload_type', ErrorList())
                self._errors['upload_type'].append(u'This field is required.')
            if not filedata:
                self._errors.setdefault('filedata', ErrorList())
                self._errors['filedata'].append(u'This field is required.')
            if not file_format:
                self._errors.setdefault('file_format', ErrorList())
                self._errors['file_format'].append(u'This field is required.')
        return cleaned_data

class EmailYAMLForm(forms.Form):
    """
    Django form for uploading an email in YAML format.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    source = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'no_clear'}))
    source_reference = forms.CharField(widget=forms.TextInput(attrs={'size':'90'}), required=False)
    campaign = forms.ChoiceField(required=False, widget=forms.Select)
    campaign_confidence = forms.ChoiceField(required=False, widget=forms.Select)
    yaml_data = forms.CharField(required=True, widget=forms.Textarea(attrs={'cols':'80', 'rows':'20'}))
    save_unsupported = forms.BooleanField(required=False, initial=True, label="Preserve unsupported attributes")
    def __init__(self, username, *args, **kwargs):
        super(EmailYAMLForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['campaign'].choices = [("","")]
        self.fields['campaign'].choices += [(c.name,
                                             c.name
                                             ) for c in get_item_names(Campaign,
                                                                       True)]
        self.fields['campaign_confidence'].choices = [("", ""),
                                             ("low", "low"),
                                             ("medium", "medium"),
                                             ("high", "high")]

class EmailEMLForm(forms.Form):
    """
    Django form for uploading an EML email.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    source = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'no_clear'}))
    source_reference = forms.CharField(widget=forms.TextInput(attrs={'size':'90'}), required=False)
    campaign = forms.ChoiceField(required=False, widget=forms.Select)
    campaign_confidence = forms.ChoiceField(required=False, widget=forms.Select)
    filedata = forms.FileField(required=True)
    def __init__(self, username, *args, **kwargs):
        super(EmailEMLForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['campaign'].choices = [("","")]
        self.fields['campaign'].choices += [(c.name,
                                             c.name
                                             ) for c in get_item_names(Campaign,
                                                                       True)]
        self.fields['campaign_confidence'].choices = [("", ""),
                                             ("low", "low"),
                                             ("medium", "medium"),
                                             ("high", "high")]

class EmailRawUploadForm(forms.Form):
    """
    Django form for uploading a raw email.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    raw_email = forms.CharField(required=True, widget=forms.Textarea(attrs={'cols':'80', 'rows':'12'}), label="Raw Email")
    source = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'no_clear'}))
    source_reference = forms.CharField(widget=forms.TextInput(attrs={'size':'120'}), required=False)
    campaign = forms.ChoiceField(required=False, widget=forms.Select)
    campaign_confidence = forms.ChoiceField(required=False, widget=forms.Select)
    def __init__(self, username, *args, **kwargs):
        super(EmailRawUploadForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['campaign'].choices = [("","")]
        self.fields['campaign'].choices += [(c.name,
                                             c.name
                                             ) for c in get_item_names(Campaign,
                                                                       True)]
        self.fields['campaign_confidence'].choices = [("", ""),
                                             ("low", "low"),
                                             ("medium", "medium"),
                                             ("high", "high")]

class EmailUploadForm(forms.Form):
    """
    Django form for uploading an email field-by-field.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    from_address = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="From")
    sender = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="Sender")
    to = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="To")
    cc = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="CC")
    subject = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="Subject")
    # this is intentionally an open string for people to populate
    date = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=True, label="Date")
    reply_to = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="Reply To")
    helo = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="HELO")
    boundary = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="Boundary")
    message_id = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="Message ID")
    originating_ip = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="Originating IP")
    x_originating_ip = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="X-Originating IP")
    x_mailer = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False, label="X-Mailer")
    raw_header = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols':'80', 'rows':'4'}), label="Raw Header")
    raw_body = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols':'80', 'rows':'4'}), label="Raw Body")
    campaign = forms.ChoiceField(required=False, widget=forms.Select)
    campaign_confidence = forms.ChoiceField(required=False, widget=forms.Select)
    source = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'no_clear'}))
    source_reference = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '1'}), required=False)

    def __init__(self, username, *args, **kwargs):
        super(EmailUploadForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)
        self.fields['campaign'].choices = [("","")]
        self.fields['campaign'].choices += [(c.name,
                                             c.name
                                             ) for c in get_item_names(Campaign,
                                                                       True)]
        self.fields['campaign_confidence'].choices = [("", ""),
                                             ("low", "low"),
                                             ("medium", "medium"),
                                             ("high", "high")]
