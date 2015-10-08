from senpy.plugins import SentimentPlugin
from senpy.models import Response, Entry

import logging

logger = logging.getLogger(__name__)

class ExamplePlugin(SentimentPlugin):

    def __init__(self, *args, **kwargs):
        super(ExamplePlugin, self).__init__(*args, **kwargs)
        logger.warn('%s: the answer to life, the universe and everything'
              % self._info.get('custom_attribute'))

    def analyse(self, *args, **kwargs):
        logger.warn('Analysing with the example.')
        logger.warn('The answer to this response is: %s.' % kwargs['parameter'])
        resp = Response()
        ent = Entry(kwargs['input'])
        ent['example:reversed'] = kwargs['input'][::-1]
        ent['example:the_answer'] = kwargs['parameter']
        resp.entries.append(ent)

        return resp
