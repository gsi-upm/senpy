from senpy.plugins import SentimentPlugin
from senpy.models import Response

class DummyPlugin(SentimentPlugin):
    pass

    def analyse(self, *args, **kwargs):
        return Response()