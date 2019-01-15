# coding=utf-8

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers


from burials.models import Cemetery, Place, Area, BurialFiles

 

class CemeterySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Cemetery
        fields = ('id', 'name', 'time_begin', 'time_end', ) #'ugh'



import copy
import json
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.http.multipartparser import parse_header
from django.template import RequestContext, loader, Template
from django.test.client import encode_multipart
from django.utils.xmlutils import SimplerXMLGenerator
from rest_framework.compat import StringIO
from rest_framework.compat import six
from django.utils.encoding import smart_text
from rest_framework.compat import yaml
from rest_framework.settings import api_settings
from rest_framework.request import clone_request
from rest_framework.utils import encoders
from rest_framework.utils.breadcrumbs import get_breadcrumbs
from rest_framework import exceptions, parsers, status, VERSION


from rest_framework import renderers
class TranslatedJsonRenderer(renderers.BaseRenderer):
    """
    Renderer which serializes to JSON.
    Applies JSON's backslash-u character escaping for non-ascii characters.
    """

    media_type = 'application/json'
    format = 'tjson'
    encoder_class = encoders.JSONEncoder
    ensure_ascii = True
    charset = None
    # JSON is a binary encoding, that can be encoded as utf-8, utf-16 or utf-32.
    # See: http://www.ietf.org/rfc/rfc4627.txt
    # Also: http://lucumr.pocoo.org/2013/7/19/application-mimetypes-and-encodings/

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON.
        """
        if data is None:
            return bytes()

        # If 'indent' is provided in the context, then pretty print the result.
        # E.g. If we're being called by the BrowsableAPIRenderer.
        renderer_context = renderer_context or {}
        indent = renderer_context.get('indent', None)

        if accepted_media_type:
            # If the media type looks like 'application/json; indent=4',
            # then pretty print the result.
            base_media_type, params = parse_header(accepted_media_type.encode('ascii'))
            indent = params.get('indent', indent)
            try:
                indent = max(min(int(indent), 8), 0)
            except (ValueError, TypeError):
                indent = None
        
        print 'TranslatedJsonRenderer', data
        if data["detail"] == "Not found":
            data["detail"] = u"Не найдено"
        ret = json.dumps(data, cls=self.encoder_class,
            indent=indent, ensure_ascii=self.ensure_ascii)

        # On python 2.x json.dumps() returns bytestrings if ensure_ascii=True,
        # but if ensure_ascii=False, the return type is underspecified,
        # and may (or may not) be unicode.
        # On python 3.x json.dumps() returns unicode strings.
        if isinstance(ret, six.text_type):
            return bytes(ret.encode('utf-8'))
        return ret
