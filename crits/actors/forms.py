from django import forms
from django.forms.utils import ErrorList

from crits.actors.actor import ActorThreatIdentifier
from crits.campaigns.campaign import Campaign
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.handlers import get_item_names, get_source_names
from crits.core.user_tools import get_user_organization
from crits.core import form_consts


class AddActorForm(forms.Form):
    """
    Django form for adding an Actor to CRITs.
    """

    error_css_class = 'error'
    required_css_class = 'required'

    name = forms.CharField(label=form_consts.Actor.NAME, required=True)
    aliases = forms.CharField(label=form_consts.Actor.ALIASES, required=False)
    description = forms.CharField(
        label=form_consts.Actor.DESCRIPTION,
        required=False,)
    campaign = forms.ChoiceField(
        widget=forms.Select,
        label=form_consts.Actor.CAMPAIGN,
        required=False)
    confidence = forms.ChoiceField(
        label=form_consts.Actor.CAMPAIGN_CONFIDENCE,
        required=False)
    source = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'bulknoinitial'}),
        label=form_consts.Actor.SOURCE,
        required=True)
    source_method = forms.CharField(
        label=form_consts.Actor.SOURCE_METHOD,
        required=False)
    source_reference = forms.CharField(
        widget=forms.TextInput(attrs={'size': '90'}),
        label=form_consts.Actor.SOURCE_REFERENCE,
        required=False)

    def __init__(self, username, *args, **kwargs):
        super(AddActorForm, self).__init__(*args, **kwargs)

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
        cleaned_data = super(AddActorForm, self).clean()
        campaign = cleaned_data.get('campaign')

        if campaign:
            confidence = cleaned_data.get('confidence')

            if not confidence or confidence == '':
                self._errors.setdefault('confidence', ErrorList())
                self._errors['confidence'].append(u'This field is required if campaign is specified.')

        return cleaned_data


class AddActorIdentifierForm(forms.Form):
    """
    Django form for adding a new Actor Identifier Type.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    identifier_type = forms.ChoiceField(label="Identifier Type", required=True)
    identifier = forms.CharField(widget=forms.TextInput, required=True)
    source = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'bulknoinitial'}),
        label=form_consts.Actor.SOURCE,
        required=True)
    source_method = forms.CharField(
        label=form_consts.Actor.SOURCE_METHOD,
        required=False)
    source_reference = forms.CharField(
        widget=forms.TextInput(attrs={'size': '90'}),
        label=form_consts.Actor.SOURCE_REFERENCE,
        required=False)


    def __init__(self, username, *args, **kwargs):
        super(AddActorIdentifierForm, self).__init__(*args, **kwargs)

        self.fields['identifier_type'].choices = [
            (c.name, c.name) for c in get_item_names(ActorThreatIdentifier, True)]
        self.fields['source'].choices = [
            (c.name, c.name) for c in get_source_names(True, True, username)]
        self.fields['source'].initial = get_user_organization(username)


class AddActorIdentifierTypeForm(forms.Form):
    """
    Django form for adding a new Actor Identifier Type.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    identifier_type = forms.CharField(widget=forms.TextInput, required=True)

class AttributeIdentifierForm(forms.Form):
    """
    Django form for adding a new Actor Identifier Type.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    # The fields will be populated on-the-fly when the form is
    # rendered so we won't populate them here.
    identifier_type = forms.ChoiceField(label="Identifier Type", required=True)
    identifier = forms.ChoiceField(label="Identifier", required=True)
    confidence = forms.ChoiceField(label="Confidence", required=True)

    def __init__(self, *args, **kwargs):
        super(AttributeIdentifierForm, self).__init__(*args, **kwargs)

        self.fields['confidence'].choices = [
            ('low', 'low'),
            ('medium', 'medium'),
            ('high', 'high')]
