from senpy.plugins import SentimentPlugin


class DummyPlugin(SentimentPlugin):

    description = 'This is a dummy self-contained plugin'
    author = '@balkian'
    version = '0.1'

    def analyse_entry(self, entry, params):
        entry['nif:isString'] = entry['nif:isString'][::-1]
        entry.reversed = entry.get('reversed', 0) + 1
        yield entry

    test_cases = [{
        "entry": {
            "nif:isString": "Hello world!"
        },
        "expected": [{
            "nif:isString": "!dlrow olleH"
        }]
    }]


if __name__ == '__main__':
    d = DummyPlugin()
    d.test()
