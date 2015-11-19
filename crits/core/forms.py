import re

from django import forms
from django.forms.util import ErrorList
from django.forms.widgets import HiddenInput, RadioSelect, SelectMultiple

from crits.core import form_consts
from crits.core.form_consts import Action as ActionConsts
from crits.core.handlers import get_source_names, get_item_names, ui_themes
from crits.core.user_role import UserRole
from crits.core.user_tools import get_user_organization
from crits.core.widgets import CalWidget
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

class ActionsForm(forms.Form):
    """
    Django form for adding actions.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    action_type = forms.ChoiceField(widget=forms.Select,
        label=ActionConsts.ACTION_TYPE,
        required=True)
    begin_date = forms.DateTimeField(
        widget=CalWidget(format='%Y-%m-%d %H:%M:%S',
                         attrs={'class': 'datetimeclass',
                                'size': '25',
                                'id': 'id_action_begin_date'}),
        input_formats=settings.PY_FORM_DATETIME_FORMATS,
        label=ActionConsts.BEGIN_DATE,
        required=False)
    end_date = forms.DateTimeField(
        widget=CalWidget(format='%Y-%m-%d %H:%M:%S',
                         attrs={'class': 'datetimeclass',
                                'size': '25',
                                'id': 'id_action_end_date'}),
        input_formats=settings.PY_FORM_DATETIME_FORMATS,
        label=ActionConsts.END_DATE,
        required=False)
    performed_date = forms.DateTimeField(
        widget=CalWidget(format='%Y-%m-%d %H:%M:%S',
                         attrs={'class': 'datetimeclass',
                                'size': '25',
                                'id': 'id_action_performed_date'}),
        input_formats=settings.PY_FORM_DATETIME_FORMATS,
        label=ActionConsts.PERFORMED_DATE,
        required=False)
    active = forms.ChoiceField(
        widget=RadioSelect,
        choices=(('on', 'on'),
                 ('off', 'off')),
        label=ActionConsts.ACTIVE)
    reason = forms.CharField(
        widget=forms.TextInput(attrs={'size': '50'}),
        required=False)
    date = forms.CharField(
        widget=forms.HiddenInput(attrs={'size': '50',
                                        'readonly': 'readonly',
                                        'id': 'id_action_date'}),
        label=ActionConsts.DATE)

    def __init__(self, *args, **kwargs):
        super(ActionsForm, self).__init__(*args, **kwargs)

class NewActionForm(forms.Form):
    """
    Django form for adding a new Action.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    action = forms.CharField(widget=forms.TextInput, required=True)
    object_types = forms.MultipleChoiceField(required=False,
                                          label=ActionConsts.OBJECT_TYPES,
                                          widget=forms.SelectMultiple,
                                          help_text="Which TLOs this is for.")
    preferred = forms.CharField(required=False,
                                label=ActionConsts.PREFERRED,
                                widget=forms.Textarea(
                                    attrs={'cols': '50', 'rows': '5'}),
                                help_text="CSV of TLO Type, Field, Value.")

    def __init__(self, *args, **kwargs):
        super(NewActionForm, self).__init__(*args, **kwargs)

        # Sort the available TLOs.
        tlos = [tlo for tlo in settings.CRITS_TYPES.keys()]
        tlos.sort()
        self.fields['object_types'].choices = [(tlo, tlo) for tlo in tlos]


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

class ToastNotificationConfigForm(forms.Form):
    """
    Django form for the user toast notifications.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    enabled = forms.BooleanField(initial=True, required=False)
    max_visible_notifications = forms.IntegerField(min_value = 1,
                                                   max_value = 10,
                                                   initial=5,
                                                   required=False,
                                                   label="Max Visible Notifications")
    acknowledgement_type = forms.ChoiceField(widget=forms.Select,
                                             initial="sticky",
                                             required=False,
                                             label="Acknowledgement Type")
    notification_anchor_location = forms.ChoiceField(widget=forms.Select,
                                                     initial="bottom_right",
                                                     required=False,
                                                     label="Anchor Location")
    newer_notifications_location = forms.ChoiceField(widget=forms.Select,
                                                     initial="top",
                                                     required=False,
                                                     label="Newer Notifications Located")
    initial_notifications_display = forms.ChoiceField(widget=forms.Select,
                                                      initial="show",
                                                      required=False,
                                                      label="On New Notifications")
    timeout = forms.IntegerField(min_value = 5,
                                 max_value = 3600,
                                 initial=30,
                                 required=False,
                                 label="Timeout (in seconds)",
                                 help_text="Used only if Acknowledgement Type is set to 'timeout'")

    def __init__(self, request, *args, **kwargs):
        super(ToastNotificationConfigForm, self).__init__(*args, **kwargs)

        prefs = request.user.prefs

        if hasattr(prefs, 'toast_notifications'):
            for k in prefs.toast_notifications:
                if k in self.fields:
                    self.fields[k].initial = prefs.toast_notifications[k]

        self.fields['acknowledgement_type'].choices = [("sticky", "sticky"),
                                                       ("timeout", "timeout")]

        self.fields['notification_anchor_location'].choices = [("top_right", "top_right"),
                                                               ("bottom_right", "bottom_right")]

        self.fields['newer_notifications_location'].choices = [("top", "top"),
                                                               ("bottom", "bottom")]

        self.fields['initial_notifications_display'].choices = [("show", "show"),
                                                                ("hide", "hide")]

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
                                         ("json", "JSON"),
                                         ("json_no_bin", "JSON (no binaries)")],
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
        self.fields['objects'].choices = [('Actor', 'Actors'),
                                          ('Certificate', 'Certificates'),
                                          ('Domain', 'Domains'),
                                          ('Email', 'Emails'),
                                          ('Indicator', 'Indicators'),
                                          ('PCAP', 'PCAPs'),
                                          ('RawData', 'Raw Data'),
                                          ('Sample', 'Samples'),
                                          ('Signature', 'Signatures')]
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
