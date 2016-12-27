import hmac, base64, struct, hashlib, time
from django.utils.crypto import pbkdf2
from M2Crypto import EVP, Rand

# from http://stackoverflow.com/questions/8529265/google-authenticator-implementation-in-python
def get_hotp_token(secret, intervals_no):
    """
    Calculate the token value given intervals_no is the current time

    :param secret: The secret.
    :type secret: str
    :param intervals_no: The current time.
    :type intervals_no: int
    :returns: str
    """

    msg = struct.pack(">Q", intervals_no)
    h = hmac.new(secret, msg, hashlib.sha1).digest()
    o = ord(h[19]) & 15
    h = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return h

def get_totp_token(secret):
    """
    Call get_hotp_token using current system time as the interval
    truncate time to the nearest 30

    :param secret: The secret.
    :type secret: str
    :returns: str
    """

    return get_hotp_token(secret, intervals_no=int(time.time())//30)

def decrypt_secret(secret, password, username):
    """
    We will get passed in a 16 byte block of data
    that has been enrypted with AES using the PIN
    the first 10 bytes are the secret
    and the remaining 6 are padding

    :param secret: The secret.
    :type secret: str
    :param password: The password.
    :type password: str
    :param username: The user this is for.
    :type username: str
    :returns: str
    """

    secret = base64.b32decode(secret)
    pw_hash = pbkdf2(password.encode('ascii'), username.encode('ascii'), 10000)
    crypt_object = EVP.Cipher('aes_128_ecb', pw_hash, '', 0, padding=0)
    tmp = crypt_object.update(secret)
    return tmp[:10]

def encrypt_secret(secret, password, username):
    """
    Pad the secret with 6 random bytes
    which makes the secret 16 bytes for ECB
    but also makes all encrypted secrets unique
    even if they have the same original value
    which is important for cases where we might allow
    a user to carry over an existing secret from
    another system

    :param secret: The secret.
    :type secret: str
    :param password: The password.
    :type password: str
    :param username: The user this is for.
    :type username: str
    :returns: str
    """

    secret += gen_random(6)
    pw_hash = pbkdf2(password.encode('ascii'), username.encode('ascii'), 10000)
    crypt_object = EVP.Cipher('aes_128_ecb', pw_hash, '', 1, padding=0)
    tmp = crypt_object.update(secret)
    return tmp

def gen_random(secret_len=10):
    """
    The default secret len is 10 so that when
    base32 encoded it results in a stream of
    ascii characters that are easy for the user to
    enter on the device without '=' padding

    :param secret_len: The length of the secret to generate.
    :type secret_len: int
    """

    return Rand.rand_bytes(secret_len)

def gen_user_secret(password, username):
    """
    Create a random secret and return
    the encrypted version and plaintext
    the plaintext is needed to display to the user

    :param password: The password to use.
    :type password: str
    :param username: The user this is for.
    :type username: str
    :returns: tuple
    """

    totp_secret = gen_random(10)
    crypt_secret = encrypt_secret(totp_secret, password, username)
    return (base64.b32encode(crypt_secret), base64.b32encode(totp_secret))

def valid_totp(user, token, secret, diff=2):
    """
    Validate a user/token/secret combination
    return true if the token is valid
    return false if the token is invalid

    :param user: The user to validate.
    :type user: str
    :param token: The token to use.
    :type token: int
    :param secret: The secret to use.
    :type secret: str
    :param diff: Variability in the token range.
    :type diff: 2
    :returns: True, False
    """

    if len(token) > 6:
        password = token[:-6]
        token = token[-6:]
    else:
        return False
    try:
        token = int(token)
    except:
        return False
    if secret:
        try:
            # an exception could occur if there is bad data supplied in the
            # secret, username or password
            # if this happens we fail authentication
            secret = decrypt_secret(secret, password, user)
        except:
            return False
        now = time.time() // 30
        for i in range(diff * -1, diff + 1):
            #print "valid - %s - %s (%s)" % (get_hotp_token(secret, int(now + i)), token, now + i)
            if get_hotp_token(secret, int(now + i)) == token:
                return True
    return False
