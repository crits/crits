import hashlib


class AnalysisContext(object):
    """
    Contains information about the target of analysis.
    """

    def __init__(self, crits_type):
        """
        """
        self.crits_type = crits_type

    def __str__(self):
        return "%s %s" % (self.crits_type, self.identifier)

    @property
    def identifier(self):
        """
        A way to uniquely identify this item.

        Between `self.crits_type` and `self.identifier`, this item should
        be uniquely identifiable.

        AnalysisContext subclasses MUST override this property.
        """
        raise NotImplementedError()


class SampleContext(AnalysisContext):
    """
    Sample service context.
    """

    def __init__(self, username=None, data=None, md5_digest=None, sample_dict=None):
        """
        Generate the sample context.

        :param username: The user creating the context.
        :type username: str
        :param data: The sample data.
        :type data: str
        :param md5_digest: The sample MD5.
        :type md5_digest: str
        :param sample_dict: The sample metadata.
        :type sample_dict: dict
        """

        super(SampleContext, self).__init__('Sample')

        self.username = username

        if not data and not md5_digest:
            raise ValueError("Either data or md5 digest required")

        self.data = data

        if data and (not md5_digest or len(md5_digest) != 32):
            self.md5 = hashlib.md5(self.data).hexdigest()
        else:
            self.md5 = md5_digest

        if sample_dict:
            self.filename = sample_dict.get('filename')
            self.filetype = sample_dict.get('filetype')
            self.mimetype = sample_dict.get('mimetype')

        # Keep sample_dict around
        self.sample_dict = sample_dict

    def has_data(self):
        """
        Do we have sample data.
        """

        return bool(self.data)

    def is_pe(self):
        """
        Is this a PE file.
        """

        return self.has_data() and self.data[:2] == "MZ"

    def is_pdf(self):
        """
        Is this a PDF.
        """

        return self.has_data() and "%PDF-" in self.data[:1024]

    @property
    def identifier(self):
        """
        Return the identifier (MD5).
        """

        return self.md5

    @property
    def url_arg(self):
        """
        Return the URL argument (MD5).
        """

        return self.md5


class PCAPContext(AnalysisContext):
    """
    PCAP service context.
    """

    def __init__(self, username=None, data=None, md5_digest=None, pcap_dict=None):
        """
        Generate the PCAP context.

        :param username: The user creating the context.
        :type username: str
        :param data: The PCAP data.
        :type data: str
        :param md5_digest: The PCAP MD5.
        :type md5_digest: str
        :param pcap_dict: The PCAP metadata.
        :type pcap_dict: dict
        """

        super(PCAPContext, self).__init__('PCAP')

        self.username = username

        if not data:
            raise ValueError("PCAP data required")

        self.data = data

        if not md5_digest or len(md5_digest) != 32:
            self.md5 = hashlib.md5(self.data).hexdigest()
        else:
            self.md5 = md5_digest

        self.pcap_dict = pcap_dict

    @property
    def identifier(self):
        """
        Return the identifier (MD5).
        """

        return self.md5

    @property
    def url_arg(self):
        """
        Return the URL argument (MD5).
        """

        return self.md5


class CertificateContext(AnalysisContext):
    """
    Certificate service context.
    """

    def __init__(self, username=None, data=None, md5_digest=None, cert_dict=None):
        """
        Generate the Certificate context.

        :param username: The user creating the context.
        :type username: str
        :param data: The Certificate data.
        :type data: str
        :param md5_digest: The Certificate MD5.
        :type md5_digest: str
        :param cert_dict: The Certificate metadata.
        :type cert_dict: dict
        """

        super(CertificateContext, self).__init__('Certificate')

        self.username = username

        if not data:
            raise ValueError("Certificate data required")

        self.data = data

        if not md5_digest or len(md5_digest) != 32:
            self.md5 = hashlib.md5(self.data).hexdigest()
        else:
            self.md5 = md5_digest

        self.certificate_dict = cert_dict

    @property
    def identifier(self):
        """
        Return the identifier (MD5).
        """

        return self.md5

    @property
    def url_arg(self):
        """
        Return the URL argument (MD5).
        """

        return self.md5


class RawDataContext(AnalysisContext):
    """
    RawData service context.
    """

    def __init__(self, username=None, _id=None, raw_data_dict=None):
        """
        Generate the RawData context.

        :param username: The user creating the context.
        :type username: str
        :param _id: The RawData ObjectId.
        :type _id: str
        :param raw_data_dict: The RawData metadata.
        :type raw_data_dict: dict
        """

        super(RawDataContext, self).__init__('RawData')

        self.username = username

        if not _id:
            raise ValueError("RawData id required.")
        else:
            self._id = _id

        self.data = 'None'
        self.raw_data_dict = raw_data_dict

    @property
    def identifier(self):
        """
        Return the identifier (ObjectId).
        """

        return self._id

    @property
    def url_arg(self):
        """
        Return the URL argument (ObjectId).
        """

        return self._id

class EventContext(AnalysisContext):
    """
    Event service context.
    """

    def __init__(self, username=None, _id=None, event_dict=None):
        """
        Generate the Event context.

        :param username: The user creating the context.
        :type username: str
        :param _id: The Event ObjectId.
        :type _id: str
        :param event_dict: The Event metadata.
        :type event_dict: dict
        """

        super(EventContext, self).__init__('Event')

        self.username = username

        if not _id:
            raise ValueError("Event id required.")
        else:
            self._id = _id

        self.data = None
        self.event_dict = event_dict

    @property
    def identifier(self):
        """
        Return the identifier (ObjectId)
        """

        return self._id

    @property
    def url_arg(self):
        """
        Return the URL argument (ObjectId)
        """

        return self._id

class IndicatorContext(AnalysisContext):
    """
    Indicator service context.
    """

    def __init__(self, username=None, _id=None, indicator_dict=None):
        """
        Generate the Indicator context.

        :param username: The user creating the context.
        :type username: str
        :param _id: The Indicator ObjectId.
        :type _id: str
        :param indicator_dict: The Indicator metadata.
        :type indicator_dict: dict
        """

        super(IndicatorContext, self).__init__('Indicator')

        self.username = username

        if not _id:
            raise ValueError("Indicator id required.")
        else:
            self._id = _id

        self.data = None
        self.indicator_dict = indicator_dict

    @property
    def identifier(self):
        """
        Return the identifier (ObjectId)
        """

        return self._id

    @property
    def url_arg(self):
        """
        Return the URL argument (ObjectId)
        """

        return self._id

class DomainContext(AnalysisContext):
    """
    Domain service context.
    """

    def __init__(self, username=None, _id=None, domain_dict=None):
        """
        Generate the Domain context.

        :param username: The user creating the context.
        :type username: str
        :param _id: The Domain ObjectId.
        :type _id: str
        :param domain_dict: The Domain metadata.
        :type domain_dict: dict
        """

        super(DomainContext, self).__init__('Domain')

        self.username = username

        if not _id:
            raise ValueError("Domain id required.")
        else:
            self._id = _id

        self.domain_dict = domain_dict

    @property
    def identifier(self):
        """
        Return the identifier (ObjectId)
        """

        return self._id

    @property
    def url_arg(self):
        """
        Return the URL argument (ObjectId)
        """

        return self._id

class IPContext(AnalysisContext):
    """
    IP service context.
    """

    def __init__(self, username=None, _id=None, ip_dict=None):
        """
        Generate the IP context.

        :param username: The user creating the context.
        :type username: str
        :param _id: The IP ObjectId.
        :type _id: str
        :param ip_dict: The IP metadata.
        :type ip_dict: dict
        """

        super(IPContext, self).__init__('IP')

        self.username = username

        if not _id:
            raise ValueError("IP id required.")
        else:
            self._id = _id

        self.ip_dict = ip_dict

    @property
    def identifier(self):
        """
        Return the identifier (ObjectId)
        """

        return self._id

    @property
    def url_arg(self):
        """
        Return the URL argument (ObjectId)
        """

        return self._id
