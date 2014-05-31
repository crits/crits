from django.conf import settings
from django import forms
from crits.core.widgets import CalWidget
from crits.relationships.handlers import get_relationship_types

class ForgeRelationshipForm(forms.Form):
    """
    Django form for forging relationships between two top-level objects.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    forward_type = forms.CharField(required=True,
                                   label="Source Type",
                                   widget = forms.TextInput(attrs={'readonly':'readonly'}))
    forward_value = forms.CharField(required=True,
                                    label="Source ID",
                                    widget = forms.TextInput(attrs={'readonly':'readonly'}))
    forward_relationship = forms.ChoiceField(required=True,
                                             widget=forms.Select(attrs={'class':'relationship-types'}),
                                             label="Relationship")
    reverse_type = forms.ChoiceField(required=True,
                                     widget=forms.Select,
                                     label="Dest Type")
    dest_id = forms.CharField(required=True,
                              label="Dest ID")
    relationship_date = forms.DateTimeField(widget=CalWidget(format=settings.PY_DATETIME_FORMAT,
                                                             attrs={'class':'datetimeclass',
                                                                    'size':'25'}),
                                            input_formats=settings.PY_FORM_DATETIME_FORMATS,
                                            required=False,
                                            label="Relationship Date")

    def __init__(self, *args, **kwargs):
        super(ForgeRelationshipForm, self).__init__(*args, **kwargs)
        self.fields['forward_type'].choices = self.fields['reverse_type'].choices = [(c, c) for c in sorted(settings.CRITS_TYPES.iterkeys())]
        self.fields['forward_relationship'].choices = [(c, c) for c in get_relationship_types(True)]

    def clean(self):
        cleaned_data = super(ForgeRelationshipForm, self).clean()

        if 'forward_value' in cleaned_data:
            try:
                cleaned_data['forward_value'] = cleaned_data['forward_value'].strip()
            except:
                pass

        if 'dest_id' in cleaned_data:
            try:
                cleaned_data['dest_id'] = cleaned_data['dest_id'].strip()
            except:
                pass

        return cleaned_data
