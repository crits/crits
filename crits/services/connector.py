class UnknownConnector(Exception):
    """
    Exception for dealing with an unknown connector type.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class MissingDependency(Exception):
    """
    Exception for dealing with a missing dependency.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class MissingConfiguration(Exception):
    """
    Exception for dealing with a missing configuration for a connector.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class Connector(object):
    """
    Service connector to help with distributed services.
    """

    # list of supported connectors
    connectors = ['amqp']
    connection = None

    def __init__(self, connector=None, *args, **kwargs):
        """
        Setup connector if supplied. **kwargs will be passed along as additional
        arguments to the connector.

        :param connector: The connector type to make a connection for.
        :type connector: str
        """

        if connector:
            self.connector(connector, args, **kwargs)

    def connector(self, connector=None, *args, **kwargs):
        """
        Setup connector if supplied. **kwargs will be passed along as arguments
        for your connection.

        :param connector: The connector type to make a connection for.
        :type connector: str
        :raises: UnknownConnector
        """

        # If we don't have a connector, or we received an unknown one, raise an
        # Exception.
        if not connector:
            raise UnknownConnector("Need to supply a connector!")
        if connector not in self.connectors:
            raise UnknownConnector("Connector %s is unknown!" % connector)

        # AMQP connection
        if connector == 'amqp':
            if 'uri' not in kwargs:
                raise MissingConfiguration("Need to provide 'uri'!")
            uri = kwargs['uri']
            del kwargs['uri']
            self.connection = self._amqp_connector(uri=uri, **kwargs)
            self.connection.connect()

    def _amqp_connector(self, uri=None, *args, **kwargs):
        """
        AMQP connector. Creates a connection to the AMQP server and returns it.
        Any extra kwargs you wish to pass to Connection() can be passed via
        **kwargs. See Kombu documentation for supported arguments.

        :param uri: The AMQP URI.
        :type uri: str - Ex: amqp://user:pass@host:port//
        :returns: :class:`kombu.Connection`
        """

        try:
            from kombu import Connection
        except:
            raise MissingDependency("Could not find Kombu. Is it installed?")
        if not uri:
            raise MissingConfiguration("Need an AMQP URI to connect to.")
        return Connection(uri, **kwargs)

    def send_msg(self, msg, exch, routing_key):
        if not self.connection:
            raise MissingConfiguration("Missing connection!")

        from kombu import Exchange, Producer
        exch = Exchange(exch, type='topic')
        prod = Producer(self.connection, exchange=exch)
        prod.publish(msg, routing_key=routing_key)

    def release(self):
        """
        Release existing connection.
        """

        self.connection.release()
