from django import forms
from django.conf import settings
#from crits.core.form_utils import decorate_bound_field
#decorate_bound_field()


class ConfigGeneralForm(forms.Form):
    """
    Django form for updating the CRITs Configuration.
    """

    required_css_class = 'required'
    debug = forms.BooleanField(initial=False,
                               required=False,
                               help_text='*Requires a web server restart.')
    email_host = forms.CharField(widget=forms.TextInput, required=False,
                                 help_text='*Requires a web server restart.')
    email_port = forms.CharField(widget=forms.TextInput, required=False,
                                 help_text='*Requires a web server restart.')
    enable_api = forms.BooleanField(initial=False,
                                    required=False,
                                    help_text='*Requires a web server restart.')
    http_proxy = forms.CharField(widget=forms.TextInput, required=False,
                                 help_text='*Requires a web server restart.')
    language_code = forms.CharField(widget=forms.TextInput,
                                    required=True,
                                    initial='en-us',
                                    help_text='*Requires a web server restart.')
    query_caching = forms.BooleanField(initial=False,
                                       required=False,
                                       help_text='*Requires a web server restart. '
                                       'Caching will improve performance but will '
                                       'consume more memory to do so!')
    rar_path = forms.CharField(widget=forms.TextInput, required=True,
                               help_text='*Requires a web server restart.')
    rt_url = forms.CharField(widget=forms.TextInput,
                             required=False,
                             label="Ticketing URL",
                             help_text='*Requires a web server restart.')
    session_timeout = forms.CharField(widget=forms.TextInput,
                                      required=False,
                                      initial="12",
                                      help_text='Session timeout in hours')
    splunk_search_url = forms.CharField(widget=forms.TextInput, required=False,
                                        help_text='*Requires a web server restart.')
    temp_dir = forms.CharField(widget=forms.TextInput, required=True,
                               help_text='*Requires a web server restart.')
    timezone = forms.CharField(widget=forms.TextInput,
                               required=True,
                               initial="America/New_York",
                               help_text='*Requires a web server restart.')
    zip7_path = forms.CharField(widget=forms.TextInput, required=True,
                                help_text='*Requires a web server restart.')
    def __init__(self, *args, **kwargs):
        super(ConfigGeneralForm, self).__init__(*args, **kwargs)


class ConfigLDAPForm(forms.Form):
    required_css_class = 'required'
    ldap_tls = forms.BooleanField(initial=False,
                                  required=False)
    ldap_server = forms.CharField(widget=forms.TextInput, required=False,
                                  help_text=('Include :port if not 389.'))
    ldap_usercn = forms.CharField(widget=forms.TextInput, required=False,
                                  help_text=('Optional cn for user lookup.'
                                             '<br />E.g. "uid=" or "cn="'))
    ldap_userdn = forms.CharField(widget=forms.TextInput, required=False)
    ldap_update_on_login = forms.BooleanField(initial=False,
                                              required=False,
                                              help_text="Update user details "
                                              "at each login")
    def __init__(self, *args, **kwargs):
        super(ConfigLDAPForm, self).__init__(*args, **kwargs)

class ConfigSecurityForm(forms.Form):
    required_css_class = 'required'
    allowed_hosts = forms.CharField(widget=forms.TextInput,
                                    required=True,
                                    initial="*",
                                    help_text=('A list of strings representing'
                                               ' the host/domain names that'
                                               ' this site can serve.<br />'
                                               '*Leaving this as * is BAD!<br />'
                                               '*Requires a web server restart.'))
    invalid_login_attempts = forms.CharField(widget=forms.TextInput, required=True)
    password_complexity_regex = forms.CharField(
                                widget=forms.TextInput,
                                required=True,
                                initial='(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$',
                                help_text="*Complexity regex for new passwords")
    password_complexity_desc = forms.CharField(
                               widget=forms.TextInput,
                               required=True,
                               initial='8 characters, at least 1 capital, 1 lowercase and 1 number/special',
                               help_text="*Description of complexity regex")
    ldap_auth = forms.BooleanField(initial=False,
                                   required=False)
    remote_user = forms.BooleanField(initial=False,
                                     required=False,
                                     help_text='*Requires a web server restart. '
                                     'Disables other authentication methods.')
    create_unknown_user = forms.BooleanField(initial=False,
                                             required=False,
                                             help_text='Creates CRITs accounts '
                                             'for users authenticated through '
                                             'REMOTE_USER. Will use LDAP info '
                                             'if ldap settings are filled out.')
    totp_web = forms.ChoiceField(choices=[('Optional', 'Optional'),
                                          ('Required', 'Required'),
                                          ('Disabled', 'Disabled')],
                                  widget=forms.Select(),
                                  required=False,
                                  initial='Optional')
    totp_cli = forms.ChoiceField(choices=[('Optional', 'Optional'),
                                          ('Required', 'Required'),
                                          ('Disabled', 'Disabled')],
                                  widget=forms.Select(),
                                  required=False,
                                  initial='Disabled')
    secure_cookie = forms.BooleanField(initial=True,
                                       required=False)
    def __init__(self, *args, **kwargs):
        super(ConfigSecurityForm, self).__init__(*args, **kwargs)

class ConfigLoggingForm(forms.Form):
    required_css_class = 'required'
    log_directory = forms.CharField(widget=forms.TextInput,
                                    required=False,
                                    initial='',
                                    help_text=('Directory to find the crits.log'
                                               ' file.<br />'
                                               '*Requires a web server restart.'))
    log_level = forms.ChoiceField(choices=[('INFO',
                                              'INFO'),
                                             ('DEBUG',
                                              'DEBUG'),
                                             ('WARN',
                                              'WARN')],
                                  widget=forms.Select(),
                                  required=True,
                                  initial='INFO',
                                  help_text='*Requires a web server restart.')
    def __init__(self, *args, **kwargs):
        super(ConfigLoggingForm, self).__init__(*args, **kwargs)

class ConfigServicesForm(forms.Form):
    required_css_class = 'required'
    service_dirs = forms.CharField(widget=forms.Textarea(attrs={'cols': '25',
                                                                'rows': '3'}),
                                   required=True,
                                   label="Service Directories",
                                   help_text=('List of absolute directory '
                                              'paths.<br />'
                                              '*Requires a web server restart.'))
    service_model = forms.ChoiceField(choices=[
                                               ('process', 'process'),
                                               ('thread', 'thread'),
                                               ('process_pool', 'process_pool'),
                                               ('thread_pool', 'thread_pool'),
                                               ('local', 'local')],
                                      widget=forms.Select(),
                                      required=True,
                                      initial='process',
                                      help_text=('Warning: Using process_pool '
                                                 'may be memory intensive.<br />'
                                                 '*Requires a web server restart.'))
    service_pool_size = forms.IntegerField(required=True,
                                           min_value=1,
                                           initial="12",
                                           help_text=('Service Thread/Process Pool Size<br />'
                                                      '*Requires a web server restart.'))
    def __init__(self, *args, **kwargs):
        super(ConfigServicesForm, self).__init__(*args, **kwargs)


class ConfigDownloadForm(forms.Form):
    required_css_class = 'required'
    depth_max = forms.CharField(widget=forms.TextInput,
                                required=False,
                                initial="10",
                                help_text='Maximum depth when downloading objects')
    total_max = forms.CharField(widget=forms.TextInput,
                                required=False,
                                initial="250",
                                help_text='Maximum number of objects to download')
    rel_max = forms.CharField(widget=forms.TextInput,
                              required=False,
                              initial="50",
                              help_text='Maximum relationships an object can have while downloading')
    def __init__(self, *args, **kwargs):
        super(ConfigDownloadForm, self).__init__(*args, **kwargs)

class ConfigCritsForm(forms.Form):
    required_css_class = 'required'
    company_name = forms.CharField(widget=forms.TextInput, required=True)
    classification = forms.CharField(widget=forms.TextInput, required=True)
    crits_message = forms.CharField(widget=forms.Textarea(attrs={'cols': '25',
                                                                'rows': '3'}),
                               required=False,
                               initial="Welcome to CRITs!",
                               label="CRITS Message",
                               help_text="Message to user on the Login page")
    crits_email = forms.CharField(widget=forms.TextInput,
                                  required=True,
                                  label="CRITs Email",
                                  help_text='*Requires a web server restart.')
    crits_email_subject_tag = forms.CharField(widget=forms.TextInput,
                                  required=False,
                                  label="Text to tag on to every Email's subject line",
                                  help_text='*Requires a web server restart.')
    crits_email_end_tag = forms.BooleanField(initial=True,
                               required=False,
                               label="Tag on the end (default=True) or the beginning",
                               help_text='*Requires a web server restart.')
    crits_version = forms.CharField(widget=forms.TextInput,
                                    required=True,
                                    initial=settings.CRITS_VERSION,
                                    label="DB Version")
    git_repo_url = forms.CharField(widget=forms.TextInput,
                                   required=False,
                                   initial=settings.CRITS_VERSION,
                                   label="Git Repo URL")
    instance_name = forms.CharField(widget=forms.TextInput, required=True)
    instance_url = forms.CharField(widget=forms.TextInput, required=True)
    def __init__(self, *args, **kwargs):
        super(ConfigCritsForm, self).__init__(*args, **kwargs)
        self.fields['crits_version'].widget.attrs['readonly'] = True


