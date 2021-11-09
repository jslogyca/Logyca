# uncompyle6 version 3.5.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /opt/punto/addons-extra/l10n_co_facturae/WSSEDian2/SingExceptions.py
# Compiled at: 2019-09-09 17:54:31


class NodeNotFound(Exception):

    def __init__(self, msg):
        super(NodeNotFound, self).__init__(msg)