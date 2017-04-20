from django import forms
from django.conf import settings
#from crits.core.form_utils import decorate_bound_field
#decorate_bound_field()


class ConfigGeneralForm(forms.Form):
    """
    Django form for updating the CRITs Configuration.
    """

    required_css_class = 'required'
    debug = forms.BooleanField(
        help_text='*Requires a web server restart.',
        initial=False,
        required=False)
    email_host = forms.CharField(
        widget=forms.TextInput,
        help_text='*Requires a web server restart.',
        required=False)
    email_port = forms.CharField(
        widget=forms.TextInput,
        help_text='*Requires a web server restart.',
        required=False)
    enable_api = forms.BooleanField(
        help_text='*Requires a web server restart.',
        initial=False,
        required=False)
    http_proxy = forms.CharField(
        widget=forms.TextInput,
        help_text='*Requires a web server restart.',
        required=False)
    language_code = forms.CharField(
        widget=forms.TextInput,
        help_text='*Requires a web server restart.',
        initial='en-us',
        required=True)
    query_caching = forms.BooleanField(
        help_text=('*Requires a web server restart. Caching will improve '
                   'performance but will consume more memory to do so!'),
        initial=False,
        required=False)
    rt_url = forms.CharField(
        widget=forms.TextInput,
        label='Ticketing URL',
        help_text='*Requires a web server restart.',
        required=False)
    session_timeout = forms.CharField(
        widget=forms.TextInput,
        help_text='Session timeout in hours',
        initial='12',
        required=False)
    splunk_search_url = forms.CharField(
        widget=forms.TextInput,
        help_text='*Requires a web server restart.',
        required=False)
    temp_dir = forms.CharField(
        widget=forms.TextInput,
        help_text='*Requires a web server restart.',
        required=True)
    timezone = forms.CharField(
        widget=forms.TextInput,
        help_text='*Requires a web server restart.',
        initial='America/New_York',
        required=True)
    zip7_path = forms.CharField(
        widget=forms.TextInput,
        help_text='*Requires a web server restart.',
        required=True)
    zip7_password = forms.CharField(
        widget=forms.TextInput,
        label='ZIP Password for downloaded artifacts',
        required=False)
    enable_toasts = forms.BooleanField(initial=False,
        label="Enable Toast Notifications",
        help_text='*Requires a web server restart.',
        required=False)

    def __init__(self, *args, **kwargs):
        super(ConfigGeneralForm, self).__init__(*args, **kwargs)


class ConfigLDAPForm(forms.Form):
    required_css_class = 'required'
    ldap_tls = forms.BooleanField(initial=False, required=False)
    ldap_server = forms.CharField(
        widget=forms.TextInput,
        help_text='Include :port if not 389.',
        required=False)
    ldap_bind_dn = forms.CharField(
        widget=forms.TextInput,
        required=False,
        help_text=('bind_dn for binding to LDAP'))
    ldap_bind_password = forms.CharField(
        widget=forms.TextInput,
        required=False,
        help_text=('bind_password for binding to LDAP'))
    ldap_usercn = forms.CharField(
        widget=forms.TextInput,
        help_text='Optional cn for user lookup.<br />E.g. "uid=" or "cn="',
        required=False)
    ldap_userdn = forms.CharField(widget=forms.TextInput, required=False)
    ldap_update_on_login = forms.BooleanField(
        help_text='Update user details at each login',
        initial=False,
        required=False)
    def __init__(self, *args, **kwargs):
        super(ConfigLDAPForm, self).__init__(*args, **kwargs)

class ConfigSecurityForm(forms.Form):
    required_css_class = 'required'
    allowed_hosts = forms.CharField(
        widget=forms.TextInput,
        help_text=('A list of strings representing the host/domain names that'
                   ' this site can serve.<br />*Leaving this as * is BAD!<br />'
                   '*Requires a web server restart.'),
        initial='*',
        required=True)
    invalid_login_attempts = forms.CharField(widget=forms.TextInput, required=True)
    password_complexity_regex = forms.CharField(
        widget=forms.TextInput,
        help_text='*Complexity regex for new passwords',
        initial='(?=^.{8,}$)((?=.*\\d)|(?=.*\\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$',
        required=True)
    password_complexity_desc = forms.CharField(
        widget=forms.TextInput,
        help_text='*Description of complexity regex',
        initial='8 characters, at least 1 capital, 1 lowercase and 1 number/special',
        required=True)
    ldap_auth = forms.BooleanField(initial=False, required=False)
    remote_user = forms.BooleanField(
        help_text='*Requires a web server restart. Disables other authentication methods.',
        initial=False,
        required=False)
    create_unknown_user = forms.BooleanField(
        help_text=('Creates CRITs accounts for users authenticated through '
                   'REMOTE_USER. Will use LDAP info if ldap settings are '
                   'filled out.'),
        initial=False,
        required=False)
    totp_web = forms.ChoiceField(
        widget=forms.Select(),
        choices=[('Optional', 'Optional'),
                 ('Required', 'Required'),
                 ('Disabled', 'Disabled')],
        initial='Optional',
        required=False)
    totp_cli = forms.ChoiceField(
        widget=forms.Select(),
        choices=[('Optional', 'Optional'),
                 ('Required', 'Required'),
                 ('Disabled', 'Disabled')],
        initial='Disabled',
        required=False)
    secure_cookie = forms.BooleanField(initial=True, required=False)
    def __init__(self, *args, **kwargs):
        super(ConfigSecurityForm, self).__init__(*args, **kwargs)

class ConfigLoggingForm(forms.Form):
    required_css_class = 'required'
    log_directory = forms.CharField(
        widget=forms.TextInput,
        help_text=('Directory to find the crits.log file.<br />'
                   '*Requires a web server restart.'),
        initial='',
        required=False)
    log_level = forms.ChoiceField(
        widget=forms.Select(),
        help_text='*Requires a web server restart.',
        choices=[('INFO', 'INFO'),
                 ('DEBUG', 'DEBUG'),
                 ('WARN', 'WARN')],
        initial='INFO',
        required=True)
    def __init__(self, *args, **kwargs):
        super(ConfigLoggingForm, self).__init__(*args, **kwargs)

class ConfigServicesForm(forms.Form):
    required_css_class = 'required'
    service_dirs = forms.CharField(
        widget=forms.Textarea(attrs={'cols': '25',
                                     'rows': '3'}),
        label='Service Directories',
        help_text=('List of absolute directory paths.<br />'
                   '*Requires a web server restart.'),
        required=False)
    service_model = forms.ChoiceField(
        widget=forms.Select(),
        help_text=('Warning: Using process_pool may be memory intensive.<br />'
                   '*Requires a web server restart.'),
        choices=[
            ('process', 'process'),
            ('thread', 'thread'),
            ('process_pool', 'process_pool'),
            ('thread_pool', 'thread_pool'),
            ('local', 'local')],
        initial='process',
        required=True)
    service_pool_size = forms.IntegerField(
        help_text=('Service Thread/Process Pool Size<br />'
                   '*Requires a web server restart.'),
        initial='12',
        min_value=1,
        required=True)
    def __init__(self, *args, **kwargs):
        super(ConfigServicesForm, self).__init__(*args, **kwargs)


class ConfigDownloadForm(forms.Form):
    required_css_class = 'required'
    depth_max = forms.CharField(
        widget=forms.TextInput,
        help_text='Maximum depth when downloading objects',
        initial='10',
        required=False)
    total_max = forms.CharField(
        widget=forms.TextInput,
        help_text='Maximum number of objects to download',
        initial='250',
        required=False)
    rel_max = forms.CharField(
        widget=forms.TextInput,
        help_text='Maximum relationships an object can have while downloading',
        initial='50',
        required=False)
    def __init__(self, *args, **kwargs):
        super(ConfigDownloadForm, self).__init__(*args, **kwargs)

class ConfigCritsForm(forms.Form):
    required_css_class = 'required'
    company_name = forms.CharField(widget=forms.TextInput, required=True)
    classification = forms.CharField(widget=forms.TextInput, required=True)
    crits_message = forms.CharField(
        widget=forms.Textarea(attrs={'cols': '25',
                                     'rows': '3'}),
        label='CRITS Message',
        help_text='Message to user on the Login page',
        initial='Welcome to CRITs!',
        required=False)
    crits_email = forms.CharField(
        widget=forms.TextInput,
        label='CRITs Email',
        help_text='*Requires a web server restart.',
        required=True)
    crits_email_subject_tag = forms.CharField(
        widget=forms.TextInput,
        label="Text to tag on to every Email's subject line",
        help_text='*Requires a web server restart.',
        required=False)
    crits_email_end_tag = forms.BooleanField(
        label='Tag on the end (default=True) or the beginning',
        help_text='*Requires a web server restart.',
        initial=True,
        required=False)
    crits_version = forms.CharField(
        widget=forms.TextInput,
        label='DB Version',
        initial=settings.CRITS_VERSION,
        required=True)
    git_repo_url = forms.CharField(
        widget=forms.TextInput,
        label='Git Repo URL',
        initial=settings.CRITS_VERSION,
        required=False)
    instance_name = forms.CharField(widget=forms.TextInput, required=True)
    instance_url = forms.CharField(widget=forms.TextInput, required=True)
    def __init__(self, *args, **kwargs):
        super(ConfigCritsForm, self).__init__(*args, **kwargs)
        self.fields['crits_version'].widget.attrs['readonly'] = True
