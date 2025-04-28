# -*- coding: utf-8 -*-


class NodeNotFound(Exception):

    def __init__(self, msg):
        super(NodeNotFound, self).__init__(msg)