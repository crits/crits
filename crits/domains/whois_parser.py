import re

class WhoisEntry(object):
    """
    This is a best-effort WHOIS entry parser. Unfortunately, WHOIS servers can
    do pretty much whatever they want to with the data they return, so there's
    really no predictability to the format that data will take. We'll do our
    best with the common data formats and leave it up to the end user to
    "massage" the resulting data as needed.
    """

    def __init__(self, text):
        self._text = text
        self.fields = {}
        self.keys = []

    def __str__(self):
        if not self.keys:
            self.parse_whois()
        data_str = ""
        for key in self.keys:
            val = self.fields[key]
            key_str = "%s: "%key
            if isinstance(val, list):
                val_str = key_str = ""
                for item in val:
                    val_str = "%s%s: %s\n"%(val_str, key, item)
                val = val_str[:-1] #eliminate the final newline
            data_str = "%s%s%s\n\n"%(data_str, key_str, val)
        return data_str

    @staticmethod
    def from_dict(d):
        """
        Create a WhoisEntry from a dictionary of WHOIS fields.
        """

        w = WhoisEntry("")
        w.fields = d
        w.keys = sorted(w.fields.keys())
        return w

    def to_dict(self):
        if not self.fields:
            self.parse_whois()
        return self.fields

    def parse_whois(self):
        """
        Parse the entry.
        """

        entry = self._text.splitlines()
        key = None
        val = ""
        for line in entry:
            #Ignore comments, where possible, and empty lines
            if line.lower().startswith(('>>>', 'queried')) or not line.strip():
                continue
            #some servers separate keys from values with a non-deterministic
            #       number of periods to make the output line up prettily.
            # Hopefully there are always at least four of them.
            if '....' in line:
                #so find where the dots start
                start_pos = line.find('....')
                #and where they end
                end_pos = line.rfind('....') + 4
            #this data is a little more normal; unfortunately this format will do funny things with timestamps
            #       on a line that has no key. e.g., "Record last updated at 2012-01-07 05:43:11"
            #       For lines that contain Internet protocol identifiers, e.g., "http://", do our best to
            #       do the right thing and not parse the protocol as a key.
            elif ':' in line and not line[line.find(':')+1:line.find(':')+3] == "//":
                start_pos = line.find(':')
                end_pos = start_pos + 1
            else:
                #A line with no key is *probably* a continuation of a multi-line value for the previous key.
                # Though this is not necessarily true, we'll assume so. Sadly, this will do funny things if
                #       there are blobs of text in the middle   of the WHOIS text that give us no indication that
                #       they're just comments.

                #Since many whois results begin with a blob of text that we don't care about,
                #       we'll first make sure we've already begun processing keys.
                if key is not None:
                    # We may have seen this key before, and it may already have multiple values
                    if isinstance(self.fields[key], list):
                        self.fields[key].append(line.strip())
                        continue
                    # If we get here, the preexisting value is a string, so join it
                    if self.fields[key]:
                        joiner = '\n'
                    else:
                        joiner = ''
                    val = joiner.join([val, line.strip()])
                    self.fields[key] = val
                continue

            key = line[:start_pos].strip().title()
            val = line[end_pos:].strip()

            #'.' is not allowed in MongoDB keys, so we'll strip any to keep from
            # breaking things.
            if '.' in key:
                key = re.sub('\.', '', key)
            #also, '$' may not be the first character
            if key.startswith('$'):
                key = key[1:]

            #if we've seen the key before, append the new value to a list of values
            if key in self.fields:
                if isinstance(self.fields[key], list):
                    self.fields[key].append(val)
                    #print key, self.fields[key], val
                else:
                    self.fields[key] = [self.fields[key], val]
            else:
                self.fields[key] = val
        self.keys = sorted(self.fields.keys())

if __name__ == "__main__":
    """
    Run a test.
    """

    my_text = '''Queried whois.internic.net with "dom sportsontheweb.net"...
       Domain Name: SPORTSONTHEWEB.NET
       Registrar: ENOM, INC.
       Whois Server: whois.enom.com
       Referral URL: http://www.enom.com
       Name Server: NS1.RUNHOSTING.COM
       Name Server: NS2.RUNHOSTING.COM
       Status: clientTransferProhibited
       Updated Date: 12-apr-2012
       Creation Date: 11-may-2007
       Expiration Date: 11-may-2013
    >>> Last update of whois database: Mon, 30 Apr 2012 17:04:12 UTC <<<
    Queried whois.enom.com with "sportsontheweb.net"...
    Visit AboutUs.org for more information about sportsontheweb.net
    <a href="http://www.aboutus.org/sportsontheweb.net">AboutUs: sportsontheweb.net</a>
    Domain name: sportsontheweb.net
    Administrative Contact:
       AttractSoft GmbH
       Customer Service (support@supportindeed.com)
       +49.4312207240
       Fax: +49.43155683399
       Mathildenstr. 18
       Kiel, SH 24148
       DE
    Technical Contact:
       AttractSoft GmbH
       Customer Service (support@supportindeed.com)
       +49.4312207240
       Fax: +49.43155683399
       Mathildenstr. 18
       Kiel, SH 24148
       DE
    Registrant Contact:
       AttractSoft GmbH
       Customer Service ()

       Fax:
       Mathildenstr. 18
       Kiel, SH 24148
       DE
    Status: Locked
    Name Servers:
       ns1.runhosting.com
       ns2.runhosting.com

    Creation date: 11 May 2007 07:37:32
    Expiration date: 11 May 2013 07:37:00
    '''
    p = WhoisEntry(my_text)
    #p.parse_whois()
    print p
    print WhoisEntry.from_dict(p.fields)
