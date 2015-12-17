from __future__ import print_function
from six import string_types

import json
import os
import logging

from collections import defaultdict
from pyld import jsonld
from flask import Response as FlaskResponse


class Response(object):

    @property
    def context(self):
        if not hasattr(self, '_context'):
            self._context = None
        return self._context

    @staticmethod
    def get_context(context):
        if isinstance(context, list):
            contexts = []
            for c in context:
                contexts.append(Response.get_context(c))
            return contexts
        elif isinstance(context, dict):
            return context
        elif isinstance(context, string_types):
            try:
                with open(context) as f:
                    return json.loads(f.read())
            except IOError:
                return context
        else:
            raise AttributeError('Please, provide a valid context')                

    def jsonld(self, frame=None, options=None,
               context=None, removeContext=None):
        if removeContext is None:
            removeContext = Response._context  # Loop?
        if frame is None:
            frame = self._frame
        if context is None:
            context = self.context
        else:
            context = self.get_context(context)
        # For some reason, this causes errors with pyld
        # if options is None:
            # options = {"expandContext": context.copy() }
        js = self
        if frame:
            logging.debug("Framing: %s", json.dumps(self, indent=4))
            logging.debug("Framing with %s", json.dumps(frame, indent=4))
            js = jsonld.frame(js, frame, options)
            logging.debug("Result: %s", json.dumps(js, indent=4))
            logging.debug("Compacting with %s", json.dumps(context, indent=4))
            js = jsonld.compact(js, context, options)
            logging.debug("Result: %s", json.dumps(js, indent=4))
        if removeContext == context:
            del js["@context"]
        return js

    def to_JSON(self, removeContext=None):
        return json.dumps(self.jsonld(removeContext=removeContext),
                          default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def flask(self,
              in_headers=False,
              url="http://demos.gsi.dit.upm.es/senpy/senpy.jsonld"):
        """
        Return the values and error to be used in flask
        """
        js = self.jsonld()
        headers = None
        if in_headers:
            ctx = js["@context"]
            headers = {
                "Link": ('<%s>;'
                         'rel="http://www.w3.org/ns/json-ld#context";'
                         ' type="application/ld+json"' % url)
            }
            del js["@context"]
        return FlaskResponse(json.dumps(js, indent=4),
                             status=self.get("status", 200),
                             headers=headers,
                             mimetype="application/json")
    
class Entry(JSONLD):
    pass


class Sentiment(JSONLD):
    pass


class EmotionSet(JSONLD):
    pass


class Emotion(JSONLD):
    pass


class Suggestion(JSONLD):
    pass

class Error(BaseException, JSONLD):
    # A better pattern would be this:
    # htp://flask.pocoo.org/docs/0.10/patterns/apierrors/
    _frame = {}
    _context = {}

    def __init__(self, *args, **kwargs):
        self.message = kwargs.get('message', None)
        super(Error, self).__init__(*args)
