# -*- coding: utf-8 -*-
###############################################################################
#
#   website_live_helpdesk for Odoo
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from collections import OrderedDict, defaultdict
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from functools import partial
from operator import attrgetter
from lxml.html import clean
from lxml import etree
from odoo.loglevels import ustr
from odoo.tools import misc
from odoo.tools import mail as BaseMail
from operator import attrgetter
import itertools
import logging
import base64
import logging
import re
import json
_logger = logging.getLogger(__name__)
from odoo import fields
from odoo import tools

def monkey_patch(cls):
    """ Return a method decorator to monkey-patch the given class. """
    def decorate(func):
        name = func.__name__
        func.super = getattr(cls, name, None)
        setattr(cls, name, func)
        return func
    return decorate

def html_sanitize(src, silent=True, sanitize_tags=True, sanitize_attributes=False, sanitize_style=False, strip_style=False, strip_classes=False):
    if not src:
        return src
    src = src.replace('<p>Website Live ChatBot MCQ Questions</p>','')
    src = ustr(src, errors='replace')
    # html: remove encoding attribute inside tags
    doctype = re.compile(r'(<[^>]*\s)(encoding=(["\'][^"\']*?["\']|[^\s\n\r>]+)(\s[^>]*|/)?>)', re.IGNORECASE | re.DOTALL)
    src = doctype.sub(u"", src)

    logger = logging.getLogger(__name__ + '.html_sanitize')
    # html encode mako tags <% ... %> to decode them later and keep them alive, otherwise they are stripped by the cleaner
    src = src.replace(u'<%', misc.html_escape(u'<%'))
    src = src.replace(u'%>', misc.html_escape(u'%>'))
    kwargs = {
        'page_structure': True,
        'style': strip_style,              # True = remove style tags/attrs
        'sanitize_style': sanitize_style,  # True = sanitize styling
        'forms': False,                     # True = remove form tags
        'remove_unknown_tags': False,
        'comments': False,
        'processing_instructions': False
    }
    if sanitize_tags:
        kwargs['allow_tags'] = tools.allowed_tags
        if etree.LXML_VERSION >= (2, 3, 1):
            # kill_tags attribute has been added in version 2.3.1
            kwargs.update({
                'kill_tags': tools.tags_to_kill,
                'remove_tags': tools.tags_to_remove,
            })
        else:
            kwargs['remove_tags'] = tools.tags_to_kill + tools.tags_to_remove

    if sanitize_attributes and etree.LXML_VERSION >= (3, 1, 0):  # lxml < 3.1.0 does not allow to specify safe_attrs. We keep all attributes in order to keep "style"
        if strip_classes:
            current_safe_attrs = tools.safe_attrs - frozenset(['class'])
        else:
            current_safe_attrs = tools.safe_attrs
        kwargs.update({
            'safe_attrs_only': True,
            'safe_attrs': current_safe_attrs,
        })
    else:
        kwargs.update({
            'safe_attrs_only': False,  # keep oe-data attributes + style
            'strip_classes': strip_classes,  # remove classes, even when keeping other attributes
        })

    try:
        # some corner cases make the parser crash (such as <SCRIPT/XSS SRC=\"http://ha.ckers.org/xss.js\"></SCRIPT> in test_mail)
        cleaner = BaseMail._Cleaner(**kwargs)
        cleaned = cleaner.clean_html(src)
        assert isinstance(cleaned, str)
        # MAKO compatibility: $, { and } inside quotes are escaped, preventing correct mako execution
        cleaned = cleaned.replace(u'%24', u'$')
        cleaned = cleaned.replace(u'%7B', u'{')
        cleaned = cleaned.replace(u'%7D', u'}')
        cleaned = cleaned.replace(u'%20', u' ')
        cleaned = cleaned.replace(u'%5B', u'[')
        cleaned = cleaned.replace(u'%5D', u']')
        cleaned = cleaned.replace(u'%7C', u'|')
        cleaned = cleaned.replace(u'&lt;%', u'<%')
        cleaned = cleaned.replace(u'%&gt;', u'%>')
        # html considerations so real html content match database value
        cleaned.replace(u'\xa0', u'&nbsp;')
    except etree.ParserError as e:
        if 'empty' in str(e):
            return u""
        if not silent:
            raise
        logger.warning(u'ParserError obtained when sanitizing %r', src, exc_info=True)
        cleaned = u'<p>ParserError when sanitizing</p>'
    except Exception:
        if not silent:
            raise
        logger.warning(u'unknown error obtained when sanitizing %r', src, exc_info=True)
        cleaned = u'<p>Unknown error when sanitizing</p>'

    # this is ugly, but lxml/etree tostring want to put everything in a 'div' that breaks the editor -> remove that
    if cleaned.startswith(u'<div>') and cleaned.endswith(u'</div>'):
        cleaned = cleaned[5:-6]
    return cleaned


@monkey_patch(fields.Html)
def convert_to_column(self, value, record, values=None, validate=True):
    if value is None or value is False:
        return None
    if self.sanitize:
        if value.find('<p>Website Live ChatBot MCQ Questions</p>') > -1:
            return html_sanitize(
                value, silent=True,
                sanitize_tags=self.sanitize_tags,
                sanitize_attributes=self.sanitize_attributes,
                sanitize_style=self.sanitize_style,
                strip_style=self.strip_style,
                strip_classes=self.strip_classes)
        else:
            return tools.html_sanitize(
                value, silent=True,
                sanitize_tags=self.sanitize_tags,
                sanitize_attributes=self.sanitize_attributes,
                sanitize_style=self.sanitize_style,
                strip_style=self.strip_style,
                strip_classes=self.strip_classes)
    return value

@monkey_patch(fields.Html)
def convert_to_cache(self, value, record, validate=True):
    if value is None or value is False:
        return None
    if validate and self.sanitize:
        if str(value).find('<p>Website Live ChatBot MCQ Questions</p>') > -1:
            return html_sanitize(
                value, silent=True,
                sanitize_tags=self.sanitize_tags,
                sanitize_attributes=self.sanitize_attributes,
                sanitize_style=self.sanitize_style,
                strip_style=self.strip_style,
                strip_classes=self.strip_classes)
        else:
            return tools.html_sanitize(
                value, silent=True,
                sanitize_tags=self.sanitize_tags,
                sanitize_attributes=self.sanitize_attributes,
                sanitize_style=self.sanitize_style,
                strip_style=self.strip_style,
                strip_classes=self.strip_classes)
    return value

