from django import forms
from django.forms.widgets import RadioSelect

from crits.campaigns.campaign import Campaign
from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.handlers import get_source_names, get_item_names
from crits.core.user_tools import get_user_organization
from crits.samples.backdoor import Backdoor
from crits.samples.exploit import Exploit

class UnrarSampleForm(forms.Form):
    """
    Django form to handle unraring a sample.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    password = forms.CharField(widget=forms.TextInput, required=False)

class XORSearchForm(forms.Form):
    """
    Django form to handle performing an XOR search.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    string = forms.CharField(widget=forms.TextInput, required=False)
    skip_nulls = forms.BooleanField(required=False)
    is_key = forms.BooleanField(required=False)

class UploadFileForm(forms.Form):
    """
    Django form to handle uploading a sample.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    upload_type = forms.ChoiceField(choices=[(form_consts.Sample.UploadType.FILE_UPLOAD, form_consts.Sample.UploadType.FILE_UPLOAD),
                                             (form_consts.Sample.UploadType.METADATA_UPLOAD, form_consts.Sample.UploadType.METADATA_UPLOAD)],
                                    widget=forms.RadioSelect(attrs={form_consts.Common.CLASS_ATTRIBUTE: form_consts.Common.BULK_SKIP + ' toggle_upload_type'}),
                                    required=True,
                                    label=form_consts.Sample.UPLOAD_TYPE)
    filedata = forms.FileField(required=False,
                               label=form_consts.Sample.FILE_DATA)
    filedata.widget.attrs=({form_consts.Common.CLASS_ATTRIBUTE: form_consts.Common.BULK_SKIP + ' id_upload_type_0 required'})
    filename = forms.CharField(widget=forms.TextInput(attrs={form_consts.Common.CLASS_ATTRIBUTE: form_consts.Common.BULK_REQUIRED + ' id_upload_type_1 required'}),
                               required=False,
                               label=form_consts.Sample.FILE_NAME)
    md5 = forms.CharField(widget=forms.TextInput(attrs={form_consts.Common.CLASS_ATTRIBUTE: form_consts.Common.BULK_REQUIRED + ' id_upload_type_1 required'}),
                          required=False,
                          label=form_consts.Sample.MD5)
    file_format = forms.ChoiceField(widget=RadioSelect(attrs={form_consts.Common.CLASS_ATTRIBUTE: form_consts.Common.BULK_SKIP + ' id_upload_type_0 required'}),
                                    choices=[("zip", "Zip"),
                                             ("rar", "RAR"),
                                             ("raw", "raw")],
                                    initial="zip",
                                    required=False,
                                    label=form_consts.Sample.FILE_FORMAT)
    password = forms.CharField(widget=forms.TextInput(attrs={form_consts.Common.CLASS_ATTRIBUTE: form_consts.Common.BULK_SKIP + ' id_upload_type_0'}),
                               required=False,
                               label=form_consts.Sample.PASSWORD)
    campaign = forms.ChoiceField(widget=forms.Select, required=False,
                                 label=form_consts.Sample.CAMPAIGN)
    confidence = forms.ChoiceField(required=False, label=form_consts.Sample.CAMPAIGN_CONFIDENCE)
    email = forms.BooleanField(required=False,
                               label=form_consts.Sample.EMAIL_RESULTS)
    related_md5 = forms.CharField(widget=forms.TextInput,
                                 required=False,
                                 label=form_consts.Sample.RELATED_MD5)
    source = forms.ChoiceField(required=True,
                               widget=forms.Select(attrs={'class': 'no_clear bulknoinitial'}),
                               label=form_consts.Sample.SOURCE)
    method = forms.CharField(widget=forms.TextInput,
                                required=False,
                                label=form_consts.Sample.SOURCE_METHOD)
    reference = forms.CharField(widget=forms.TextInput,
                                required=False,
                                label=form_consts.Sample.SOURCE_REFERENCE)

    def __init__(self, username, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name,
                                          c.name) for c in get_source_names(True,
                                                                            True,
                                                                            username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['campaign'].choices = [('', '')] + [
                (c.name, c.name) for c in get_item_names(Campaign, True)]
        self.fields['confidence'].choices = [('', ''),
                                             ('low', 'low'),
                                             ('medium', 'medium'),
                                             ('high', 'high')]

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)

    def clean(self):
        from django.forms.util import ErrorList
        cleaned_data = super(UploadFileForm, self).clean()
        upload_type = cleaned_data.get('upload_type')
        if 'filedata' in self.files:
            filedata = True
        else:
            filedata = False
        filename = cleaned_data.get('filename')
        file_format = cleaned_data.get('file_format')

        if upload_type == "File Upload":
            file_format = cleaned_data.get('file_format')
            if 'filedata' in self.files:
                filedata = True
            else:
                filedata = False

            if not filedata:
                self._errors.setdefault('filedata', ErrorList())
                self._errors['filedata'].append(u'This field is required.')
            if not file_format:
                self._errors.setdefault('file_format', ErrorList())
                self._errors['file_format'].append(u'This field is required.')
        else: #Metadata Upload
            filename = cleaned_data.get('filename')
            md5 = cleaned_data.get('md5')

            if not filename:
                self._errors.setdefault('filename', ErrorList())
                self._errors['filename'].append(u'This field is required.')
            if not md5:
                self._errors.setdefault('md5', ErrorList())
                self._errors['md5'].append(u'This field is required.')

        campaign = cleaned_data.get('campaign')

        if campaign:
            confidence = cleaned_data.get('confidence')

            if not confidence or confidence == '':
                self._errors.setdefault('confidence', ErrorList())
                self._errors['confidence'].append(u'This field is required if campaign is specified.')

        return cleaned_data

class BackdoorForm(forms.Form):
    """
    Django form to handle adding a backdoor to a sample.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    backdoor_types = forms.ChoiceField(required=True,
                                       widget=forms.Select)
    backdoor_version = forms.CharField(widget=forms.TextInput,
                                       required=False)
    def __init__(self, *args, **kwargs):
        super(BackdoorForm, self).__init__(*args, **kwargs)
        self.fields['backdoor_types'].choices = [(c.name,
                                                  c.name
                                                  ) for c in get_item_names(Backdoor,
                                                                            True)]

class NewBackdoorForm(forms.Form):
    """
    Django form to handle uploading a new backdoor.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    name = forms.CharField(widget=forms.TextInput, required=True)

class NewExploitForm(forms.Form):
    """
    Django form to handle uploading a new exploit.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    name = forms.CharField(widget=forms.TextInput, required=True)

class ExploitForm(forms.Form):
    """
    Django form to handle adding an exploit to a sample.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    exploit = forms.ChoiceField(required=True, widget=forms.Select)

    def __init__(self, *args, **kwargs):
        super(ExploitForm, self).__init__(*args, **kwargs)
        self.fields['exploit'].choices = [(c.name,
                                           c.name
                                           ) for c in get_item_names(Exploit,
                                                                     True)]
