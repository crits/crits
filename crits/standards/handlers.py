import logging

from crits.standards.parsers import STIXParser, STIXParserException

logger = logging.getLogger(__name__)


def import_standards_doc(data, analyst, method, ref=None, make_event=False,
                         source=None):
    """
    Import a standards document into CRITs.

    :param data: The document data to feed into
                 :class:`crits.standards.parsers.STIXParser`
    :type data: str
    :param analyst: The user importing the document.
    :type analyst: str
    :param method: The method of acquiring this document.
    :type method: str
    :param ref: The reference to this document.
    :type ref: str
    :param make_event: Whether or not we should make an Event for this document.
    :type make_event: bool
    :param source: The name of the source who provided this document.
    :type source: str
    :returns: dict with keys:
              "success" (boolean),
              "reason" (str),
              "imported" (list),
              "failed" (list)
    """

    ret = {
            'success': False,
            'reason': '',
            'imported': [],
            'failed': []
          }

    try:
        parser = STIXParser(data, analyst, method)
        parser.parse_stix(reference=ref, make_event=make_event, source=source)
        parser.relate_objects()
    except STIXParserException, e:
        logger.exception(e)
        ret['reason'] = str(e.message)
        return ret
    except Exception, e:
        logger.exception(e)
        ret['reason'] = str(e)
        return ret

    ret['imported'] = parser.imported
    ret['failed'] = parser.failed
    ret['success'] = True
    return ret
