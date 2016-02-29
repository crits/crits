CRITs Time Based One-time Password Authentication

ToC
1. Overview
2. Implementation
3. FAQ
4. References

== 1. Overview ==
The Time based One Time Password (TOTP) support for CRITs uses the RFC6238 [1]
based implementation of HOTP [2]. This support allows a client to install the
Google Authenticator [3] client to generate unique TOTP passwords that allows
the user to login using a username, password and second factor password in the
form of TOTP token. This feature enables two-factor authentication for all
users.

This feature requires a third party package not part of the standards CRITs
dependancies. The pycrypto package [4] is used for generating random numbers
used in the generation of new secrets and AES for encrypting and decrypting
secrets from the database.

Every user will be forced to authenticate initially to CRITs using a standard
username and password. On first login CRITs will prompt them to generate a new
OTP password and secret. Once a secret has been established the user will then
be required to enter username, password and valid OTP for all subsequent
logins. Every user is responsible for properly recording their unique secret in
Google Authenticator.

== 2. Implementation ==
The following steps occur when a user attempts to authenticate to CRITs.

1. On login, CRITs will check if the user has a valid TOTP 'secret' value in
the mongodb user collection.

2. If the user does not have a valid 'secret', redisplay the login page with a
message stating the next login will capture a unique password.

2a. The value in the OTP field will be the users password, this password is
used to encrypt / decrypt the secret key in the CRITs database.

2b. A new secret key is generated for the user using the pycrypto random
function, encrypted with AES using the password as the key. The users password
is run through pbkdf2 to generate the key material passed into the AES
encryption algorithm. The resulting encrypted blob is stored in the users
mongodb profile document.

2c. The user is displayed their new secret key, which they must enter into
their Google Authenticator client. The user must enter the key as displayed,
any change will result in an inoperable state, CRITs does not keep a copy of
the plaintext secret after this point.

3. After a user has a secret established all subsequent logins require a valid
username, password and OTP. The OTP is a combination of their OTP password
generated in 2a followed by the current 6-digit number provided by Google
Authenticator.

3a. CRITs first verifies that the username and password combination is valid.
If valid CRITs will process the OTP.

3b. The OTP is broken into 2 parts - the password and the 6-digit token.

3c. CRITs retrieves the users stored secret created in 2b from the database and
decrypts it using the OTP password supplied by the user.

3d. CRITs uses the secret to compute 5 valid 6-digit tokens using the HOTP
algorithm. Each 6-digit token is valid for 30-seconds and CRITs will accept up
to 2 values before or after the current value to account for time skew among
devices and latency in the request.

3e. If the CRITs generated 6-digit token matches the user supplied token the
user is authenticated to CRITs and redirected to the next page. If the
comparison fails the user is denied access and must supply new authentication
credentials.

== 3. FAQ ==
* What happens if a user loses their secret, either because they cannot access
Google Authenticator or the secret has been deleted from their device?

Secrets can theoretically be recovered using the users OTP password by
decrypting the value in the database. There is no supported way to do this,
someone would need to do this manually.

The supported method is to contact your local CRITs administratior who may 
clear the encrypted blob that is stored in the users mongodb profile document. 
This may be performed either in the CRITs Web UI or from the command line using
the following command executed from your base CRITs installation directory:

"python manage.py users -u [USER] -c "

This will clear the affected users encrypted blob and allow them to re-establish 
a new OTP account.

* When TOTP is enabled, will my API calls be affected?

TOTP is enforced based on originating authentication source through the CRITs Web
UI control panel under System/Auth/Security settings.

* What platforms are supported by Google Authenticator?

A lot. See [4].

* What happens if the users device time skew exceeds 1m?

This implementation does not account for or handle gradual time skew resulting
from lack of time sync. It is critical that the users device syncs time to a
reliable source. In the case of mobile phones this is normally not a problem.

* Can users leverage Google Authenticator on non-mobile devices to generate
valid token codes?

Technically this implementation does not prevent a user from using a desktop
implementation of Google Authenticator (or writing their own software using the
implementation). This is highly **unadvisable** and defeats the second factor
requirement. If the users secret is stolen along with their username and
password it is possible for an adversary to login to their account. Secrets
should be kept only on devices which have a reasonable expectation of security
and not in-band with the user login process.

== 4. References ==

[1] http://tools.ietf.org/html/rfc6238
[2] http://tools.ietf.org/html/rfc4226
[3] http://code.google.com/p/google-authenticator/
[4] https://www.dlitz.net/software/pycrypto/doc/
