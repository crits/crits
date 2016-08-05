from tastypie import authorization, fields, http
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import ImmediateHttpResponse

from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsAPIResource, MongoObject
from crits.vocabulary.actors import ThreatTypes, Motivations
from crits.vocabulary.actors import Sophistications, IntendedEffects
from crits.vocabulary.confidence import Confidence
from crits.vocabulary.events import EventTypes
from crits.vocabulary.indicators import IndicatorTypes, IndicatorThreatTypes
from crits.vocabulary.indicators import IndicatorAttackTypes, IndicatorCI
from crits.vocabulary.ips import IPTypes
from crits.vocabulary.kill_chain import KillChain
from crits.vocabulary.objects import ObjectTypes
from crits.vocabulary.relationships import RelationshipTypes
from crits.vocabulary.sectors import Sectors
from crits.vocabulary.status import Status

class VocabResource(CRITsAPIResource):
    """
    Class to handle everything related to the Vocabulary API.

    Currently supports GET.
    """

    category = fields.CharField(attribute="category")
    values = fields.ListField(attribute="values")

    class Meta:
        allowed_methods = ('get')
        resource_name = "vocab"
        authentication = MultiAuthentication(CRITsApiKeyAuthentication(),
                                             CRITsSessionAuthentication())
        authorization = authorization.Authorization()

    def obj_get_list(self, bundle=None, **kwargs):
        output = []
        vocab_classes = (ThreatTypes, Motivations, Sophistications,
                         IntendedEffects, Confidence, EventTypes,
                         IndicatorTypes, IndicatorThreatTypes,
                         IndicatorAttackTypes, IndicatorCI, IPTypes, KillChain,
                         ObjectTypes, RelationshipTypes, Sectors, Status)
        for class_ in vocab_classes:
            values = class_.values(sort=True)
            output.append(MongoObject(initial={'category': class_.__name__,
                                               'values': values}))
        return output

    def obj_get(self, bundle=None, **kwargs):
        category = kwargs['pk']
        try:
            class_ = globals()[category]
        except:
            msg = 'Vocabulary category "%s" does not exist' % category
            raise ImmediateHttpResponse(response=http.HttpBadRequest(msg))

        values = class_.values(sort=True)
        return MongoObject(initial={'category': category, 'values': values})
