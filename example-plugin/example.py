from senpy.plugins import SentimentPlugin
from senpy.models import Response

import logging

logger = logging.getLogger(__name__)

class ExamplePlugin(SentimentPlugin):

    def __init__(self, *args, **kwargs):
        super(ExamplePlugin, self).__init__(*args, **kwargs)
        logger.warn('%s: the answer to life, the universe and everything'
              % self._info.get('custom_attribute'))

    def analyse(self, *args, **kwargs):
        logger.warn('Analysing with the example')
        return Response()
