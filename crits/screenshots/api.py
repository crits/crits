from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
from crits.objects.object_type import ObjectType
from crits.objects.handlers import add_object


class ObjectResource(CRITsAPIResource):
    """
    Class to handle everything related to the Objects API.

    Currently supports POST.
    """

    class Meta:
        queryset = ObjectType.objects.all()
        allowed_methods = ('post')
        resource_name = "objects"
        authentication = MultiAuthentication(CRITsApiKeyAuthentication(),
                                             CRITsSessionAuthentication())
        authorization = authorization.Authorization()
        serializer = CRITsSerializer()

    def get_object_list(self, request):
        """
        Use the CRITsAPIResource to get our objects but provide the class to get
        the objects from.

        :param request: The incoming request.
        :type request: :class:`django.http.HttpRequest`
        :returns: Resulting objects in the specified format (JSON by default).
        """

        return super(ObjectResource, self).get_object_list(request,
                                                           ObjectType,
                                                           False)

    def obj_create(self, bundle, **kwargs):
        """
        Handles adding objects through the API.

        :param bundle: Bundle containing the object to add.
        :type bundle: Tastypie Bundle object.
        :returns: Bundle object.
        :raises BadRequest: If necessary data is not provided or creation fails.

        """
        analyst = bundle.request.user.username
        crits_type = bundle.data.get('crits_type', None)
        crits_id = bundle.data.get('crits_id', None)
        object_type = bundle.data.get('object_type', None)

        if not object_type:
            raise BadRequest("You must provide an Object Type!")

        ot_array = object_type.split(" - ")
        object_type = ot_array[0]
        name = ot_array[1] if len(ot_array) == 2 else ot_array[0]

        source = bundle.data.get('source', None)
        method = bundle.data.get('method', None)
        reference = bundle.data.get('reference', None)
        add_indicator = bundle.data.get('add_indicator', None)
        filedata = bundle.data.get('filedata', None)
        value = bundle.data.get('value', None)

        if not crits_type or not crits_id:
            raise BadRequest("You must provide a top-level object!")
        if not filedata and not value:
            raise BadRequest("You must provide a value or filedata!")


        result = add_object(crits_type,
                            crits_id,
                            object_type,
                            name,
                            source,
                            method,
                            reference,
                            analyst,
                            value=value,
                            file_=filedata,
                            add_indicator=add_indicator)
        if not result['success']:
            raise BadRequest(result['message'])
        else:
            return bundle
