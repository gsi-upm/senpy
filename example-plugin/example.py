from senpy.plugins import SentimentPlugin
from senpy.models import Response, Entry

import logging

logger = logging.getLogger(__name__)

class ExamplePlugin(SentimentPlugin):

    def analyse(self, *args, **kwargs):
        logger.warn('Analysing with the example.')
        logger.warn('The answer to this response is: %s.' % kwargs['parameter'])
        resp = Response()
        ent = Entry(kwargs['input'])
        ent['example:reversed'] = kwargs['input'][::-1]
        ent['example:the_answer'] = kwargs['parameter']
        resp.entries.append(ent)

        return resp
