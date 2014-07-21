import re

from django import forms
from django.forms.util import ErrorList
from django.forms.widgets import HiddenInput, SelectMultiple

from crits.core import form_consts
from crits.core.handlers import get_source_names, get_item_names, ui_themes
from crits.core.user_role import UserRole
from crits.core.user_tools import get_user_organization
from crits.config.config import CRITsConfig
from crits import settings

def add_bucketlist_to_form(input_form):
    """
    Add a bucket_list field to a form.

    :param input_form: The form to add to.
    :type input_form: :class:`django.forms.Form`
    :returns: :class:`django.forms.Form`
    """

    input_form.fields[form_consts.Common.BUCKET_LIST_VARIABLE_NAME] = \
            forms.CharField(widget=forms.TextInput,
                            required=False,
                            label=form_consts.Common.BUCKET_LIST,
                            help_text="Use comma separated values.")

def add_ticket_to_form(input_form):
    """
    Add a tickets field to a form.

    :param input_form: The form to add to.
    :type input_form: :class:`django.forms.Form`
    :returns: :class:`django.forms.Form`
    """

    input_form.fields[form_consts.Common.TICKET_VARIABLE_NAME] = \
            forms.CharField(widget=forms.TextInput,
                            required=False,
                            label=form_consts.Common.TICKET,
                            help_text="Use comma separated values.")

class AddSourceForm(forms.Form):
    """
    Django form for adding a new source to CRITs.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    source = forms.CharField(widget=forms.TextInput, required=True)

class AddReleasabilityForm(forms.Form):
    """
    Django form for adding a new releasability instance to a top-level object.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    source = forms.ChoiceField(required=True, widget=forms.Select)

    def __init__(self, username, *args, **kwargs):
        super(AddReleasabilityForm, self).__init__(*args, **kwargs)
        self.fields['source'].choices = [(c.name,
                                          c.name) for c in get_source_names(True,
                                                                               True,
                                                                               username)]

class NavMenuForm(forms.Form):
    """
    Django form for the user preferences navigation menu.
    """

    error_css_class = 'error'
    required_css_class = 'required'

    DEFAULT_TExT_COLOR = "#FFF"
    DEFAULT_BACKGROUND_COLOR = '#464646'
    DEFAULT_HOVER_TEXT_COLOR = '#39F'
    DEFAULT_HOVER_BACKGROUND_COLOR = '#6F6F6F'

    nav_menu = forms.ChoiceField(widget=forms.RadioSelect(), initial="default",
                                 help_text="Colors currently only work with topmenu. \
                                 Examples of valid color codes: #39F or #9AAED8.")
    text_color = forms.CharField(label="Text Color", initial=DEFAULT_TExT_COLOR,
                                 help_text="Default: " + DEFAULT_TExT_COLOR)
    background_color = forms.CharField(label="Background Color", initial=DEFAULT_BACKGROUND_COLOR,
                                       help_text="Default: " + DEFAULT_BACKGROUND_COLOR)
    hover_text_color = forms.CharField(label="Hover Text Color", initial=DEFAULT_HOVER_TEXT_COLOR,
                                       help_text="Default: " + DEFAULT_HOVER_TEXT_COLOR)
    hover_background_color = forms.CharField(label="Hover Background Color", initial=DEFAULT_HOVER_BACKGROUND_COLOR,
                                             help_text="Default: " + DEFAULT_HOVER_BACKGROUND_COLOR)

    def __init__(self, request, *args, **kwargs):
        super(NavMenuForm, self).__init__(*args, **kwargs)

        prefs = request.user.prefs
        for k in prefs.nav:
            if k in self.fields:
                self.fields[k].initial = prefs.nav[k]

        self.fields['nav_menu'].choices = [('default','default'),
                                        ('topmenu','topmenu')]

    def clean(self):
        cleaned_data = super(NavMenuForm, self).clean()

        def check_hex_color(self, color_code, field_name):
            if not re.match('^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color_code):
                self._errors.setdefault(field_name, ErrorList())
                self._errors[field_name].append("This is not a valid color code. Valid examples: #39F or #9AAED8")

        check_hex_color(self, cleaned_data.get('text_color'), 'text_color')
        check_hex_color(self, cleaned_data.get('background_color'), 'background_color')
        check_hex_color(self, cleaned_data.get('hover_text_color'), 'hover_text_color')
        check_hex_color(self, cleaned_data.get('hover_background_color'), 'hover_background_color')

        return cleaned_data

class PrefUIForm(forms.Form):
    """
    Django form for the user preferences interface.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    theme = forms.ChoiceField(required=True, widget=forms.Select,
                              initial="default")

    # layeredthemes = forms.MultipleChoiceField(required=True,
    #                                           label="Layer Themes",
    #                                           help_text="Pick Themes to use",
    #                                           widget=forms.SelectMultiple)
    table_page_size = forms.IntegerField(required=True, min_value = 2, max_value = 10000,
                                         initial=25)

    def __init__(self, request, *args, **kwargs):
        super(PrefUIForm, self).__init__(*args, **kwargs)

        prefs = request.user.prefs
        for k in prefs.ui:
            if k in self.fields:
                self.fields[k].initial = prefs.ui[k]

#        self.fields['layeredthemes'].choices = self.fields['theme'].choices

        self.fields['theme'].choices = [(t,
                                          t) for t in ui_themes()]

class AddUserRoleForm(forms.Form):
    """
    Django form for adding a new user role.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    role = forms.CharField(widget=forms.TextInput, required=True)

class DownloadFileForm(forms.Form):
    """
    Django form for downloading a top-level object.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    obj_type = forms.CharField(widget=HiddenInput)
    obj_id = forms.CharField(widget=HiddenInput)

    objects = forms.MultipleChoiceField(required=True, label="Objects",
                                        help_text="Objects to collect",
                                        widget=forms.SelectMultiple)

    depth_limit = forms.CharField(widget=forms.TextInput, required=False,
                                  label="Depth",
                                  initial=0,
                                  help_text="Depth levels to traverse.<br />" +
                                            "0 for this object only. Max: %i")

    total_limit = forms.CharField(widget=forms.TextInput, required=False,
                                  label="Maximum",
                                  help_text="Total objects to return. Max: %i")

    rel_limit = forms.CharField(widget=forms.TextInput, required=False,
                                label="Relationships",
                                help_text="If an object has more relationships<br />" +
                                          "than this, ignore it. Max: %i")

    rst_fmt = forms.ChoiceField(choices=[("zip", "zip"),
                                         ("stix", "STIX"),
                                         ("stix_no_bin", "STIX (no binaries)")],
                                         label="Result format")

    bin_fmt = forms.ChoiceField(choices=[("raw", "raw"),
                                         ("base64", "base64"),
                                         ("zlib", "zlib")],
                                         label="Binary format")

    def __init__(self, *args, **kwargs):
        crits_config = CRITsConfig.objects().first()
        depth_max = getattr(crits_config, 'depth_max', settings.DEPTH_MAX)
        total_max = getattr(crits_config, 'total_max', settings.TOTAL_MAX)
        rel_max = getattr(crits_config, 'rel_max', settings.REL_MAX)
        super(DownloadFileForm, self).__init__(*args, **kwargs)
        self.fields['objects'].choices = [('Sample', 'Samples'),
                                          ('Email', 'Emails'),
                                          ('Indicator', 'Indicators'),
                                          ('Domain', 'Domains'),
                                          ('Certificate', 'Certificates'),
                                          ('RawData', 'Raw Data'),
                                          ('PCAP', 'PCAPs')]
        self.fields['total_limit'].initial = total_max
        self.fields['rel_limit'].initial = rel_max
        self.fields['depth_limit'].help_text = self.fields['depth_limit'].help_text % depth_max
        self.fields['total_limit'].help_text = self.fields['total_limit'].help_text % total_max
        self.fields['rel_limit'].help_text = self.fields['rel_limit'].help_text % rel_max


class TLDUpdateForm(forms.Form):
    """
    Django form to update the TLD list.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    filedata = forms.FileField()


class SourceAccessForm(forms.Form):
    """
    Django form for updating a user's profile and source access.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    username = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                               required=True)
    first_name = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                                 required=True)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                                required=True)
    email = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                            required=True)
    sources = forms.MultipleChoiceField(required=True,
                                        widget=SelectMultiple(attrs={'class':'multiselect',
                                                                     'style': 'height: auto;'}))
    organization = forms.ChoiceField(required=True, widget=forms.Select)
    role = forms.ChoiceField(required=True, widget=forms.Select)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'textbox'}),
                               required=False)
    totp = forms.BooleanField(initial=False, required=False)
    secret = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                             required=False)
    subscriptions = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(SourceAccessForm, self).__init__(*args, **kwargs)
        self.fields['sources'].choices = [(c.name,
                                           c.name) for c in get_source_names(False,
                                                                             False,
                                                                             None)]
        self.fields['role'].choices = [(c.name,
                                        c.name) for c in get_item_names(UserRole,
                                                                           True)]
        self.fields['organization'].choices = [(c.name,
                                                c.name) for c in get_source_names(True,
                                                                                     False,
                                                                                     None)]


class SourceForm(forms.Form):
    """
    Django form to add source information to a top-level object.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    name = forms.ChoiceField(required=True, widget=forms.Select)
    date = forms.CharField(widget=HiddenInput(attrs={'readonly': 'readonly',
                                                     'id': 'source_added_date'}),
                                                     required=False)
    method = forms.CharField(widget=forms.TextInput(attrs={'size': '90'}),
                             required=False)
    reference = forms.CharField(widget=forms.TextInput(attrs={'size': '90'}),
                                required=False)
    analyst = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    def __init__(self, username, *args, **kwargs):
        super(SourceForm, self).__init__(*args, **kwargs)
        self.fields['name'].choices = [(c.name,
                                        c.name) for c in get_source_names(True,
                                                                             True,
                                                                             username)]
        self.fields['name'].initial = get_user_organization(username)


class TicketForm(forms.Form):
    """
    Django form to add a ticket to a top-level object.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    ticket_number = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}),
                                    required=True)
    date = forms.CharField( widget=forms.HiddenInput(attrs={'size': '50',
                                                            'readonly':'readonly',
                                                            'id':'id_indicator_ticket_date'}))
