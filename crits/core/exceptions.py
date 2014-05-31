class ZipFileError(Exception):
    """
    Exception class for dealing with errors that arise when uploading
    zip files.  The primary reason for defining the class is to be able
    to bundle up any errors that occur, handle them gracefully and present
    an appropriate error message to the user
    """

    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
