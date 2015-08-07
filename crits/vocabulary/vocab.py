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

        l = []
        for k,v in cls.__dict__.iteritems():
            if ('__' not in k and
                isinstance(v, basestring) and
                '__' not in v and
                'vocabulary' not in v):
                l.append(v)
        if sort:
            l.sort()
        return l
