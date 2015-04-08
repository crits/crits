from django import forms

from crits.locations.location import Location
from crits.core.handlers import get_item_names

class AddLocationForm(forms.Form):
    """
    Django form for adding a location to a TLO.

    The list of names comes from :func:`get_item_names`.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    location_type = forms.ChoiceField(widget=forms.Select, required=True)
    country = forms.ChoiceField(widget=forms.Select, required=True)
    description = forms.CharField(
        widget=forms.TextInput(attrs={'size': '50'}),
        required=False)
    latitude = forms.CharField(
        widget=forms.TextInput(attrs={'size': '50'}),
        required=False)
    longitude = forms.CharField(
        widget=forms.TextInput(attrs={'size': '50'}),
        required=False)

    def __init__(self, *args, **kwargs):
        super(AddLocationForm, self).__init__(*args, **kwargs)
        self.fields['location_type'].choices = [
            ('Originated From', 'Originated From'),
            ('Destined For', 'Destined For'),
        ]
        self.fields['country'].choices = [
            (c.name, c.name) for c in get_item_names(Location, True)]
