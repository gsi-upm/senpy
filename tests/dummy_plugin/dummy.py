from senpy.plugins import SentimentPlugin
from senpy.models import Results


class DummyPlugin(SentimentPlugin):
    def analyse(self, *args, **kwargs):
        return Results()
