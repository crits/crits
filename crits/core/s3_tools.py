from django.conf import settings
from bson.objectid import ObjectId
import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key

class S3Error(Exception):
    """
    Generic S3 Exception.
    """

    pass

def s3_connector(bucket):
    """
    Connect to an S3 bucket.

    :param bucket: The bucket to connect to.
    :type bucket: str
    :returns: :class:`boto.s3.connection.S3Connection`, S3Error
    """

    S3_hostname = getattr(settings, 'S3_HOSTNAME', S3Connection.DefaultHost)
    try:
        conn = S3Connection(aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
                            is_secure = True,
                            host = S3_hostname)

        mybucket = conn.get_bucket(bucket)
        return mybucket
    except boto.exception.S3ResponseError as e:
        raise S3Error("Error connecting to S3: %s" % e)
    except:
        raise

def s3_create_bucket(bucket):
    """
    Create an S3 bucket.

    :param bucket: The bucket to create.
    :type bucket: str
    :returns: S3Error
    """

    try:
        S3_hostname = getattr(settings, 'S3_HOSTNAME', S3Connection.DefaultHost)
        conn = S3Connection(aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
                            is_secure = True,
                            host = S3_hostname)
        conn.create_bucket(bucket)
    except boto.exception.S3CreateError as e:
        raise S3Error("Error creating bucket in S3: %s" % e)
    except:
        raise

def s3_translate_collection(collection):
    """
    Translate CRITs collection to S3 bucket.

    :param collection: The collection to translate.
    :type collection: str
    :returns: str
    """

    bucket = settings.COLLECTION_TO_BUCKET_MAPPING[collection.replace(".files","")]
    return bucket + settings.S3_SEPARATOR + settings.S3_ID

def file_exists_s3(sample_md5, collection):
    """
    Determine if a file aleady exists in S3.

    :param sample_md5: The MD5 to search for.
    :type sample_md5: str
    :param collection: The collection to translate for lookup.
    :type collection: str
    :returns: str
    """

    bucket = s3_connector(s3_translate_collection(collection))
    return bucket.get_key(sample_md5)

def put_file_s3(data, collection):
    """
    Add a file to S3.

    :param data: The data to add.
    :type data: str
    :param collection: The collection to translate for addition.
    :type collection: str
    :returns: str
    """

    bucket = s3_connector(s3_translate_collection(collection))
    k = Key(bucket)
    oid = ObjectId()
    k.key = oid
    # TODO: pass md5 to put_file() to avoid recalculation.
    k.set_contents_from_string(data)
    return oid

def get_file_s3(oid, collection):
    """
    Get a file from S3.

    :param oid: The ObjectId to lookup.
    :type oid: str
    :param collection: The collection to translate for lookup.
    :type collection: str
    :returns: str
    """

    bucket = s3_connector(s3_translate_collection(collection))
    k = bucket.get_key(oid)
    return k.get_contents_as_string()

def get_filename_s3(sample_md5, collection):
    """
    Get a filename from S3.

    :param sample_md5: The MD5 to lookup.
    :type sample_md5: str
    :param collection: The collection to translate for lookup.
    :type collection: str
    :returns: str
    """

    try:
        bucket = s3_connector(s3_translate_collection(collection))
        k = bucket.get_key(sample_md5)
        filename = k.get_metadata("filename")
    except Exception:
        return None
    return filename

def delete_file_s3(sample_md5, collection):
    """
    Remove a file from S3.

    :param sample_md5: The MD5 to remove.
    :type sample_md5: str
    :param collection: The collection to translate for lookup.
    :type collection: str
    :returns: True, None
    """

    try:
        bucket = s3_connector(s3_translate_collection(collection))
        k = bucket.get_key(sample_md5)
        k.delete()
        return True
    except Exception:
        return None
