import json
import yaml

from bson.objectid import ObjectId
from dateutil.parser import parse
from django.http import HttpResponse
from lxml.etree import tostring

from django.core.urlresolvers import resolve, get_script_prefix

from tastypie.exceptions import BadRequest, ImmediateHttpResponse
from tastypie.serializers import Serializer
from tastypie.authentication import SessionAuthentication, ApiKeyAuthentication
from tastypie.utils.mime import build_content_type
from tastypie_mongoengine.resources import MongoEngineResource

from crits.core.data_tools import format_file, create_zip
from crits.core.handlers import remove_quotes, generate_regex
from crits.core.user_tools import user_sources


# The following leverages code from the Tastypie library.
class CRITsApiKeyAuthentication(ApiKeyAuthentication):
    """
    API Key Authentication Class.
    """

    def is_authenticated(self, request, **kwargs):
        """
        Determine if the user can properly authenticate with the
        username and API key they provided.

        :param request: Django request object (Required)
        :type request: :class:`django.http.HttpRequest`
        :returns: True, :class:`tastypie.http.HttpUnauthorized`
        """

        try:
            username, api_key = self.extract_credentials(request)
        except ValueError:
            return self._unauthorized()

        if not username or not api_key:
            return self._unauthorized()

        try:
            from crits.core.user import CRITsUser
            user = CRITsUser.objects(username=username).first()
        except:
            return self._unauthorized()

        if not user:
            return self._unauthorized()

        if not user.is_active:
            return self._unauthorized()

        key_auth_check = self.get_key(user, api_key)
        if key_auth_check:
            request.user = user
            return True
        else:
            return self._unauthorized()

    def get_key(self, user, api_key):
        """
        Attempts to find the API key for the user. Uses ``ApiKey`` by default
        but can be overridden.

        :param user: The user trying to authenticate.
        :type user: str
        :param api_key: The key the user is trying to authenticate with.
        :type api_key: str
        :returns: True, False
        """

        if user:
            if user.validate_api_key(api_key):
                return True
        return False


class CRITsSessionAuthentication(SessionAuthentication):
    """
    API Authentication leveraging an existing Django browser session.
    """

    def get_identifier(self, request):
        """
        Returns the username as the identifier.

        :param request: Django request object (Required)
        :type request: :class:`django.http.HttpRequest`
        :returns: str
        """

        return request.user.username


class CRITsSerializer(Serializer):
    """
    Custom serializer for CRITs.
    """

    formats = ['json', 'xml', 'yaml', 'file']
    content_types = {
        'json': 'application/json',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'file': 'application/octet-stream',
    }

    def _format_data(self, filedata, file_format=None):
        """
        Format filedata based on request.

        :param filedata: The filedata to format.
        :type filedata: str
        :param file_format: The format the file should be in:
                            "base64", "zlib", "raw", "invert".
        :type file_format: str
        :returns: list of [<formatted data>, <file extension>]
        """

        if file_format not in ('base64', 'zlib', 'raw', 'invert'):
            file_format = 'raw'
        return format_file(filedata, file_format)[0]

    def to_file(self, data, options=None):
        """
        Respond with filedata instead of metadata.

        :param data: The data to be worked on.
        :type data: dict for multiple objects,
                    :class:`tastypie.bundle.Bundle` for a single object.
        :param options: Options to alter how this serializer works.
        :type options: dict
        :returns: :class:`django.http.HttpResponse`,
                  :class:`tastypie.exceptions.BadRequest`
        """

        get_file = options.get('file', None)
        file_format = options.get('file_format', 'raw')
        response = None
        zipfile = None

        if get_file:
            files = []
            if hasattr(data, 'obj'):
                if hasattr(data.obj, 'filedata'):
                    filename = data.obj.md5
                    filedata = data.obj.filedata.read()
                    if filedata:
                        filedata = self._format_data(filedata, file_format)
                        files.append([filename, filedata])
                elif hasattr(data.obj, 'screenshot'):
                    filename = "%s.png" % data.obj.md5
                    filedata = data.obj.screenshot.read()
                    if filedata:
                        files.append([filename, filedata])
            elif 'objects' in data:
                try:
                    objs = data['objects']
                    for obj_ in objs:
                        if hasattr(obj_.obj, 'filedata'):
                            filename = obj_.obj.md5
                            filedata = obj_.obj.filedata.read()
                            if filedata:
                                filedata = self._format_data(filedata,
                                                             file_format)
                                files.append([filename, filedata])
                        elif hasattr(obj_.obj, 'screenshot'):
                            filename = "%s.png" % data.obj.md5
                            filedata = data.obj.screenshot.read()
                            if filedata:
                                files.append([filename, filedata])
                except:
                    pass
            try:
                if len(files):
                    zipfile = create_zip(files)
                    response =  HttpResponse(zipfile,
                                                content_type="application/octet-stream; charset=utf-8")
                    response['Content-Disposition'] = 'attachment; filename="results.zip"'
                else:
                    response = BadRequest("No files found!")
            except Exception, e:
                response = BadRequest(str(e))
        return response

    def to_json(self, data, options=None):
        """
        Respond with JSON formatted data. This is the default.

        :param data: The data to be worked on.
        :type data: dict for multiple objects,
                    :class:`tastypie.bundle.Bundle` for a single object.
        :param options: Options to alter how this serializer works.
        :type options: dict
        :returns: str
        """

        options = options or {}
        username = options.get('username', None)

        # if this is a singular object, just return our internal to_json()
        # which handles the Embedded MongoEngine classes.
        if hasattr(data, 'obj'):
            if data.obj._has_method('sanitize'):
                data.obj.sanitize(username=username, rels=True)
            return data.obj.to_json()

        data = self._convert_mongoengine(data, options)
        return json.dumps(data, sort_keys=True)

    def to_xml(self, data, options=None):
        """
        Respond with XML formatted data.

        :param data: The data to be worked on.
        :type data: dict for multiple objects,
                    :class:`tastypie.bundle.Bundle` for a single object.
        :param options: Options to alter how this serializer works.
        :type options: dict
        :returns: str
        """

        options = options or {}

        if hasattr(data, 'obj'):
            data = {'objects': [data]}

        data = self._convert_mongoengine(data, options)
        return tostring(self.to_etree(data, options), xml_declaration=True,
                        encoding='utf-8')

    def to_yaml(self, data, options=None):
        """
        Respond with YAML formatted data.

        :param data: The data to be worked on.
        :type data: dict for multiple objects,
                    :class:`tastypie.bundle.Bundle` for a single object.
        :param options: Options to alter how this serializer works.
        :type options: dict
        :returns: str
        """

        options = options or {}
        username = options.get('username', None)

        # if this is a singular object, just return our internal to_yaml()
        # which handles the Embedded MongoEngine classes.
        if hasattr(data, 'obj'):
            if data.obj._has_method('sanitize'):
                data.obj.sanitize(username=username, rels=True)
            return data.obj.to_yaml()

        data = self._convert_mongoengine(data, options)
        return yaml.dump(data)

    def _convert_mongoengine(self, data, options=None):
        """
        Convert the MongoEngine class to a serializable object.
        This also sanitizes the content.

        :param data: The data to be worked on.
        :type data: dict for multiple objects,
                    :class:`tastypie.bundle.Bundle` for a single object.
        :param options: Options to alter how this serializer works.
        :type options: dict
        :returns: dict
        """

        # if this is a list of multiple objects, use our internal to_json()
        # for each one before processing normally.
        username = options.get('username', None)
        if 'objects' in data:
            objs = data['objects']
            data['objects'] = []
            for obj_ in objs:
                if obj_.obj._has_method('sanitize'):
                    obj_.obj.sanitize(username=username, rels=True)
                data['objects'].append(json.loads(obj_.obj.to_json()))
        data = self.to_simple(data, options)
        return data


class CRITsAPIResource(MongoEngineResource):
    """
    Standard CRITs API Resource.
    """

    class Meta:
        default_format = "application/json"

    def crits_response(self, content, status=200):
        """
        An amazing hack so we can return our own custom JSON response. Instead
        of having the ability to craft and return an HttpResponse, Tastypie
        requires us to raise this custom exception in order to do so.

        The content should be a dict with keys of:

            - return_code: 0 (success), 1 (failure), etc. for custom returns.
            - type: The CRITs TLO type (Sample, Email, etc.)
            - id: The ObjectId (as a string) of the TLO. (optional if not
                  available)
            - message: A custom message you wish to return.

        If you wish to extend your content to contain more k/v pairs you can do
        so as long as they are JSON serializable.

        :param content: The information we wish to return in the response.
        :type content: dict (must be json serializable)
        :param status: If we wish to return anything other than a 200.
        :type status: int
        :raises: :class:`tastypie.exceptions.ImmediateHttpResponse`
        """

        raise ImmediateHttpResponse(HttpResponse(json.dumps(content),
                                                 content_type="application/json",
                                                 status=status))

    def create_response(self, request, data, response_class=HttpResponse,
                        **response_kwargs):
        """
        Override the default create_response so we can pass the GET
        parameters into options. This allows us to use GET parameters
        to adjust how our serializers respond.

        :param request: Django request object (Required)
        :type request: :class:`django.http.HttpRequest`
        :param data: The data to be worked on.
        :type data: dict for multiple objects,
                    :class:`tastypie.bundle.Bundle` for a single object.
        :param response_class: The class to utilize for the response.
        :type response_class: :class:`django.http.HttpResponse` (Default)
        :returns: :class:`django.http.HttpResponse` (Default)
        """

        desired_format = self.determine_format(request)
        options = request.GET.copy()
        options['username'] = request.user.username
        serialized = self.serialize(request, data, desired_format,
                                    options=options)
        return response_class(content=serialized,
                            content_type=build_content_type(desired_format),
                            **response_kwargs)

    def determine_format(self, request):
        """
        Used to determine the desired format.

        :param request: Django request object (Required)
        :type request: :class:`django.http.HttpRequest`
        :returns: str
        """

        return determine_format(request, self._meta.serializer,
                                default_format=self._meta.default_format)

    def deserialize(self, request, data, format=None):
        """
        Custom deserializer which is only used to collect filedata uploads
        and pass the binary along with the rest of the POST like
        tastyie would normally do.

        :param request: Django request object (Required)
        :type request: :class:`django.http.HttpRequest`
        :param data: The data to pass along.
        :type data: dict
        :param format: The format of the request.
        :type format: str
        :returns: data in requested format.
        """

        # Get format from request. Assume json if nothing provided
        if not format:
            format = request.META.get('CONTENT_TYPE', 'application/json')
        if format == 'application/x-www-form-urlencoded':
            if 'filedata' in request.POST:
                raise BadRequest("Filedata only supported in multipart forms.")
            else:
                return request.POST
        # If a file was uploaded, add it to data and pass it along
        if format.startswith('multipart'):
            data = request.POST.copy()
            if 'filedata' in request.FILES:
                if hasattr(request.FILES['filedata'], 'read'):
                    data.update(request.FILES)
                else:
                    raise BadRequest("Expected filehandle, got string.")
            return data
        return super(CRITsAPIResource, self).deserialize(request, data, format)

    def get_object_list(self, request, klass, sources=True):
        """
        Handle GET requests. This does all sorts of work to ensure the
        results are sanitized and that source restriction is adhered to.
        Adds the ability to limit results and the content of the results
        through GET parameters.

        :param request: Django request object (Required)
        :type request: :class:`django.http.HttpRequest`
        :param klass: The CRITs top-level object to get.
        :type klass: class which inherits from
                     :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        :param sources: If we should limit by source.
        :type sources: boolean
        :returns: :class:`crits.core.crits_mongoengine.CritsQuerySet`
        """

        querydict = {}
        get_params = request.GET.copy()
        regex = request.GET.get('regex', False)
        only = request.GET.get('only', None)
        exclude = request.GET.get('exclude', None)
        source_list = user_sources(request.user.username)
        no_sources = True
        # Chop off trailing slash and split on remaining slashes.
        # If last part of path is not the resource name, assume it is an
        # object ID.
        path = request.path[:-1].split('/')
        if path[-1] != self.Meta.resource_name:
            # If this is a valid object ID, convert it. Otherwise, use
            # the string. The corresponding query will return 0.
            if ObjectId.is_valid(path[-1]):
                querydict['_id'] = ObjectId(path[-1])
            else:
                querydict['_id'] = path[-1]

        do_or = False
        for k,v in get_params.iteritems():
            v = v.strip()
            try:
                v_int = int(v)
            except:
                # If can't be converted to an int use the string.
                v_int = v
            if k == "c-_id":
                try:
                    querydict['_id'] = ObjectId(v)
                except:
                    pass
            if k.startswith("c-"):
                field = k[2:]
                # Attempt to discover query operators. We use django-style operators
                # (same as MongoEngine). These also override regex.
                try:
                    op_index = field.index("__")
                    op = "$%s" % field[op_index+2:]
                    field = field[:op_index]
                except ValueError:
                    op_index = None
                if op_index is not None:
                    if op in ('$gt', '$gte', '$lt', '$lte', '$ne', '$in', '$nin', '$exists'):
                        val = v
                        if field in ('created', 'modified'):
                            try:
                                val = parse(val, fuzzy=True)
                            except:
                                pass
                        if op in ('$in', '$nin'):
                            if field == 'source.name':
                                val = []
                                for i in v.split(','):
                                    s = remove_quotes(i)
                                    if s in source_list:
                                        no_sources = False
                                        val.append(s)
                            else:
                                val = [remove_quotes(i) for i in v.split(',')]
                        if op == '$exists':
                            if val in ('true', 'True', '1'):
                                val = 1
                            elif val in ('false', 'False', '0'):
                                val = 0
                        if field in ('size', 'schema_version'):
                            if isinstance(val, list):
                                v_f = []
                                for i in val:
                                    try:
                                        v_f.append(int(i))
                                    except:
                                        pass
                                val = v_f
                            else:
                                try:
                                    val = int(val)
                                except:
                                    val = None
                        if val or val == 0:
                            querydict[field] = {op: val}
                elif field in ('size', 'schema_version'):
                    querydict[field] = v_int
                elif field in ('created', 'modified'):
                    try:
                        querydict[field] = parse(v, fuzzy=True)
                    except:
                        querydict[field] = v
                elif field == 'source.name':
                    v = remove_quotes(v)
                    if v in source_list:
                        no_sources = False
                        querydict[field] = v
                elif regex:
                    querydict[field] = generate_regex(v)
                else:
                    querydict[field] = remove_quotes(v)
            if k == 'or':
                do_or = True
        if do_or:
            tmp = {}
            tmp['$or'] = [{x:y} for x,y in querydict.iteritems()]
            querydict = tmp
        if no_sources and sources:
            querydict['source.name'] = {'$in': source_list}
        if only or exclude:
            required = [k for k,f in klass._fields.iteritems() if f.required]
        if only:
            fields = only.split(',')
            if exclude:
                excludes = exclude.split(',')
                fields = [x for x in fields if x not in excludes]
            for r in required:
                if r not in fields:
                    fields.append(r)
            results = klass.objects(__raw__=querydict).only(*fields)
        elif exclude:
            fields = exclude.split(',')
            for r in required:
                if r not in fields:
                    fields.append(r)
            results = klass.objects(__raw__=querydict).exclude(*fields)
        else:
            results = klass.objects(__raw__=querydict)
        return results

    def obj_get_list(self, bundle, **kwargs):
        """
        Placeholder for overriding the default tastypie function in the future.
        """

        return super(CRITsAPIResource, self).obj_get_list(bundle=bundle, **kwargs)

    def obj_get(self, bundle, **kwargs):
        """
        Placeholder for overriding the default tastypie function in the future.
        """

        return super(CRITsAPIResource, self).obj_get(bundle=bundle, **kwargs)

    def obj_create(self, bundle, **kwargs):
        """
        Create an object in CRITs. Should be overridden by each
        individual top-level resource.

        :returns: NotImplementedError if the resource doesn't override.
        """

        raise NotImplementedError('You cannot currently create this objects through the API.')

    def obj_update(self, bundle, **kwargs):
        """
        Update an object in CRITs. Should be overridden by each
        individual top-level resource.

        :returns: NotImplementedError if the resource doesn't override.
        """

        import crits.actors.handlers as ah
        import crits.core.handlers as coreh
        import crits.objects.handlers as objh
        import crits.relationships.handlers as relh
        import crits.services.handlers as servh
        import crits.signatures.handlers as sigh
        import crits.indicators.handlers as indh

        actions = {
            'Common': {
                'add_object': objh.add_object,
                'add_releasability': coreh.add_releasability,
                'forge_relationship': relh.forge_relationship,
                'run_service': servh.run_service,
                'status_update' : coreh.status_update,
                'ticket_add' : coreh.ticket_add,
                'ticket_update' : coreh.ticket_update,
                'ticket_remove' : coreh.ticket_remove,
                'source_add_update': coreh.source_add_update,
                'source_remove': coreh.source_remove,
                'action_add' : coreh.action_add,
                'action_update' : coreh.action_update,
                'action_remove' : coreh.action_remove,
                'description_update' : coreh.description_update,
            },
            'Actor': {
                'update_actor_tags': ah.update_actor_tags,
                'attribute_actor_identifier': ah.attribute_actor_identifier,
                'set_identifier_confidence': ah.set_identifier_confidence,
                'remove_attribution': ah.remove_attribution,
                'set_actor_name': ah.set_actor_name,
                'update_actor_aliases': ah.update_actor_aliases,
            },
            'Backdoor': {},
            'Campaign': {},
            'Certificate': {},
            'Domain': {},
            'Email': {},
            'Event': {},
            'Exploit': {},
            'Indicator': {
                'modify_attack_types' : indh.modify_attack_types,
                'modify_threat_types' : indh.modify_threat_types,
                'activity_add' : indh.activity_add,
                'activity_update' : indh.activity_update,
                'activity_remove' : indh.activity_remove,
                'ci_update' : indh.ci_update
                          },
            'IP': {},
            'PCAP': {},
            'RawData': {},
            'Sample': {},
            'Signature': {
                'update_dependency': sigh.update_dependency,
                'update_min_version': sigh.update_min_version,
                'update_max_version': sigh.update_max_version,
                'update_signature_data': sigh.update_signature_data,
                'update_signature_type': sigh.update_signature_type,
                'update_title': sigh.update_title
            },
            'Target': {},
        }

        prefix = get_script_prefix()
        uri = bundle.request.path
        if prefix and uri.startswith(prefix):
            uri = uri[len(prefix)-1:]
        view, args, kwargs = resolve(uri)

        type_ = kwargs['resource_name'].title()
        if type_ == "Raw_Data":
            type_ = "RawData"
        if type_[-1] == 's':
            type_ = type_[:-1]
        if type_ in ("Pcap", "Ip"):
            type_ = type_.upper()
        id_ = kwargs['pk']

        content = {'return_code': 0,
                   'type': type_,
                   'message': '',
                   'id': id_}

        # Make sure we have an appropriate action.
        action = bundle.data.get("action", None)
        atype = actions.get(type_, None)
        if atype is None:
            content['return_code'] = 1
            content['message'] = "'%s' is not a valid resource." % type_
            self.crits_response(content)
        action_type = atype.get(action, None)
        if action_type is None:
            atype = actions.get('Common')
            action_type = atype.get(action, None)
        if action_type:
            data = bundle.data
            # Requests don't need to have an id_ as we will derive it from
            # the request URL. Override id_ if the request provided one.
            data['id_'] = id_
            # Override type (if provided)
            data['type_'] = type_
            # Override user (if provided) with the one who made the request.
            data['user'] = bundle.request.user.username
            try:
                results = action_type(**data)
                if not results.get('success', False):
                    content['return_code'] = 1
                    # TODO: Some messages contain HTML and other such content
                    # that we shouldn't be returning here.
                    message = results.get('message', None)
                    content['message'] = message
                else:
                    content['message'] = "success!"
            except Exception, e:
                content['return_code'] = 1
                content['message'] = str(e)
        else:
            content['return_code'] = 1
            content['message'] = "'%s' is not a valid action." % action
        self.crits_response(content)

    def obj_delete_list(self, bundle, **kwargs):
        """
        Delete list of objects in CRITs. Should be overridden by each
        individual top-level resource.

        :returns: NotImplementedError if the resource doesn't override.
        """

        raise NotImplementedError('You cannot currently delete objects through the API.')

    def obj_delete(self, bundle, **kwargs):
        """
        Delete an object in CRITs. Should be overridden by each
        individual top-level resource.

        :returns: NotImplementedError if the resource doesn't override.
        """

        raise NotImplementedError('You cannot currently delete this object through the API.')

    def resource_name_from_type(self, crits_type):
        """
        Take a CRITs type and convert it to the appropriate API resource name.

        :param crits_type: The CRITs type.
        :type crits_type: str
        :returns: str
        """

        if crits_type == "RawData":
            return "raw_data"
        else:
            return "%ss" % crits_type.lower()


def determine_format(request, serializer, default_format='application/json'):
    """
    This overrides the default tastyie determine_format.
    This is done because we want to default to "application/json"
    even though most browsers will send along "application/xml" in the
    Accept header if no "format" is provided.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param serializer: The serializer being used.
    :type serializer: :class:`crits.core.api.CRITsSerializer`
    :param default_format: The format to respond in.
    :type default_format: str
    :returns: str
    """

    # First, check if they forced the format.
    if request.GET.get('format'):
        if request.GET['format'] in serializer.formats:
            return serializer.get_mime_for_format(request.GET['format'])

    if request.GET.get('file'):
        default_format = 'application/octet-stream'

    # No valid 'Accept' header/formats. Sane default.
    return default_format


class MongoObject(object):
    """Class that represents a Mongo-like object"""
    def __init__(self, initial=None):
        self.__dict__['_data'] = {}

        if hasattr(initial, 'items'):
            self.__dict__['_data'] = initial

    def __getattr__(self, name):
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        self.__dict__['_data'][name] = value

    def to_dict(self):
        return self._data
