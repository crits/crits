class CRITsBaseScript(object):
    """
    Base class for all CRITs scripts to inherit.
    """

    user = None

    def __init__(self, user=None):
        """
        Initialization of class. Set the username.

        :param username: The user running this script.
        :type username: str
        """

        self.user = user
