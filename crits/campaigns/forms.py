from django import forms
from django.forms.widgets import HiddenInput

from crits.campaigns.campaign import Campaign
from crits.core.forms import add_bucketlist_to_form, add_ticket_to_form
from crits.core.handlers import get_item_names

from crits.vocabulary.relationships import RelationshipTypes

relationship_choices = [(c, c) for c in RelationshipTypes.values(sort=True)]

class AddCampaignForm(forms.Form):
    """
    Django form for adding a new Campaign.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    campaign = forms.CharField(widget=forms.TextInput, required=True)
    aliases = forms.CharField(widget=forms.TextInput, required=False)
    description = forms.CharField(widget=forms.TextInput, required=False)
    related_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    related_type = forms.CharField(widget=forms.HiddenInput(), required=False)
    relationship_type = forms.ChoiceField(required=False,
                                          label='Relationship Type',
                                          widget=forms.Select(attrs={'id':'relationship_type'}))

    def __init__(self, *args, **kwargs):
        super(AddCampaignForm, self).__init__(*args, **kwargs)
        self.fields['relationship_type'].choices = relationship_choices
        self.fields['relationship_type'].initial = RelationshipTypes.RELATED_TO

        add_bucketlist_to_form(self)
        add_ticket_to_form(self)

class TTPForm(forms.Form):
    """
    Django form for adding/editing a Campaign TTP.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    ttp = forms.CharField(
        widget=forms.Textarea(attrs={'cols': '35',
                                     'rows': '5'}),
        required=True)

class CampaignForm(forms.Form):
    """
    Django form for attributing a Campaign to another object.

    The list of names comes from :func:`get_item_names`.
    Confidence can be one of "low", "medium", or "high".
    """

    error_css_class = 'error'
    required_css_class = 'required'
    name = forms.ChoiceField(widget=forms.Select, required=True)
    confidence = forms.ChoiceField(widget=forms.Select, required=True)
    description = forms.CharField(widget=forms.Textarea(), required=False)
    date = forms.CharField(widget=HiddenInput, required=False)
    related = forms.BooleanField(
        help_text="Apply to all first level related objects.",
        initial=False,
        required=False)

    def __init__(self, *args, **kwargs):
        super(CampaignForm, self).__init__(*args, **kwargs)
        self.fields['confidence'].choices = [
            ('low', 'low'),
            ('medium', 'medium'),
            ('high', 'high'),
        ]
        self.fields['name'].choices = [
            (c.name, c.name) for c in get_item_names(Campaign, True)]
