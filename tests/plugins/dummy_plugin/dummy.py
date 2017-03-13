from senpy.plugins import SentimentPlugin


class DummyPlugin(SentimentPlugin):
    def analyse_entry(self, entry, params):
        entry.text = entry.text[::-1]
        entry.reversed = entry.get('reversed', 0) + 1
        yield entry
