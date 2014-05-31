"""A module for parsing e-mail content from pcap files.

Exported Classes:

smtpcap -- Extract SMTP sessions from a pcap file and present e-mail content.

"""

import nids
from email.parser import Parser
import tempfile
import hashlib
import magic
from multiprocessing import Process, Queue


"""
Due to issues with the implementation of nids, it only wants to be imported and initialized once - multiple
import/init attempts result in seg faults.  Therefore, when parsing pcaps, we need to do it in a separate
process to ensure that nids is only loaded once.  Unfortunately, there's an issue with Python, Django and
multithreading.  Based upon this post to stackoverflow

http://stackoverflow.com/questions/13193278/understand-python-threading-bug

I've implemented the following patch and it seems to have 'fixed' the DummyThread error.  If/when Python
fixes this issue, this patch should probably be removed.
"""
import threading
threading._DummyThread._Thread__stop = lambda x: 42


class smtpcap:
    """Extract SMTP sessions from a pcap file and present e-mail content.

    Public functions:
    get_all_headers -- Retrieve either all message headers, or all header
    values for a specific header name.

    get_content -- Retrieve decoded content for all message parts in a message.

    get_header -- Retrieve header value for a specific header name.

    get_message_count -- Retrieve a count of the number of messages processed.

    parse_pcap -- Parse a pcap data blob for SMTP sessions.

    """
    def __init__(self):
        """Given the name of a pcap file, store individual SMTP sessions."""
        self.smtp = None

    def get_all_headers(self, message_id, name=""):
        """Retrieve either all message headers or all header values for a specific
        header name.

        :Parameters:
            message_id : integer - identifier for a specific message pulled from pcap
            name : (Optional) string - retrieve only header values for name

        :Returns:
            headers : list of header names and values

        """
        headers = []
        message = self._get_message(message_id)

        if message:
            if name:
                headers = message.get_all(name)
            else:
                headers = message.items()

        return headers

    def get_content(self, message_id):
        """Retrieve decoded content for all message parts in a message.

        :Parameters:
            message_id : integer - identifier for a specific message pulled from pcap

        :Returns:
            content : list of dictionaries containing message parts
                parts:[{
                        'filename':<string>,
                        'message-content-type':<string>,
                        'magic-content-type':<string>,
                        'encoding':<string>,
                        'content':<message part data>
                       }]

        """
        parts = []
        message = self._get_message(message_id)

        if message:

            # Walk each part for multipart messages
            if message.is_multipart():
                for part in message.walk():
                    part_info = self._get_part_info(part)
                    if part_info:
                        parts.append(part_info)
            else:
                part_info = self._get_part_info(message)
                if part_info:
                    parts.append(part_info)

        return parts

    def get_header(self, message_id, name):
        """ Retrieve header value for a specific header name.

        :Parameters:
            message_id : integer - identifier for a specific message pulled from pcap

        :Returns:
            header : string - header value associated with given name

        """
        header = ""
        message = self._get_message(message_id)
        if message:
            header = message.get(name)

        return header

    def get_message_count(self):
        """Retrieve a count of the number of messages processed

        :Paramenters:
            None

        :Returns:
            count : integer

        """
        return len(self.messages)

    def parse_pcap(self, data):
        """ Parse a pcap data blob for SMTP sessions.  Due the way in which the nids library is implemented, there
        are a couple of hoops to jump through in order for it to function properly:

        - the library will only accept the path to a pcap file on disk, therefore we need to first write the uploaded
        blob out to a temporary file, and then feed that to nids.

        - the library can only be loaded and initialized once within an instace of Python, therefore, we need to
        run each instance of nids within its own process.  Note: Running nids in a separate thread was tested
        and does not work, enough of the library is loaded/initialized globally that seg faults still occur.

        :Parameters:
            data : pcap data

        :Returns:
            None

        """

        # Write the pcap blob out to a file
        tempPCAPFile = tempfile.NamedTemporaryFile()
        tempPCAPFile.write(data)
        tempPCAPFile.flush()

        # Instantiate a new process for nids, use a Queue to pass back parsed messages
        out_queue = Queue()
        smtp = _pcap_parser(tempPCAPFile.name)
        proc = Process(target=smtp.run_parser, args=(out_queue,))
        proc.start()
        self.messages = out_queue.get()
        proc.join()

        # Closing the temp file will cause it to be deleted
        tempPCAPFile.close()

    def _get_message(self, message_id):
        """ Retrieve message associated with given internal id

        :Parameters:
            id : integer

        :Returns:
            message : smtp message, if message id does not exist, return ""

        """
        try:
            return self.messages[message_id]
        except IndexError:
            return ""
        return ""

    def _get_part_info(self, part):
        """A 'private' method to build a dictionary of info from a message part.

        :Parameters:
            content : message part data

        :Returns:
            dictionary :
                {
                    'filename':<string>,
                    'message-content-type':<string>,
                    'magic-content-type':<string>,
                    'encoding':<string>,
                    'content':<message part data>
                }
        """
        part_info = {}
        content = part.get_payload(decode=1)

        # Only keep parts with actual content and mimetype not equal to multipart/*
        if content and part.get_content_maintype() != "multipart":
            part_info["content"] = content
            part_info["message-content-type"] = part.get_content_type()

            # If a part doesn't have a filename defined, generate one
            part_info["filename"] = part.get_filename()
            if not part_info["filename"]:
                part_info["filename"] = hashlib.md5(content).hexdigest()

            # If for some reason there is a slash (/) in the filename, convert
            # to a dot so file writes don't fail
            part_info["filename"] = part_info["filename"].replace("/", ".")

            # The content-type associated with a message part is not always that reliable, so
            # feed the message content through magic to get its opinion
            part_info["magic-content-type"] = ""

            try:
                mt = magic.Magic(mime=True)
                part_info["magic-content-type"] = mt.from_buffer(part_info["content"])
            except AttributeError:
                mt = magic.open(magic.MAGIC_MIME)
                mt.load()
                part_info["magic-content-type"] = mt.buffer(part_info["content"])

            # If magic fails, use the content-type from the message
            if not part_info["magic-content-type"]:
                part_info["magic-content-type"] = part.get_content_type()

            # Normalize encoding strings
            part_info["encoding"] = part.get("Content-Transfer-Encoding")
            if part_info["encoding"]:
                part_info["encoding"] = part_info["encoding"].lower()
            else:
                part_info["encoding"] = "none"

        return part_info


# The purpose of this class is to parse a pcap file for SMTP sessions
#
class _pcap_parser:
    """A 'private' class to parse a pcap for SMTP sessions.


    """
    def __init__(self, pcap_path):
        """Initialize and run nids parser on given pcap file."""
        self.pcap_path = pcap_path
        self.messages = []
        self.end_states = (nids.NIDS_CLOSE, nids.NIDS_TIMEOUT, nids.NIDS_RESET)

    def run_parser(self, out_queue):
        try:
            nids.param("filename", self.pcap_path)
            nids.param("scan_num_hosts", 0)     # disable portscan detection
            nids.init()
            nids.chksum_ctl([('0.0.0.0/0', False), ])
            nids.register_tcp(self._handleTcpStream)

            nids.run()

        except Exception:
            self.messages = []

        out_queue.put(self.messages)

    def _handleTcpStream(self, tcp):
        """Parser call-back for processing data streams."""
        # Collect time and IP metadata
        ((src, sport), (dst, dport)) = tcp.addr

        # Grab data for every SMTP session
        if tcp.nids_state == nids.NIDS_JUST_EST:
            if sport == 25 or dport == 25:
                tcp.client.collect = 1
                tcp.server.collect = 1

        # Wait until the SMTP session completes before processing
        elif tcp.nids_state == nids.NIDS_DATA:
            tcp.discard(0)

        # Process SMTP session data
        elif tcp.nids_state in self.end_states:

            # We're only interested in the server side of the traffic
            server_data = tcp.server.data[:tcp.server.count]

            # Python's email parser module doesn't seem to like ESMTP
            # formatted messages, so we'll skip the EHLO -> DATA header,
            # parse from the first 'Received:' value, and add the ESMTP
            # header values back in later.
            f = server_data.find("Received:")
            message = Parser().parsestr(server_data[f:])

            # Add ESMTP headers back into the email message object
            esmtp_start = server_data.find("EHLO")
            esmtp_end = server_data.find("DATA")
            if esmtp_start >= 0:
                esmtp_headers = server_data[esmtp_start:esmtp_end]
                for line in esmtp_headers.splitlines():
                    if "EHLO" not in line:
                        (name, value) = line.split(":")
                        message.add_header(name, value)

            self.messages.append(message)
