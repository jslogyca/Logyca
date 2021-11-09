# uncompyle6 version 3.5.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /opt/punto/addons-extra/l10n_co_facturae/WSSEDian2/Signing.py
# Compiled at: 2019-09-29 16:12:30
import OpenSSL.crypto as crypto, base64

class Signing(object):

    def __init__(self, pkcs, password, read_file=False):
        if read_file:
            self._pkcs = crypto.load_pkcs12(open(pkcs, 'rb').read(), password)
        else:
            self._pkcs = crypto.load_pkcs12(base64.b64decode(pkcs), password)
        self._cert = self._pkcs.get_certificate()
        self._key = self._pkcs.get_privatekey()

    def sign_text(self, data, digest='sha256'):
        return crypto.sign(self._key, data, digest=digest)

    def get_cert_subject(self):
        return self._cert.get_subject()

    def get_cert_binary(self):
        return crypto.dump_certificate(crypto.FILETYPE_ASN1, self._cert)