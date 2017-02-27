from senpy.plugins import SentimentPlugin


class DummyPlugin(SentimentPlugin):
    def analyse_entry(self, entry, params):
        entry.text = entry.text[::-1]
        yield entry
