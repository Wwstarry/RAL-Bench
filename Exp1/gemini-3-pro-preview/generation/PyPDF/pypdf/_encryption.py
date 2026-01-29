import hashlib
import time

# Padding for password
_pad = b"\x28\xBF\x4E\x5E\x4E\x75\x8A\x41\x64\x00\x4E\x56\xFF\xFA\x01\x08\x2E\x2E\x00\xB6\xD0\x68\x3E\x80\x2F\x0C\xA9\xFE\x64\x53\x69\x7A"

def rc4(key, data):
    x = 0
    y = 0
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) % 256
        s[i], s[j] = s[j], s[i]
    
    res = bytearray(len(data))
    i = 0
    j = 0
    for k in range(len(data)):
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        res[k] = data[k] ^ s[(s[i] + s[j]) % 256]
    return bytes(res)

def alg32(password, rev, keylen, owner_entry, p_entry, id_entry, metadata=True):
    # Algorithm 3.2: Compute encryption key
    m = hashlib.md5()
    # 1. Pad password
    pwd = (password[:32] + _pad)[:32]
    m.update(pwd)
    # 2. Pass O value
    m.update(owner_entry)
    # 3. Pass P value
    m.update(p_entry)
    # 4. Pass ID
    m.update(id_entry)
    # 5. (Revision 4 only) - skipped for basic support
    
    digest = m.digest()
    
    # 6. Revision 3 or greater - loop
    if rev >= 3:
        for i in range(50):
            digest = hashlib.md5(digest[:keylen]).digest()
    
    return digest[:keylen]

def generate_owner_password(owner_pwd, user_pwd):
    # Algorithm 3.3
    if not owner_pwd:
        owner_pwd = user_pwd
    m = hashlib.md5()
    pwd = (owner_pwd[:32] + _pad)[:32]
    m.update(pwd)
    digest = m.digest()
    if True: # Revision 2
        return rc4(digest[:5], user_pwd)
    # Revision 3 logic omitted for brevity