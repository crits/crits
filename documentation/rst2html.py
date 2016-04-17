#!/usr/bin/env python

"""
This requires the python docutils library.
"""
from __future__ import unicode_literals

from docutils.core import publish_cmdline

publish_cmdline(writer_name='html')
