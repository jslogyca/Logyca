# -*- coding: utf-8 -*-

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