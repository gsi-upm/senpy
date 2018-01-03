import noop
from senpy.plugins import SentimentPlugin


class NoOp(SentimentPlugin):
    '''This plugin does nothing. Literally nothing.'''

    version = 0

    def analyse_entry(self, entry, *args, **kwargs):
        yield entry

    def test(self):
        print(dir(noop))
        super(NoOp, self).test()

    test_cases = [{
        'entry': {
            'nif:isString': 'hello'
        },
        'expected': {
            'nif:isString': 'hello'
        }
    }]
