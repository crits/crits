from django.conf import settings
if settings.FILE_DB == settings.S3:
    from crits.core.s3_tools import get_file_s3

import gridfs
import pymongo

import magic

class MongoError(Exception):
    """
    Generic MongoError exception.
    """
    pass

# TODO: mongo_connector() and gridfs_connector() can probably be combined into
# one function.

# Setup standard connector to the MongoDB instance for use in any functions
def mongo_connector(collection, preference=settings.MONGO_READ_PREFERENCE):
    """
    Connect to the mongo database if you need to use PyMongo directly and not
    use MongoEngine.

    :param collection: the collection to use.
    :type collection: str
    :param preference: PyMongo Read Preference for ReplicaSet/clustered DBs.
    :type preference: str.
    :returns: :class:`pymongo.MongoClient`,
              :class:`crits.core.mongo_tools.MongoError`
    """

    try:
        connection = pymongo.MongoClient("%s" % settings.MONGO_HOST,
                                        settings.MONGO_PORT,
                                        read_preference=preference,
                                        ssl=settings.MONGO_SSL)
        db = connection[settings.MONGO_DATABASE]
        if settings.MONGO_USER:
            db.authenticate(settings.MONGO_USER, settings.MONGO_PASSWORD)
        return db[collection]
    except pymongo.errors.ConnectionFailure as e:
        raise MongoError("Error connecting to Mongo database: %s" % e)
    except KeyError as e:
        raise MongoError("Unknown database or collection: %s" % e)
    except:
        raise

def gridfs_connector(collection, preference=settings.MONGO_READ_PREFERENCE):
    """
    Connect to the mongo database if you need to use PyMongo directly and not
    use MongoEngine. Used specifically for accessing GridFS.

    :param collection: the collection to use.
    :type collection: str
    :param preference: PyMongo Read Preference for ReplicaSet/clustered DBs.
    :type preference: str.
    :returns: :class:`gridfs.GridFS`,
              :class:`crits.core.mongo_tools.MongoError`
    """

    try:
        connection = pymongo.MongoClient("%s" % settings.MONGO_HOST,
                                        settings.MONGO_PORT,
                                        read_preference=preference,
                                        ssl=settings.MONGO_SSL)
        db = connection[settings.MONGO_DATABASE]
        if settings.MONGO_USER:
            db.authenticate(settings.MONGO_USER, settings.MONGO_PASSWORD)
        return gridfs.GridFS(db, collection)
    except pymongo.errors.ConnectionFailure as e:
        raise MongoError("Error connecting to Mongo database: %s" % e)
    except KeyError as e:
        raise MongoError("Unknown database: %s" % e)
    except:
        raise

def get_file(sample_md5, collection=settings.COL_SAMPLES):
    """
    Get a file from GridFS (or S3 if that's what you've configured).

    :param sample_md5: The MD5 of the file to download.
    :type sample_md5: str
    :param collection: The collection to grab the file from.
    :type collection: str
    :returns: str
    """

    # Workaround until pcap download uses pcap object
    if settings.FILE_DB == settings.GRIDFS:
        return get_file_gridfs(sample_md5, collection)
    elif settings.FILE_DB == settings.S3:
        objs = mongo_connector(collection)
        obj = objs.find_one({"md5": sample_md5})
        oid = obj['filedata']
        return get_file_s3(oid,collection)

def put_file(m, data, collection=settings.COL_SAMPLES):
    """
    Add a file to storage.

    :param m: The filename.
    :type m: str
    :param data: The data to add.
    :type data: str
    :param collection: The collection to grab the file from.
    :type collection: str
    :returns: str
    """

    return put_file_gridfs(m, data, collection)

def get_file_gridfs(sample_md5, collection=settings.COL_SAMPLES):
    """
    Get a file from GridFS.

    :param sample_md5: The MD5 of the file to download.
    :type sample_md5: str
    :param collection: The collection to grab the file from.
    :type collection: str
    :returns: str
    """

    data = None
    try:
        fm = mongo_connector("%s.files" % collection)
        objectid = fm.find_one({'md5': sample_md5}, {'_id': 1})['_id']
        fs = gridfs_connector("%s" % collection)
        data = fs.get(objectid).read()
    except Exception:
        return None
    return data

def put_file_gridfs(m, data, collection=settings.COL_SAMPLES):
    """
    Add a file to storage.

    :param m: The filename.
    :type m: str
    :param data: The data to add.
    :type data: str
    :param collection: The collection to grab the file from.
    :type collection: str
    :returns: str
    """

    mimetype = magic.from_buffer(data, mime=True)
    try:
        fs = gridfs_connector("%s" % collection)
        fs.put(data, content_type="%s" % mimetype, filename="%s" % m)
    except Exception:
        return None
    return m

def delete_file(sample_md5, collection=settings.COL_SAMPLES):
    """
    delete_file allows you to delete a file from a gridfs collection specified
    in the collection parameter.
    this will only remove the file object, not metadata from assocatiated collections
    for full deletion of metadata and file use delete_sample

    :param sample_md5: The MD5 of the file to delete.
    :type sample_md5: str
    :param collection: The collection to delete the file from.
    :type collection: str
    :returns: True, False, None
    """
    fm = mongo_connector("%s.files" % collection)
    sample = fm.find_one({'md5': sample_md5}, {'_id': 1})
    success = None
    if sample:
        objectid = sample["_id"]
        fs = gridfs_connector("%s" % collection)
        try:
            fs.delete(objectid)
            return True
        except:
            return None
    return success

####################################################
# NOTE: The following wrappers are only here for   #
#       legacy code and rare instances where we    #
#       cannot use MongoEngine to achieve our      #
#       goal. Please use these as a last resort!   #
####################################################

# Wrapper for pymongo's find_one function
def mongo_find_one(collection, query, fields=None, skip=0, sort=None,
                   *args, **kwargs):
    """
    Find one document from a collection matching the parameters.

    :param collection: The collection to query.
    :type collection: str
    :param query: The query to find the document(s).
    :type query: dict
    :param fields: The fields to return for each document.
    :type fields: dict
    :param skip: How many documents to skip before returning.
    :type skip: int
    :param sort: How to sort the results.
    :type sort: dict
    :returns: PyMongo cursor.
    """

    col = mongo_connector(collection)
    return col.find_one(query, fields, skip=skip, sort=sort, *args, **kwargs)

# Wrapper for pymongo's find function
def mongo_find(collection, query, fields=None, skip=0, limit=0, sort=None,
               count=False, *args, **kwargs):
    """
    Find documents from a collection matching the parameters.

    :param collection: The collection to query.
    :type collection: str
    :param query: The query to find the document(s).
    :type query: dict
    :param fields: The fields to return for each document.
    :type fields: dict
    :param skip: How many documents to skip before returning.
    :type skip: int
    :param limit: How many documents to return.
    :type limit: int
    :param sort: How to sort the results.
    :type sort: dict
    :param count: Only return a count of the documents.
    :type count: boolean
    :returns: PyMongo cursor, int
    """

    col = mongo_connector(collection)
    results = col.find(query, fields, skip=skip, limit=limit, sort=sort,
                       *args, **kwargs)
    if not kwargs.get('timeout', True):
        col.close
    if count:
        return results.count()
    else:
        return results

# Wrapper for pymongo's insert function
def mongo_insert(collection, doc_or_docs, username=None, safe=True, *args,
                 **kwargs):
    """
    Insert documents into a collection.

    :param collection: The collection to query.
    :type collection: str
    :param doc_or_docs: A single document or list of documents to insert.
    :type doc_or_docs: dict or list
    :param username: The user inserting these documents.
    :type username: str
    :param safe: Whether or not to insert in safe mode.
    :type safe: boolean
    :returns: dict with keys:
              "success" (boolean),
              "message" (list),
              "object" (insertion response) if successful.
    """

    col = mongo_connector(collection)
    try:
        col.insert(doc_or_docs, safe=safe, check_keys=True, *args, **kwargs)
        return {'success':True, 'message':[], 'object':doc_or_docs}
    except Exception, e:
        # OperationFailure gets raised only if safe=True and there is some error
        return {'success':False, 'message':[format_error(e)]}


# Wrapper for pymongo's update function
def mongo_update(collection, query, alter, username=None,
                 multi=True, upsert=False, safe=True, *args, **kwargs):
    """
    Update documents in a collection.

    :param collection: The collection to query.
    :type collection: str
    :param query: The query to use to find the documents to update.
    :type query: dict
    :param alter: How to update the documents.
    :type alter: dict
    :param username: The user updating the documents.
    :type username: str
    :param multi: Whether or not to update multiple documents.
    :type multi: boolean
    :param upsert: Insert documents into the collection if they are not found.
    :type upsert: boolean
    :param safe: Use safe mode while performing the update.
    :type safe: boolean
    :returns: dict with keys "success" (boolean) and "message" (list)
    """

    col = mongo_connector(collection)
    try:
        r = col.update(query, alter, multi=multi, upsert=upsert,
                       check_keys=True, safe=safe, *args, **kwargs)
        return {'success':True, 'message':[r]}
    except Exception, e:
       return {'success':False, 'message':[format_error(e)]}

# Wrapper for pymongo's save function
def mongo_save(collection, to_save, username=None, safe=True, *args, **kwargs):
    """
    Save a document to a collection.

    :param collection: The collection to query.
    :type collection: str
    :param to_save: The document to save.
    :type to_save: dict
    :param username: The user saving the document.
    :type username: str
    :param safe: Use safe mode while performing the save.
    :type safe: boolean
    :returns: dict with keys "success" (boolean) and "message" (list)
    """

    col = mongo_connector(collection)
    try:
        r = col.save(to_save, check_keys=True, manipulate=True, safe=safe,
                     *args, **kwargs)
        return {'success':True, 'message':[r]}
    except Exception, e:
       return {'success':False, 'message':[format_error(e)]}

# Wrapper for pymongo's find_and_modify function
def mongo_find_and_modify(collection, query, alter, fields=None, username=None,
                          sort={}, remove=False, new=False, upsert=False, *args,
                          **kwargs):
    """
    Find documents from a collection matching the parameters, update them, and
    return them.

    :param collection: The collection to query.
    :type collection: str
    :param query: The query to use to find the documents to update.
    :type query: dict
    :param alter: How to update the documents.
    :type alter: dict
    :param fields: The fields to return for each document.
    :type fields: dict
    :param username: The user updating the documents.
    :type username: str
    :param sort: How to sort the results.
    :type sort: dict
    :param remove: Remove documents instead of update.
    :type remove: boolean
    :param new: Return the updated documents instead of the original ones.
    :param upsert: Insert documents into the collection if they are not found.
    :type upsert: boolean
    :returns: dict with keys:
              "success" (boolean),
              "message" (list),
              "object" (cursor) if successful.
    """
    try:
        col = mongo_connector(collection)
        result = col.find_and_modify(query, update=alter, fields=fields,
                                     remove=remove, new=new, upsert=upsert,
                                     sort=sort, *args, **kwargs)
    except Exception, e:
        return {'success':False, 'message':[format_error(e)]}
    try:
        return {'success':True, 'message':[], 'object': result}
    except Exception, e:
        return {'success':True, 'message':[format_error(e)], 'object': result}

# Wrapper for pymongo's remove function
def mongo_remove(collection, query=None, username=None, safe=True, verify=False,
                 *args, **kwargs):
    """
    Find documents from a collection matching the parameters.

    :param collection: The collection to query.
    :type collection: str
    :param query: The query to use to find the documents to remove.
    :type query: dict
    :param username: The user removing the documents.
    :type username: str
    :param safe: Use safe mode while removing the documents.
    :type safe: boolean
    :param verify: Verify the removal.
    :type verify: boolean
    :returns: dict with keys "success" (boolean) and "message" list.
    """

    if not query:
        return {'success': False, 'message':['No query supplied to remove']}
    else:
        try:
            col = mongo_connector(collection)
            col.remove(query, safe=safe, *args, **kwargs)
            if verify:
                if mongo_find(collection, query, count=True):
                    return {'success':False,
                            'message':['Unknown error; unable to remove item']}
            return {'success':True, 'message':[]}
        except Exception, e:
            return {'success':False, 'message':[format_error(e)]}

def format_error(e):
    """
    wrapper for core/handlers format_error function.
    Redefined here to avoid circular imports.

    :param e: The error.
    :type e: :class:`Exception`
    :returns: str
    """

    from crits.core.handlers import format_error as fe
    return fe(e)
