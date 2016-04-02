from builtins import object
class CRITsBaseScript(object):
    """
    Base class for all CRITs scripts to inherit.
    """

    username = None

    def __init__(self, username=None):
        """
        Initialization of class. Set the username.

        :param username: The user running this script.
        :type username: str
        """

        self.username = username
