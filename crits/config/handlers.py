from django.conf import settings

from crits.config.config import CRITsConfig

def modify_configuration(forms, analyst):
    """
    Modify the configuration with the submitted changes.

    :param config_form: The form data.
    :type config_form: dict
    :param analyst: The user making the modifications.
    :type analyst: str
    :returns: dict with key "message"
    """

    config = CRITsConfig.objects().first()
    if not config:
        config = CRITsConfig()

    data = None
    for form in forms:
        if not data:
            data = form.cleaned_data
        else:
            data.update(form.cleaned_data)

   # data = config_form.cleaned_data
    allowed_hosts_list = data['allowed_hosts'].split(',')
    allowed_hosts = ()
    for allowed_host in allowed_hosts_list:
        allowed_hosts = allowed_hosts + (allowed_host.strip(),)
    data['allowed_hosts'] = allowed_hosts
    service_dirs_list = data['service_dirs'].split(',')
    service_dirs = ()
    for service_dir in service_dirs_list:
        service_dirs = service_dirs + (service_dir.strip(),)
    data['service_dirs'] = service_dirs
    config.merge(data, overwrite=True)
    try:
        config.save(username=analyst)
        return {'message': "Success!"}
    except Exception, e:
        return {'message': "Failure: %s" % e}
