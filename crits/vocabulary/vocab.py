class vocab(object):
    """
    Base CRITs vocabulary object. Does nothing right now.
    """

    @classmethod
    def values(cls, sort=False):
        """
        Get available values in a list.

        :param sort: Should the list be sorted.
        :type sort: bool
        :returns: list
        """

        l = [i for i in cls.__dict__.values() if i is not None and '__' not in i
             and 'vocabulary' not in i]
        if sort:
            l.sort()
        return l
