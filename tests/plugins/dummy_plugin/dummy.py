from senpy.plugins import SentimentPlugin


class DummyPlugin(SentimentPlugin):
    def analyse_entry(self, entry, params):
        entry['nif:iString'] = entry['nif:isString'][::-1]
        entry.reversed = entry.get('reversed', 0) + 1
        yield entry

    def test(self):
        pass
