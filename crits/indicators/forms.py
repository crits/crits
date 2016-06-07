from django.conf import settings
from django import forms
from django.forms.widgets import RadioSelect

from crits.campaigns.campaign import Campaign
from crits.core import form_consts
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.widgets import CalWidget
from crits.core.handlers import get_source_names, get_item_names
from crits.core.user_tools import get_user_organization
from crits.vocabulary.indicators import (
    IndicatorTypes,
    IndicatorThreatTypes,
    IndicatorAttackTypes
)

from crits.vocabulary.relationships import RelationshipTypes

relationship_choices = [(c, c) for c in RelationshipTypes.values(sort=True)]

class IndicatorActivityForm(forms.Form):
    """
    Django form for adding activity.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    description = forms.CharField(
        widget=forms.TextInput(attrs={'size': '50'}),
        required=False)
    start_date = forms.DateTimeField(
        widget=CalWidget(format='%Y-%m-%d %H:%M:%S',
                         attrs={'class': 'datetimeclass',
                                'size': '25',
                                'id': 'id_activity_start_date'}),
        input_formats=settings.PY_FORM_DATETIME_FORMATS,
        required=False)
    end_date = forms.DateTimeField(
        widget=CalWidget(format='%Y-%m-%d %H:%M:%S',
                         attrs={'class': 'datetimeclass',
                                'size': '25',
                                'id': 'id_activity_end_date'}),
        input_formats=settings.PY_FORM_DATETIME_FORMATS,
        required=False)
    date = forms.CharField(
        widget=forms.HiddenInput(attrs={'size': '50',
                                        'readonly': 'readonly',
                                        'id': 'id_activity_date'}))

class UploadIndicatorCSVForm(forms.Form):
    """
    Django form for uploading Indicators via a CSV file.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    filedata = forms.FileField()
    source = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'no_clear'}),
        label=form_consts.Indicator.SOURCE,
        required=True)
    method = forms.CharField(
        widget=forms.TextInput,
        label=form_consts.Indicator.SOURCE_METHOD,
        required=False)
    reference = forms.CharField(
        widget=forms.TextInput(attrs={'size': '90'}),
        label=form_consts.Indicator.SOURCE_REFERENCE,
        required=False)
    related_id = forms.CharField(widget=forms.HiddenInput(), required=False, label=form_consts.Common.RELATED_ID)
    related_type = forms.CharField(widget=forms.HiddenInput(), required=False, label=form_consts.Common.RELATED_TYPE)
    relationship_type = forms.ChoiceField(required=False,
                                          label=form_consts.Common.RELATIONSHIP_TYPE,
                                          widget=forms.Select(attrs={'id':'relationship_type'}))

    def __init__(self, username, *args, **kwargs):
        super(UploadIndicatorCSVForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [
            (c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['relationship_type'].choices = relationship_choices
        self.fields['relationship_type'].initial = RelationshipTypes.RELATED_TO

class UploadIndicatorTextForm(forms.Form):
    """
    Django form for uploading Indicators via a CSV blob.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    source = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'no_clear'}),
        label=form_consts.Indicator.SOURCE,
        required=True)
    method = forms.CharField(
        widget=forms.TextInput,
        label=form_consts.Indicator.SOURCE_METHOD,
        required=False)
    reference = forms.CharField(
        widget=forms.TextInput(attrs={'size': '90'}),
        label=form_consts.Indicator.SOURCE_REFERENCE,
        required=False)
    data = forms.CharField(
        widget=forms.Textarea(attrs={'cols': '80', 'rows': '20'}),
        required=True)
    related_id = forms.CharField(widget=forms.HiddenInput(), required=False, label=form_consts.Common.RELATED_ID)
    related_type = forms.CharField(widget=forms.HiddenInput(), required=False, label=form_consts.Common.RELATED_TYPE)
    relationship_type = forms.ChoiceField(required=False,
                                          label=form_consts.Common.RELATIONSHIP_TYPE,
                                          widget=forms.Select(attrs={'id':'relationship_type'}))

    def __init__(self, username, *args, **kwargs):
        super(UploadIndicatorTextForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [
            (c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)
        dt = "Indicator, Type, Threat Type, Attack Type, Description, Campaign, Campaign Confidence, Confidence, Impact, Bucket List, Ticket, Action, Status\n"
        self.fields['data'].initial = dt
        self.fields['relationship_type'].choices = relationship_choices
        self.fields['relationship_type'].initial = RelationshipTypes.RELATED_TO

class UploadIndicatorForm(forms.Form):
    """
    Django form for uploading a single Indicator.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    indicator_type = forms.ChoiceField(widget=forms.Select, required=True)
    threat_type = forms.ChoiceField(widget=forms.Select, required=True)
    attack_type = forms.ChoiceField(widget=forms.Select, required=True)
    value = forms.CharField(
        widget=forms.Textarea(attrs={'rows': '5', 'cols': '28'}),
        required=True)
    description = forms.CharField(
        widget=forms.TextInput(attrs={'size': '50'}),
        required=False)
    confidence = forms.ChoiceField(widget=forms.Select, required=True)
    impact = forms.ChoiceField(widget=forms.Select, required=True)
    campaign = forms.ChoiceField(widget=forms.Select, required=False)
    campaign_confidence = forms.ChoiceField(widget=forms.Select, required=False)
    source = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'no_clear'}),
        label=form_consts.Indicator.SOURCE,
        required=True)
    method = forms.CharField(
        widget=forms.TextInput,
        label=form_consts.Indicator.SOURCE_METHOD,
        required=False)
    reference = forms.CharField(
        widget=forms.TextInput(attrs={'size': '90'}),
        label=form_consts.Indicator.SOURCE_REFERENCE,
        required=False)
    related_id = forms.CharField(widget=forms.HiddenInput(), required=False, label=form_consts.Common.RELATED_ID)
    related_type = forms.CharField(widget=forms.HiddenInput(), required=False, label=form_consts.Common.RELATED_TYPE)
    relationship_type = forms.ChoiceField(required=False,
                                          label=form_consts.Common.RELATIONSHIP_TYPE,
                                          widget=forms.Select(attrs={'id':'relationship_type'}))

    def __init__(self, username, *args, **kwargs):
        super(UploadIndicatorForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [
            (c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)
        self.fields['indicator_type'].choices = [
            (c,c) for c in IndicatorTypes.values(sort=True)
        ]
        self.fields['threat_type'].choices = [
            (c,c) for c in IndicatorThreatTypes.values(sort=True)
        ]
        self.fields['threat_type'].initial = IndicatorThreatTypes.UNKNOWN
        self.fields['attack_type'].choices = [
            (c,c) for c in IndicatorAttackTypes.values(sort=True)
        ]
        self.fields['attack_type'].initial = IndicatorAttackTypes.UNKNOWN
        self.fields['indicator_type'].widget.attrs = {'class': 'object-types'}
        self.fields['campaign'].choices = [("", "")]
        self.fields['campaign'].choices += [
            (c.name, c.name) for c in get_item_names(Campaign, True)]
        self.fields['campaign_confidence'].choices = [
            ("", ""),
            ("low", "low"),
            ("medium", "medium"),
            ("high", "high")]
        self.fields['confidence'].choices = [
            ("unknown", "unknown"),
            ("benign", "benign"),
            ("low", "low"),
            ("medium", "medium"),
            ("high", "high")]
        self.fields['impact'].choices = [
            ("unknown", "unknown"),
            ("benign", "benign"),
            ("low", "low"),
            ("medium", "medium"),
            ("high", "high")]

        self.fields['relationship_type'].choices = relationship_choices
        self.fields['relationship_type'].initial = RelationshipTypes.RELATED_TO

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)
