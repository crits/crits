import tempfile, shutil
import os
import re
import subprocess
import time
import datetime
import csv
import json, yaml
import string

from bson.objectid import ObjectId
from bson import json_util
from dateutil.parser import parse
from django.conf import settings
from hashlib import md5

from crits.core.class_mapper import class_from_value
from crits.core.exceptions import ZipFileError
from crits.core.mongo_tools import get_file

def get_file_fs(sample_md5):
    """
    Read a file from the filesystem. The path to the file is:

    /data/files/<md5[:2]>/<md5[2:4]>/<md5>

    :param sample_md5: The MD5 of the file to read off of disk.
    :type sample_md5: str
    :returns: str
    """

    try:
        fin = open('/data/files/%s/%s/%s' % (sample_md5[:2],
                                             sample_md5[2:4],
                                             sample_md5),
                   'rb')
        data = fin.read()
        fin.close()
    except:
        raise
    return data

def put_file_fs(data):
    """
    Write a file to the filesystem. The path to write the file to is:

    /data/files/<md5[:2]>/<md5[2:4]>/<md5>

    :param data: The data of the file to write.
    :type data: str
    :returns: str (the md5 of the file written)
    """

    a = md5()
    a.update(data)
    sample_md5 = a.hexdigest()
    try:
        fout = open('/data/files/%s/%s/%s' % (sample_md5[:2],
                                              sample_md5[2:4],
                                              sample_md5),
                    'wb')
        fout.write(data)
        fout.close()
    except:
        raise
    return sample_md5

def create_zip(files, pw_protect=True):
    """
    Create a zip file. Creates a temporary directory to write files to on disk
    using :class:`tempfile`. Uses /usr/bin/zip as the zipping mechanism
    currently. Will password protect the zip file as a default. The password for
    the zip file defaults to "infected", but it can be changed in the config
    under zip7_password.

    :param files: The files to add to the zip file.
    :type files: list of files which are in the format of a list or tuple of
                 (<filename>, <data>).
    :param pw_protect: To password protect the zip file or not.
    :type pw_protect: boolean
    :returns: :class:`crits.core.exceptions.ZipFileError`, str
    """

    dumpdir = ""
    try:
        # Zip can take data from stdin to compress, but
        # you can't define the filenames within the archive,
        # they show up as "-".  Therefore, we need to write
        # out the file, compress it and return the zip.
        # Save the sample as a file in a temp directory
        # NOTE: the following line was causing a "permission denied" exception.
        # Removed dir arg.
        from crits.config.config import CRITsConfig
        crits_config = CRITsConfig.objects().first()
        if crits_config:
            zip7_password = crits_config.zip7_password or 'infected'
        else:
            zip7_password = settings.ZIP7_PASSWORD or 'infected'
        dumpdir = tempfile.mkdtemp() #dir=temproot
        #write out binary files
        for f in files:
            filename = f[0]
            file_data = f[1]

            # make sure our desired path doesn't already exist (some files may
            # have the same name but different data)
            path = dumpdir + "/" + filename.encode("utf-8")
            i = 1
            tmp = path
            while os.path.exists(tmp):
                tmp = path+"("+str(i)+")"
                i += 1

            with open(tmp, "wb") as fh:
                fh.write(file_data)

        # Build the command line for zip
        # NOTE: forking subprocess instead of using Python's ZipFile library
        # because ZipFile does not allow us to create password-protected zip
        # archives, only read them.
        # -j don't include original filepath
        zipname = "zip.zip" #The name we give it doesn't really matter
        args = ["/usr/bin/zip", "-r", "-j", dumpdir+"/"+zipname, dumpdir]
        if pw_protect:
            args += ["-P", zip7_password]
        args += [dumpdir+"/"+zipname, dumpdir]

        proc = subprocess.Popen(args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        # Give the process 30 seconds to complete, otherwise kill it
        waitSeconds = 30
        while (proc.poll() is None and waitSeconds):
            time.sleep(1)
            waitSeconds -= 1

        zipdata = ""
        if proc.returncode:     # zip spit out an error
            errmsg = "Error while creating archive\n" + proc.stdout.read()
            raise ZipFileError, errmsg
        elif not waitSeconds:   # Process timed out
            proc.terminate()
            raise ZipFileError, "Error:\nProcess failed to terminate"
        else:
            with open(dumpdir + "/" + zipname, "rb") as fh:
                zipdata = fh.read()
        if not len(zipdata):
            raise ZipFileError, "Error:\nThe zip archive contains no data"
        return zipdata

    except ZipFileError:
        raise
    except Exception, ex:
        errmsg = ""
        for err in ex.args:
            errmsg = errmsg + " " + unicode(err)
        raise ZipFileError, errmsg
    finally:
        if os.path.isdir(dumpdir):
            shutil.rmtree(dumpdir)

def format_file(data, file_format):
    """
    Format data into the provided format. Acceptable formats are:
        - base64
        - zlib
        - raw
        - invert

    :param data: The data to format.
    :type data: str
    :param file_format: The format to convert the data into.
    :type file_format: str
    :returns: tuple of (<formatted_data>, <file_extension>)
    """

    if data == None:
        return ("", "")

    if file_format == "base64":
        import base64
        data = base64.b64encode(data)
        ext = ".b64"
    elif file_format == "zlib":
        import zlib
        data = zlib.compress(data)
        ext = ".Z"
    elif file_format == "raw":
        ext = ""
    elif file_format == "invert":
        data = ''.join([chr(ord(c) ^ 0xff) for c in data])
        ext = ".ff"
    return (data, ext)

def convert_datetimes_to_string(obj):
    """
    Iterates over all the keys of a document to convert all datetime objects
    to strings.

    Will also work with ordinary datetime objects or lists of datetimes and
    lists of dictionaries. Any non-datetime values will be left as-is.

    :param obj: The date object(s) to convert to a string.
    :type obj: datetime.datetime, list, dict
    :returns: obj
    """

    if isinstance(obj, datetime.datetime):
        return datetime.datetime.strftime(obj, settings.PY_DATETIME_FORMAT)
    elif isinstance(obj, list) or isinstance(obj, dict):
        for idx in (xrange(len(obj)) if isinstance(obj, list) else obj.keys()):
            obj[idx] = convert_datetimes_to_string(obj[idx])

    return obj

def convert_string_to_bool(value):
    """
    Converts the string values "True" or "False" to their boolean
    representation.

    :param value: The string.
    :type value: str.
    :returns: True, False
    """

    if(value != None) and ((value == True) or (value == "True") or (value == "true")):
        return True
    else:
        return False

def format_object(obj_type, obj_id, data_format="yaml", cleanse=True,
                  obj_sources=[], remove_source=False, remove_rels=False,
                  remove_schema_version=False, remove_campaign=False,
                  remove_buckets=False, remove_releasability=False,
                  remove_unsupported=False):
    """
    Formats a top-level object for utilization in certain conditions. Removes
    CRITs-internal necessary data so users editing the document via the
    interface don't alter or have the ability to overwrite things they should
    not.

    :param obj_type: The CRITs type of the top-level object to format.
    :type obj_type: str
    :param obj_id: The ObjectId to search for.
    :type obj_id: str
    :param data_format: The format of the returned data.
    :type data_format: str of "yaml" or "json"
    :param cleanse: Remove "to", "actions", "releasability", and "bucket_list"
                    if this is an Email or Indicator.
    :type cleanse: boolean
    :param obj_sources: The sources to overwrite into the document or to set
                        the source list to an empty list if remove_source is
                        False.
    :type obj_sources: list
    :param remove_source: Remove the source key from the document.
    :type remove_source: boolean
    :param remove_rels: Remove the relationships key from the document.
    :type remove_rels: boolean
    :param remove_schema_version: Remove the schema_version key from the
                                  document.
    :type remove_schema_version: boolean
    :param remove_campaign: Remove the campaign key from the document.
    :type remove_campaign: boolean
    :param remove_buckets: Remove the bucket_list key from the document.
    :type remove_buckets: boolean
    :param remove_releasability: Remove the releasability key from the document.
    :type remove_releasability: boolean
    :param remove_unsupported: Remove the unsupported_attrs key from the document.
    :type remove_unsupported: boolean
    :returns: str
    """

    collection = settings.CRITS_TYPES[obj_type]
    obj_class = class_from_value(obj_type, obj_id)
    if not obj_class:
        return ""

    data = obj_class.to_dict()
    if data is None:
        return ""

    # Emails use raw_header (singular) as the attribute but store it as
    # raw_headers (plural) in the database. When viewing an email in YAML
    # or JSON convert from plural to singular. This will allow a copy/paste
    # of these views to be imported correctly.
    if 'raw_headers' in data:
        data['raw_header'] = data['raw_headers']
        del data['raw_headers']

    if cleanse and collection in [settings.COL_EMAIL, settings.COL_INDICATORS]:
        if "to" in data:
            del data["to"]
        if "actions" in data:
            del data["actions"]
        if "releasability" in data:
            del data["releasability"]
        if "bucket_list" in data:
            del data["bucket_list"]

    if remove_source and 'source' in data:
        del data["source"]
    elif 'source' in data:
        data['source'] = obj_sources

    if remove_rels and 'relationships' in data:
        del data["relationships"]

    if remove_rels and 'objects' in data:
        del data["objects"]

    if remove_schema_version and 'schema_version' in data:
        del data["schema_version"]

    if remove_campaign and 'campaign' in data:
        del data["campaign"]

    del data["_id"]
    if data.has_key("modified"):
        del data["modified"]

    if remove_buckets and 'bucket_list' in data:
        del data['bucket_list']

    if remove_releasability and 'releasability' in data:
        del data['releasability']

    if remove_unsupported and 'unsupported_attrs' in data:
        del data['unsupported_attrs']

    data = json.dumps(convert_datetimes_to_string(data),
                      default=json_util.default)
    if data_format == "yaml":
        data = yaml.dump(yaml.load(data), default_flow_style=False)
    elif data_format == "json":
        data = json.dumps(json.loads(data))

    return data

def make_ascii_strings(md5=None, data=None):
    """
    Find and return all printable ASCII strings in a string.

    :param md5: The MD5 of the Sample to parse.
    :type md5: str
    :param data: The data to parse.
    :type data: str
    :returns: str
    """

    if md5:
        data = get_file(md5)
    strings_data = 'ASCII Strings\n'
    strings_data += "-" * 30
    strings_data += "\n"
    ascii_regex = re.compile('([ -~]{4,})')
    matches = ascii_regex.findall(data)
    strings_data += '\n'.join([x for x in matches])
    return strings_data + "\n\n\n\n"

def make_unicode_strings(md5=None, data=None):
    """
    Find and return all printable Unicode strings in a string.

    :param md5: The MD5 of the Sample to parse.
    :type md5: str
    :param data: The data to parse.
    :type data: str
    :returns: str
    """

    if md5:
        data = get_file(md5)
    strings_data = 'Unicode Strings\n'
    strings_data += "-" * 30
    strings_data += "\n"
    unicode_regex = re.compile('(([%s]\x00){4,})' % string.printable)
    matches = unicode_regex.findall(data)
    strings_data += '\n'.join([x[0].replace('\x00', '') for x in matches])
    return strings_data + "\n\n\n\n"

def make_stackstrings(md5=None, data=None):
    """
    Find and return all stack strings in a string.

    :param md5: The MD5 of the Sample to parse.
    :type md5: str
    :param data: The data to parse.
    :type data: str
    :returns: str
    """

    if md5:
        data = get_file(md5)
    x = 0
    prev = 0
    strings = ''
    while x < len(data):
        if (data[x] == '\xc6') and ((data[x+1] == '\x45') or (data[x+1] == '\x84')):
            a = ord(data[x+3])
            if (a <= 126 and a >= 32) or (a==9): strings += data[x+3]
            prev = x
            x += 4
        elif (data[x] == '\xc6') and (data[x+1] == '\x44'):
            a = ord(data[x+4])
            if (a <= 126 and a >= 32) or (a==9): strings += data[x+4]
            prev = x
            x += 5
        elif (data[x] == '\xc6') and ((data[x+1] == '\x05') or (data[x+1] == '\x85')):
            a = ord(data[x+6])
            if (a <= 126 and a >= 32) or (a==9): strings += data[x+6]
            prev = x
            x += 7
        else:
            if ((x - prev) ==12): strings += '\n'
            x += 1
    strings = strings.replace('\x00', '\r')
    return strings

def make_hex(md5=None, data=None):
    """
    Convert data into hex formatted output.

    :param md5: The MD5 of the Sample to parse.
    :type md5: str
    :param data: The data to parse.
    :type data: str
    :returns: str
    """

    if md5:
        data = get_file(md5)
    length = 16
    hex_data = ''
    digits = 4 if isinstance(data, unicode) else 2
    for i in xrange(0, len(data), length):
        s = data[i:i+length]
        hexa = ' '.join(["%0*X" % (digits, ord(x))  for x in s])
        text = ' '.join([x if 0x20 <= ord(x) < 0x7F else '.'  for x in s])
        hex_data += "%04X   %-*s   %s\r\n" % (i, length*(digits + 1), hexa, text)
    return hex_data

def xor_string(md5=None, data=None, key=0, null=0):
    """
    XOR data.

    :param md5: The MD5 of the Sample to parse.
    :type md5: str
    :param data: The data to parse.
    :type data: str
    :param key: The XOR key to use.
    :type key: int
    :param null: Whether or not to skip nulls.
    :type null: int (0 or 1)
    :returns: str
    """

    if md5:
        data = get_file(md5)
    out = ''
    for c in data:
        if ord(c) == 0 and null == 1:
            out += c
        elif ord(c) == key and null == 1:
            out += c
        else:
            out += chr(ord(c) ^ key)
    return out

def xor_search(md5=None, data=None, string=None, skip_nulls=0):
    """
    Search a string for potential XOR keys. Uses a small list of common
    plaintext terms, XORs those terms using keys 0-255 and searches the data for
    any match. If there is a match, that key is included in the results.

    :param md5: The MD5 of the Sample to parse.
    :type md5: str
    :param data: The data to parse.
    :type data: str
    :param string: The custom string to XOR and search for.
    :type string: str
    :param skip_nulls: Whether or not to skip nulls.
    :type skip_nulls: int (0 or 1)
    :returns: list
    """

    if md5:
        data = get_file(md5)
    if string is None or string == '':
        plaintext_list = [
                        'This program',
                        'kernel32',
                        'KERNEL32',
                        'http',
                        'svchost',
                        'Microsoft',
                        'PE for WIN32',
                        'startxref',
                        '!This program cannot be run in DOS mode',
                        '\xD0\xCF\x11\xE0\xA1\xB1\x1a\xE1',
                        'D\x00o\x00c\x00u\x00m\x00e\x00n\x00t\x00 \x00S\x00u\x00m\x00m\x00a\x00r\x00y\x00 \x00I\x00n\x00f\x00o\x00r\x00m\x00a\x00t\x00i\x00o\x00n',
                        ]
    else:
        plaintext_list = ["%s" % string]
    results = []
    for plaintext in plaintext_list:
        for i in range(0, 255):
            xord_string = xor_string(data=plaintext,
                                     key=i,
                                     null=skip_nulls)
            if xord_string in data:
                if i not in results:
                    results.append(i)
    results.sort()
    return results

def make_list(s):
    """
    Make a list of out a string of data that needs to be parsed using
    :class:`csv.reader`.

    :param s: The string to convert
    :type s: str
    :returns: list
    """

    l = []
    l.append(s)
    a = csv.reader(l, skipinitialspace=True)
    b = None
    for i in a:
        b = i
    return b

def remove_html_tags(data):
    """
    Remove html tags from a string.

    :param data: The string to parse.
    :type data: str
    :returns: str
    """

    p = re.compile(r'<.*?>')
    return p.sub('', data)

def datestring_to_isodate(datestring):
    """
    Parse a string using :class:`dateutil` and return the results.

    :param datestring: The date string to parse.
    :returns: datetime.datetime
    """

    return parse(datestring, fuzzy=True)

def clean_dict(dict_, keys_to_remove):
    """
    Remove keys we don't want to display to the user.

    Can also be used to remove keys from user input that we want to manage
    ourselves. In the latter case, be sure the query is using $set and not
    completely replacing the document, otherwise keys added elsewhere might
    be lost.

    :param dict_: The dictionary to iterate over.
    :type dict_: dict
    :param keys_to_remove: The list of keys we want to remove.
    :type keys_to_remove: list
    """

    for key in keys_to_remove:
        if key in dict_:
            del dict_[key]

def json_handler(obj):
    """
    Handles converting datetimes and Mongo ObjectIds to string.

    Usage: json.dumps(..., default=json_handler)

    :param obj: The object that needs converting.
    :type obj: datetime.datetime, ObjectId
    :returns: str
    """

    if isinstance(obj, datetime.datetime):
        return datetime.datetime.strftime(obj, settings.PY_DATETIME_FORMAT)
    elif isinstance(obj, ObjectId):
        return str(obj)

def generate_qrcode(data, size):
    """
    Generate a QR Code Image from a string.

    Will attempt to import qrcode (which also requires Pillow) and io. If
    this fails we will return None.

    :param data: data to be converted into a QR Code
    :type data: str
    :param size: tuple of (width, height) in pixels to resize the QR Code
    :type size: tuple
    :returns: str in base64 format
    """

    try:
        import qrcode, io
    except:
        return None
    a = io.BytesIO()
    qr = qrcode.QRCode()
    qr.add_data(data)
    img = qr.make_image().resize(size)
    img.save(a, 'PNG')
    qr_img = a.getvalue().encode('base64').replace('\n', '')
    a.close()
    return qr_img

def validate_md5_checksum(md5_checksum):
    """
    Validates that string is truly an MD5.

    :param md5_checksum: The string to validate.
    :type md5_checksum: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """
    retVal = {'success': True, 'message': ''}

    if re.match("^[a-fA-F0-9]{32}$", md5_checksum) == None:
        retVal['message'] += "The MD5 digest needs to be 32 hex characters."
        retVal['success'] = False

    return retVal

def validate_sha1_checksum(sha1_checksum):
    """
    Validates that string is truly a SHA1.
    :param sha1_checksum: str
    :return: dict with keys "success" (boolean) and "message" (str)
    """
    retVal = {'success': True, 'message': ''}

    if re.match("^[a-fA-F0-9]{40}$", sha1_checksum) == None:
        retVal['message'] += "The SHA1 digest needs to be 40 hex characters."
        retVal['success'] = False

    return retVal

def validate_sha256_checksum(sha256_checksum):
    """
    Validates that string is truly a SHA256.

    :param sha256_checksum: The string to validate.
    :type sha256_checksum: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """
    retVal = {'success': True, 'message': ''}

    if re.match("^[a-fA-F0-9]{64}$", sha256_checksum) == None:
        retVal['message'] += "The SHA256 digest needs to be 64 hex characters."
        retVal['success'] = False

    return retVal

def detect_pcap(data):
    """
    Detect if the data has the magic numbers for a PCAP.

    :param data: The data to inspect.
    :type data: str
    :returns: bool
    """

    magic = ''.join(x.encode('hex') for x in data[:4])
    if magic in (
        'a1b2c3d4', #identical
        'd4c3b2a1', #swapped
        '4d3cb2a1',
        'a1b23c4d', #nanosecond resolution
        '0a0d0d0a', #pcap-ng
    ):
        return True
    else:
        return False
