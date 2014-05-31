#LDAP Auth in CRITs#

[TOC]


This guide covers the basics of using LDAP authentication in CRITs. There are
a few options and definitely some gotchas and hopefully this document will help
you answer those questions. This guide should cover Active Directory and LDAP
implementations regardless of your opinion on AD = LDAP :)

##LDAP Configuration Options##
All LDAP configuration options can be accessed via the CRITs Control Panel in
the `Navigation Menu`_ Within the Control Panel Menu, an entry exists for
*System*. This is where the LDAP options can be set.

LDAP Authentication in CRITs is set up to attempt to bind to the LDAP directory
using the end user supplied username and password credentials. It currently does
not use a user account to bind to LDAP and then search for usernames supplied.

###Control Panel Options###
-----
**Remote user:**
This checkbox will force CRITs to attempt to authenticate all users externally
to CRITs. Local users will loose their access and you may have to reset the
configuration from command line to regain access to CRITs.

**Create unknown user:**
This checkbox will attempt to create CRITs users via remote authenticated users.
If a user supplies a valid username and password, CRITs will allow them access
to the installation.

**Ldap auth:**
This checkbox tells CRITs you want to look usernames up in an external LDAP
database. If CRITs cannot find the username in the external database it will try
to authenticate via it's local database stored in Mongo.

**Ldap tls:**
This checkbox indicates that CRITs should use TLS to protect the information it
is passing to the LDAP server to prevent sniffing of credentials on the wire.
If you are using LDAP auth, it is highly recommended that you use TLS as well.

**Ldap server:**
Input box defines what server, via fqdn or IP address, you want CRITs to send
authentication attempts. You can use a FQDN of an active directory domain here
if DNS will resolve the domain controllers, but CRITs is not AD Site aware and may
attempt to contact a remote DC for authentication.

**Ldap usercn:**
When using a distinguished name for logins, this box tells crits what to prepend
to the LDAP request. Typically it's a setting like *cn=* or *uid=*. If you are
using a User Principal name like *user@domain.name*, leave this option blank.

**Ldap userdn:**
This section defines what additional strings to append to your username login
requests. When using a distinguished name, a standard DN string is used. When
using a User Principal name, a *@domain.name* is used.

- **Using a Distinguished Name:**
When using a distinguished name, you must specify when in the LDAP structure the
user account resides. If you are authenticating against Active Directory, this
means you need to point at the OU the user currently resides. For example, if
you have an Active Directory structure based in the domain killchain.com. In
your domain, you user accounts live in the /UsersAndGroups/Users OU, your
distinguished name entry for *Ldap userdn* would look like
```
OU=Users,OU=UsersAndGroups,DC=killchain,DC=com
```
This means ++all++ users that need to access CRITs must be located in this OU
as CRITs will not search the directory structure for other users. Also, in most
AD structures user object *CN* are the users full name as in *John Doe* in this
case to enable a user to log in with his/her CN you would need to make a user in
crits with a username `John Doe` and the string passed via LDAP auth would look
like this example
```
CN=John Doe,OU=Users,OU=UsersAndGroups,DC=killchain,DC=com
```
==Remember CRITs usernames are case sensitive== when the user logs in they must
provide the spacing and case exactly as entered in the CRITs configuration.

- **Using a User Principal Name:**
In the case you want to make your life simple and enable your user to log in
with their *username* associated with a AD domain name, in our example you
would set the *Ldap usercn* to be blank and set *Ldap userdn* to
```
@killchain.com
```
Creating the username in CRITs, again in our example, as jdoe the string passed
to the ldap server would look like
```
jdoe@killchain.com
```

**Ldap update on login:**
This selection defines that you wants CRITs to search for user attributes in the
LDAP schema and update the local configuration options such as email address,
first name, last name, etc.
