import json
import yaml

from bson.objectid import ObjectId
from django.http import HttpResponse
from lxml.etree import tostring

from tastypie.exceptions import BadRequest
from tastypie.serializers import Serializer
from tastypie.authentication import SessionAuthentication, ApiKeyAuthentication
from tastypie.utils.mime import build_content_type
from tastypie_mongoengine.resources import MongoEngineResource

from crits.core.data_tools import format_file, create_zip
from crits.core.handlers import download_object_handler, remove_quotes, generate_regex
from crits.core.source_access import SourceAccess
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

    formats = ['json', 'xml', 'yaml', 'stix', 'file']
    content_types = {
        'json': 'application/json',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'stix': 'application/stix+xml',
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
            elif 'objects' in data:
                try:
                    objs = data['objects']
                    for obj_ in objs:
                        filename = obj_.obj.md5
                        filedata = obj_.obj.filedata.read()
                        if filedata:
                            filedata = self._format_data(filedata, file_format)
                            files.append([filename, filedata])
                except:
                    pass
            try:
                if len(files):
                    zipfile = create_zip(files)
                    response =  HttpResponse(zipfile,
                                                mimetype='application/octet-stream; charset=utf-8')
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
            data.obj.sanitize(username=username, rels=True)
            return data.obj.to_yaml()

        data = self._convert_mongoengine(data, options)
        return yaml.dump(data)

    def to_stix(self, data, options=None):
        """
        Respond with STIX formatted data.

        :param data: The data to be worked on.
        :type data: dict for multiple objects,
                    :class:`tastypie.bundle.Bundle` for a single object.
        :param options: Options to alter how this serializer works.
        :type options: dict
        :returns: str
        """

        options = options or {}
        get_binaries = 'stix_no_bin'
        if 'binaries' in options:
            try:
                if int(options['binaries']):
                    get_binaries = 'stix'
            except:
                pass

        # This is bad.
        # Should probably find a better way to determine the user
        # who is making this API call. However, the data to
        # convert is already queried by the API using the user's
        # source access list, so technically we should not be
        # looping through any data the user isn't supposed to see,
        # so this sources list is just a formality to get
        # download_object_handler() to do what we want.
        sources = [s.name for s in SourceAccess.objects()]

        if hasattr(data, 'obj'):
            objects = [(data.obj._meta['crits_type'],
                       data.obj.id)]
            object_types = [objects[0][0]]
        elif 'objects' in data:
            try:
                objects = []
                object_types = []
                objs = data['objects']
                data['objects'] = []
                for obj_ in objs:
                    objects.append((obj_.obj._meta['crits_type'],
                                    obj_.obj.id))
                    object_types.append(obj_.obj._meta['crits_type'])
            except Exception:
                return ""
        else:
            return ""

        try:
            # Constants are here to make sure:
            # 1: total limit of objects to return
            # 0: depth limit - only want this object
            # 0: relationship limit - don't get relationships
            data = download_object_handler(1,
                                           0,
                                           0,
                                           get_binaries,
                                           'raw',
                                           object_types,
                                           objects,
                                           sources)
        except Exception:
            data = ""
        if 'data' in data:
            data = data['data']
        return data

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
            if hasattr(request.FILES, 'filedata'):
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
        for k,v in get_params.iteritems():
            v = v.strip()
            try:
                v_int = int(v)
            except:
                pass
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
                    if op in ('$gt', '$gte', '$lt', '$lte', '$ne', '$in', '$nin'):
                        val = v
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
                        if val:
                            querydict[field] = {op: val}
                elif field in ('size', 'schema_version'):
                    querydict[field] = v_int
                elif field == 'source.name':
                    v = remove_quotes(v)
                    if v in source_list:
                        no_sources = False
                        querydict[field] = v
                elif regex:
                    querydict[field] = generate_regex(v)
                else:
                    querydict[field] = remove_quotes(v)
        if no_sources and sources:
            querydict['source.name'] = {'$in': source_list}
        if only or exclude:
            required = [k for k,v in klass._fields.iteritems() if v.required]
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

        raise NotImplementedError('You cannot currently update this object through the API.')

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
