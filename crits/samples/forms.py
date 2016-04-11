from django import forms
from django.forms.widgets import RadioSelect

from crits.campaigns.campaign import Campaign
from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.handlers import get_source_names, get_item_names
from crits.backdoors.handlers import get_backdoor_names
from crits.core.user_tools import get_user_organization

from crits.vocabulary.relationships import RelationshipTypes

relationship_choices = [(c, c) for c in RelationshipTypes.values(sort=True)]

class UnzipSampleForm(forms.Form):
    """
    Django form to handle unziping a sample.
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
    sha1 = forms.CharField(widget=forms.TextInput(attrs={form_consts.Common.CLASS_ATTRIBUTE: form_consts.Common.BULK_REQUIRED + ' id_upload_type_1'}),
                           required=False,
                           label=form_consts.Sample.SHA1)
    sha256 = forms.CharField(widget=forms.TextInput(attrs={form_consts.Common.CLASS_ATTRIBUTE: form_consts.Common.BULK_REQUIRED + ' id_upload_type_1'}),
                             required=False,
                             label=form_consts.Sample.SHA256)
    size = forms.CharField(widget=forms.TextInput(attrs={form_consts.Common.CLASS_ATTRIBUTE: form_consts.Common.BULK_REQUIRED + ' id_upload_type_1'}),
                           required=False,
                           label=form_consts.Sample.SIZE)
    mimetype = forms.CharField(widget=forms.TextInput(attrs={form_consts.Common.CLASS_ATTRIBUTE: form_consts.Common.BULK_REQUIRED + ' id_upload_type_1'}),
                               required=False,
                               label=form_consts.Sample.MIMETYPE)
    file_format = forms.ChoiceField(widget=RadioSelect(attrs={form_consts.Common.CLASS_ATTRIBUTE: form_consts.Common.BULK_SKIP + ' id_upload_type_0 required'}),
                                    choices=[("zip", "7z/Zip/RAR"),
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
    inherit_campaigns = forms.BooleanField(initial=True,
                                           required=False,
                                           label=form_consts.Sample.INHERIT_CAMPAIGNS)
    source = forms.ChoiceField(required=True,
                               widget=forms.Select(attrs={'class': 'no_clear bulknoinitial'}),
                               label=form_consts.Sample.SOURCE)
    method = forms.CharField(widget=forms.TextInput,
                                required=False,
                                label=form_consts.Sample.SOURCE_METHOD)
    reference = forms.CharField(widget=forms.TextInput,
                                required=False,
                                label=form_consts.Sample.SOURCE_REFERENCE)
    inherit_sources = forms.BooleanField(initial=True,
                                         required=False,
                                         label=form_consts.Sample.INHERIT_SOURCES)
    related_md5 = forms.CharField(widget=forms.TextInput,
                                 required=False,
                                 label=form_consts.Sample.RELATED_MD5)
    email = forms.BooleanField(required=False,
                               label=form_consts.Sample.EMAIL_RESULTS)
    backdoor = forms.ChoiceField(widget=forms.Select, required=False,
                                 label=form_consts.Backdoor.NAME)
    related_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    related_type = forms.CharField(widget=forms.HiddenInput(), required=False)
    relationship_type = forms.ChoiceField(required=False,
                                          label='Relationship Type',
                                          widget=forms.Select(attrs={'id':'relationship_type'}))

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
        self.fields['backdoor'].choices = [('', '')]

        self.fields['relationship_type'].choices = relationship_choices
        self.fields['relationship_type'].initial = RelationshipTypes.RELATED_TO

        for (name, version) in get_backdoor_names(username):
            display = name
            value = name + '|||' + version
            if version:
                display += ' (Version: ' + version + ')'
            self.fields['backdoor'].choices.append((value, display))

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)

    def clean(self):
        from django.forms.utils import ErrorList
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

        inherit_campaigns = cleaned_data.get('inherit_campaigns')
        inherit_sources = cleaned_data.get('inherit_sources')
        if inherit_campaigns or inherit_sources:
            related_md5 = cleaned_data.get('related_md5')
            related_id = cleaned_data.get('related_id')
            if not (related_md5 or related_id):
                if inherit_campaigns:
                    self._errors.setdefault('inherit_campaigns', ErrorList())
                    self._errors['inherit_campaigns'].append(u'Nothing to inherit from.')
                if inherit_sources:
                    self._errors.setdefault('inherit_sources', ErrorList())
                    self._errors['inherit_sources'].append(u'Nothing to inherit from.')
                self._errors.setdefault('related_md5', ErrorList())
                self._errors['related_md5'].append(u'Need a Related MD5 from which to inherit.')

        return cleaned_data
