from __future__ import print_function
from __future__ import unicode_literals
from django.utils.crypto import get_random_string as grs

print(grs(50, 'abcdefghijklmnopqrstuvwxyz0123456789!@#%^&*(-_=+)'))
